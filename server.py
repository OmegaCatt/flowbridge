import argparse,json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from engine import Queue,connection,crm_receive,init
ROOT=Path(__file__).resolve().parent
HEADERS={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"}
class Server(ThreadingHTTPServer):
    daemon_threads=True
    def handle_error(self,request,client_address):pass

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,code,payload,mime='application/json; charset=utf-8'):
        body=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False).encode();self.send_response(code)
        for key,value in HEADERS.items():self.send_header(key,mime if key=='Content-Type' else value)
        self.send_header('Content-Length',str(len(body)))
        if code==429:self.send_header('Retry-After','2')
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def allowed(self):return self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port) and self.headers.get('Origin') in [None,'http://127.0.0.1:'+str(self.server.server_port)]
    def body(self):
        if self.headers.get('Content-Type','').split(';')[0].lower()!='application/json':raise ValueError('Požadován JSON.')
        length=int(self.headers.get('Content-Length','0'))
        if not 0<length<=16000:raise ValueError('Limit požadavku je 16 000 bajtů.')
        self.connection.settimeout(3);return json.loads(self.rfile.read(length))
    def do_GET(self):
        if not self.allowed():return self.send(403,{'error':'Nepovolený host nebo původ.'})
        url=urlsplit(self.path)
        if self.server.is_crm:
            if url.path!='/api/records':return self.send(404,{'error':'Nenalezeno.'})
            with connection(self.server.database) as database:rows=[dict(row) for row in database.execute('SELECT external_key,order_id,payload FROM crm_records ORDER BY external_key LIMIT 1000')]
            return self.send(200,{'records':[{**row,'payload':json.loads(row['payload'])} for row in rows]})
        queue=self.server.queue
        if url.path=='/api/jobs':return self.send(200,{'jobs':queue.jobs()})
        if url.path=='/api/job':
            key=parse_qs(url.query).get('id',[''])[0];result=queue.detail(key);return self.send(200 if result else 404,result or {'error':'Běh neexistuje.'})
        if url.path=='/api/summary':
            with connection(self.server.crm_database) as database:count=database.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0]
            return self.send(200,{'jobs':len(queue.jobs()),'crmRecords':count,'fictional':True})
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if url.path not in files:return self.send(404,{'error':'Nenalezeno.'})
        name,mime=files[url.path];return self.send(200,(ROOT/'web'/name).read_bytes(),mime)
    def do_POST(self):
        if not self.allowed():return self.send(403,{'error':'Nepovolený host nebo původ.'})
        try:
            body=self.body();path=urlsplit(self.path).path
            if self.server.is_crm:
                if path!='/api/orders':return self.send(404,{'error':'Nenalezeno.'})
                status,result=crm_receive(self.server.database,self.headers.get('Idempotency-Key'),body,self.headers.get('X-Demo-Mode','normal'));return self.send(status,result)
            if path=='/api/preview':return self.send(200,self.server.queue.preview(body))
            if path=='/api/events':
                try:return self.send(200,self.server.queue.enqueue(body))
                except ValueError as error:return self.send(409 if 'Konflikt' in str(error) else 400,{'error':str(error)})
            if path=='/api/replay':
                if not isinstance(body,dict) or set(body)!={'id'} or not isinstance(body['id'],str):raise ValueError('Neplatný běh.')
                self.server.queue.replay(body['id']);return self.send(200,{'ok':True})
            return self.send(404,{'error':'Nenalezeno.'})
        except (ValueError,TypeError,TimeoutError,RecursionError):return self.send(400,{'error':'Neplatný vstup nebo nepovolený replay. Ověřte JSON a stav běhu.'})

class Application:
    def __init__(self,directory,port=4196,crm_port=4197,worker=True):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);self.stop=threading.Event()
        self.crm=Server(('127.0.0.1',crm_port),Handler);self.crm.is_crm=True;self.crm.database=directory/'crm.sqlite';init(self.crm.database)
        self.app=Server(('127.0.0.1',port),Handler);self.app.is_crm=False;self.app.crm_database=self.crm.database
        self.queue=Queue(directory/'queue.sqlite','http://127.0.0.1:'+str(self.crm.server_port)+'/api/orders');self.app.queue=self.queue
        self.threads=[threading.Thread(target=server.serve_forever,daemon=True) for server in [self.crm,self.app]]
        if worker:self.threads.append(threading.Thread(target=self.run_worker,daemon=True))
    def run_worker(self):
        while not self.stop.is_set():
            try:self.queue.process_next()
            except Exception:pass # Durable lease is recovered; no source data in logs.
            self.stop.wait(.25)
    def start(self):
        for thread in self.threads:thread.start()
        return self
    def close(self):
        self.stop.set()
        if len(self.threads)>2:self.threads[-1].join(timeout=4)
        for server in [self.app,self.crm]:server.shutdown();server.server_close()
        for thread in self.threads[:2]:thread.join(timeout=2)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=4196);parser.add_argument('--crm-port',type=int,default=4197);parser.add_argument('--data',default=str(ROOT/'data'));args=parser.parse_args()
    application=Application(args.data,args.port,args.crm_port).start();print('FlowBridge: http://127.0.0.1:'+str(application.app.server_port),flush=True)
    try:
        while True:time.sleep(1)
    except KeyboardInterrupt:application.close()
