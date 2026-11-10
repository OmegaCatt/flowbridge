import concurrent.futures,json,tempfile,time,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from engine import transform,connection,crm_receive
from server import Application

def event(key='event-a',mode='normal'):
    return {'eventId':key,'orderId':'order-'+key,'customer':'  Severka   Studio ','email':'  NAKUP@SEVERKA.EXAMPLE ','total':'1234,50','currency':'CZK','mode':mode}

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.application=Application(self.temp.name,0,0,worker=False).start();self.queue=self.application.queue;self.now=1000.;self.queue.clock=lambda:self.now
    def tearDown(self):self.application.close();self.temp.cleanup()
    def test_preview_validates_normalizes_exact_money_and_writes_nothing(self):
        result=self.queue.preview(event());self.assertEqual(result['transformed']['totalHalers'],123450);self.assertEqual(result['transformed']['email'],'nakup@severka.example');self.assertEqual(result['transformed']['customer'],'Severka Studio');self.assertEqual(self.queue.jobs(),[])
        with connection(self.application.crm.database) as database:self.assertEqual(database.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0],0)
        for total in ['1e3','-1','0','1.999','NaN','999999999']:
            self.assertFalse(self.queue.preview({**event(),'total':total})['valid'])
    def test_real_http_success_duplicate_and_conflicting_event(self):
        self.queue.enqueue(event());self.assertTrue(self.queue.process_next());self.assertEqual(self.queue.detail('event-a')['state'],'succeeded');self.assertTrue(self.queue.enqueue(event())['duplicate']);self.assertFalse(self.queue.process_next())
        with self.assertRaisesRegex(ValueError,'Konflikt'):self.queue.enqueue({**event(),'total':'2000'})
        with connection(self.application.crm.database) as database:self.assertEqual(database.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0],1)
    def test_actual_transient_http_retry_has_delay_then_success(self):
        self.queue.enqueue(event(mode='transient'));self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['state'],'retry');self.assertFalse(self.queue.process_next());self.now+=2;self.queue.process_next();detail=self.queue.detail('event-a');self.assertEqual(detail['state'],'succeeded');self.assertEqual(detail['attempts'],2);self.assertIn('retry',[item['kind'] for item in detail['timeline']])
    def test_committed_target_with_failed_ack_is_not_written_twice(self):
        self.queue.enqueue(event(mode='after_commit'));self.queue.process_next()
        with connection(self.application.crm.database) as database:self.assertEqual(database.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0],1)
        self.now+=2;self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['state'],'succeeded')
        with connection(self.application.crm.database) as database:self.assertEqual(database.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0],1)
    def test_429_obeys_retry_after(self):
        self.queue.enqueue(event(mode='rate_limit'));self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['next_at'],1002);self.now+=2;self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['state'],'succeeded')
    def test_truly_invalid_input_goes_to_dead_without_contacting_target(self):
        self.queue.enqueue({**event(),'email':'bad'});self.assertEqual(self.queue.detail('event-a')['state'],'dead');self.assertFalse(self.queue.process_next())
        with self.assertRaises(ValueError):self.queue.replay('event-a')
        with connection(self.application.crm.database) as database:self.assertEqual(database.execute('SELECT COUNT(*) FROM crm_attempts').fetchone()[0],0)
    def test_422_is_not_retried_and_replay_is_bounded_without_rewriting_history(self):
        self.queue.enqueue(event(mode='reject'));self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['state'],'dead')
        for _ in range(2):self.queue.replay('event-a');self.queue.process_next()
        detail=self.queue.detail('event-a');self.assertEqual(detail['attempts'],3);self.assertEqual(detail['replays'],2);self.assertEqual(sum(item['kind']=='replay' for item in detail['timeline']),2)
        with self.assertRaises(ValueError):self.queue.replay('event-a')
    def test_retries_stop_at_three_and_never_spin_forever(self):
        self.queue.enqueue(event(mode='outage'))
        for _ in range(3):self.queue.process_next();self.now+=60
        self.assertEqual(self.queue.detail('event-a')['state'],'dead');self.assertEqual(self.queue.detail('event-a')['attempts'],3);self.assertFalse(self.queue.process_next())
    def test_claim_lease_is_recovered_after_interrupted_worker(self):
        self.queue.enqueue(event());claimed=self.queue.claim();self.assertEqual(claimed['state'],'processing');self.assertIsNone(self.queue.claim());self.now+=11;self.queue.process_next();detail=self.queue.detail('event-a');self.assertEqual(detail['state'],'succeeded');self.assertEqual(detail['attempts'],2);self.assertIn('recovered',[item['kind'] for item in detail['timeline']])
    def test_concurrent_duplicate_enqueue_and_claim_are_atomic(self):
        with concurrent.futures.ThreadPoolExecutor(5) as pool:results=list(pool.map(lambda _:self.queue.enqueue(event()),range(5)))
        self.assertEqual(sum(not result['duplicate'] for result in results),1)
        with concurrent.futures.ThreadPoolExecutor(5) as pool:claims=list(pool.map(lambda _:self.queue.claim(),range(5)))
        self.assertEqual(sum(claim is not None for claim in claims),1)
    def test_persistence_across_service_restart(self):
        self.queue.enqueue(event());self.application.close();self.application=Application(self.temp.name,0,0,worker=False).start();self.queue=self.application.queue;self.assertEqual(len(self.queue.jobs()),1);self.queue.process_next();self.assertEqual(self.queue.detail('event-a')['state'],'succeeded')
    def test_target_rejects_changed_idempotent_payload_and_duplicate_business_key(self):
        payload=transform(event());self.assertEqual(crm_receive(self.application.crm.database,'key',payload,'normal')[0],201);self.assertEqual(crm_receive(self.application.crm.database,'key',payload,'normal')[0],200);self.assertEqual(crm_receive(self.application.crm.database,'key',{**payload,'totalHalers':1},'normal')[0],409);self.assertEqual(crm_receive(self.application.crm.database,'other',payload,'normal')[0],409)
    def test_http_origin_size_paths_and_contract(self):
        base='http://127.0.0.1:'+str(self.application.app.server_port)
        for path,data,headers,expected in [('/api/preview',event(),{'Origin':'https://evil.example'},403),('/api/events',{'url':'http://evil.example'}, {},400),('/api/preview',{'x':'x'*16001},{},400),('/.env.local',None,{},404)]:
            request=Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**headers})
            with self.assertRaises(HTTPError) as result:urlopen(request)
            self.assertEqual(result.exception.code,expected);result.exception.close()
        with urlopen(base) as response:self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
