"""Durable fictional order delivery. No external credentials or company connector."""
import hashlib,json,re,sqlite3,time
from contextlib import contextmanager
from decimal import Decimal,InvalidOperation
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

@contextmanager
def connection(path):
    database=sqlite3.connect(path,timeout=10);database.row_factory=sqlite3.Row
    database.execute('PRAGMA foreign_keys=ON');database.execute('PRAGMA busy_timeout=10000')
    try:yield database
    finally:database.close()

def init(path):
    with connection(path) as database:
        database.executescript('''PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,hash TEXT NOT NULL,source TEXT NOT NULL,transformed TEXT,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,cycle_attempts INTEGER NOT NULL DEFAULT 0,replays INTEGER NOT NULL DEFAULT 0,next_at REAL NOT NULL,lease_until REAL,created_at REAL NOT NULL,updated_at REAL NOT NULL,error TEXT);
          CREATE INDEX IF NOT EXISTS ready ON jobs(state,next_at);
          CREATE TABLE IF NOT EXISTS timeline(n INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT REFERENCES jobs(id),at REAL,kind TEXT,detail TEXT);
          CREATE TABLE IF NOT EXISTS crm_records(external_key TEXT PRIMARY KEY,order_id TEXT UNIQUE,payload TEXT,hash TEXT);
          CREATE TABLE IF NOT EXISTS crm_attempts(external_key TEXT PRIMARY KEY,calls INTEGER NOT NULL);''')

def envelope(value):
    keys={'eventId','orderId','customer','email','total','currency','mode'}
    if not isinstance(value,dict) or set(value)!=keys:raise ValueError('Požadováno právě eventId, orderId, customer, email, total, currency, mode.')
    if any(not isinstance(value[key],str) or len(value[key])>200 for key in keys):raise ValueError('Pole musí být text do 200 znaků.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value['eventId']) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value['orderId']):raise ValueError('ID musí mít 1–80 písmen, číslic, podtržítek nebo pomlček.')
    if value['mode'] not in ['normal','transient','reject','after_commit','rate_limit','outage']:raise ValueError('Neznámý režim fiktivního CRM.')
    return dict(value)

def transform(source):
    source=envelope(source);customer=' '.join(source['customer'].split());email=source['email'].strip().lower()
    if not 1<=len(customer)<=100 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ValueError('Jméno nebo e-mail neprošel validací.')
    if source['currency']!='CZK':raise ValueError('Ukázka přijímá pouze CZK.')
    if not re.fullmatch(r'\d{1,8}(?:[.,]\d{1,2})?',source['total']):raise ValueError('Částka musí být nezáporný běžný desetinný text do 8 číslic.')
    amount=int(Decimal(source['total'].replace(',','.'))*100)
    if amount<=0:raise ValueError('Částka musí být kladná.')
    return {'orderId':source['orderId'],'customer':customer,'email':email,'totalHalers':amount,'currency':'CZK'}

def audit(database,key,kind,detail,now):database.execute('INSERT INTO timeline(job_id,at,kind,detail) VALUES(?,?,?,?)',(key,now,kind,detail))

class Queue:
    def __init__(self,path,target_url,clock=time.time,transport=urlopen):
        self.path=path;self.target_url=target_url;self.clock=clock;self.transport=transport;init(path)
    def preview(self,source):
        source=envelope(source)
        try:return {'valid':True,'transformed':transform(source),'writes':False}
        except ValueError as error:return {'valid':False,'error':str(error),'writes':False}
    def enqueue(self,source):
        source=envelope(source);key=source['eventId'];digest=fingerprint(source);now=self.clock()
        with connection(self.path) as database,database:
            database.execute('BEGIN IMMEDIATE');old=database.execute('SELECT * FROM jobs WHERE id=?',(key,)).fetchone()
            if old:
                if old['hash']!=digest:raise ValueError('Konflikt: stejné ID události má jiný obsah.')
                return {'id':key,'state':old['state'],'duplicate':True}
            if database.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]>=1000:raise ValueError('Limit ukázky je 1 000 událostí.')
            try:payload=transform(source);state='pending';error=None
            except ValueError as problem:payload=None;state='dead';error=str(problem)
            database.execute('INSERT INTO jobs(id,hash,source,transformed,state,next_at,created_at,updated_at,error) VALUES(?,?,?,?,?,?,?,?,?)',(key,digest,canonical(source),canonical(payload) if payload else None,state,now,now,now,error))
            audit(database,key,'received','Přijata fiktivní objednávková událost.',now);audit(database,key,'validated' if payload else 'invalid','Normalizace dokončena.' if payload else error,now)
        return {'id':key,'state':state,'duplicate':False}
    def claim(self):
        now=self.clock()
        with connection(self.path) as database,database:
            database.execute('BEGIN IMMEDIATE')
            for old in database.execute("SELECT * FROM jobs WHERE state='processing' AND lease_until<=?",(now,)).fetchall():
                exhausted=old['cycle_attempts']>=3;database.execute('UPDATE jobs SET state=?,next_at=?,lease_until=NULL,updated_at=?,error=? WHERE id=?',('dead' if exhausted else 'retry',now,now,'Obnovení po přerušení procesu.',old['id']));audit(database,old['id'],'recovered','Vypršel nárok předchozího workeru; identita zůstává stejná.',now)
            job=database.execute("SELECT * FROM jobs WHERE state IN ('pending','retry') AND next_at<=? ORDER BY next_at,id LIMIT 1",(now,)).fetchone()
            if not job:return None
            database.execute("UPDATE jobs SET state='processing',attempts=attempts+1,cycle_attempts=cycle_attempts+1,lease_until=?,updated_at=? WHERE id=?",(now+10,now,job['id']))
            audit(database,job['id'],'attempt','HTTP pokus '+str(job['attempts']+1),now)
            return dict(database.execute('SELECT * FROM jobs WHERE id=?',(job['id'],)).fetchone())
    def process_next(self):
        job=self.claim()
        if not job:return False
        retryable=False;success=False;delay=2**job['cycle_attempts'];detail='Síťová chyba nebo nedostupný cíl.'
        try:
            request=Request(self.target_url,data=job['transformed'].encode(),headers={'Content-Type':'application/json','Idempotency-Key':job['id'],'X-Demo-Mode':json.loads(job['source'])['mode']},method='POST')
            with self.transport(request,timeout=2) as response:
                result=json.loads(response.read(4097));success=response.status in [200,201] and result.get('externalKey')==job['id'];detail='CRM potvrdilo záznam.' if success else 'Cíl vrátil neplatné potvrzení.'
        except HTTPError as error:
            retryable=error.code==429 or 500<=error.code<=599;detail='HTTP '+str(error.code)
            if error.code==429:
                try:delay=min(60,max(2,int(error.headers.get('Retry-After','2'))))
                except ValueError:delay=2
            error.close()
        except (URLError,TimeoutError,OSError,ValueError):retryable=True
        now=self.clock();state='succeeded' if success else 'retry' if retryable and job['cycle_attempts']<3 else 'dead'
        with connection(self.path) as database,database:
            # An expired/reclaimed attempt cannot overwrite a newer lease's result.
            current=database.execute('SELECT * FROM jobs WHERE id=?',(job['id'],)).fetchone()
            if current['state']=='processing' and current['attempts']==job['attempts']:
                database.execute('UPDATE jobs SET state=?,next_at=?,lease_until=NULL,updated_at=?,error=? WHERE id=?',(state,now+delay if state=='retry' else now,now,None if success else detail,job['id']))
                audit(database,job['id'],state,detail+(' · další pokus za '+str(delay)+' s' if state=='retry' else ''),now)
        return True
    def replay(self,key):
        now=self.clock()
        with connection(self.path) as database,database:
            database.execute('BEGIN IMMEDIATE');job=database.execute('SELECT * FROM jobs WHERE id=?',(key,)).fetchone()
            if not job or job['state']!='dead' or not job['transformed'] or job['replays']>=2:raise ValueError('Replay vyžaduje chybný běh s platným vstupem; nejvýše dva ruční cykly.')
            database.execute("UPDATE jobs SET state='pending',cycle_attempts=0,replays=replays+1,next_at=?,updated_at=?,error=NULL WHERE id=?",(now,now,key));audit(database,key,'replay','Ruční opakování beze změny obsahu a idempotency klíče.',now)
    def jobs(self):
        with connection(self.path) as database:return [dict(row) for row in database.execute('SELECT id,state,attempts,cycle_attempts,replays,next_at,created_at,updated_at,error FROM jobs ORDER BY created_at DESC,id LIMIT 1000')]
    def detail(self,key):
        with connection(self.path) as database:
            row=database.execute('SELECT * FROM jobs WHERE id=?',(key,)).fetchone()
            if not row:return None
            result=dict(row);result['source']=json.loads(result['source']);result['transformed']=json.loads(result['transformed']) if result['transformed'] else None;result['timeline']=[dict(row) for row in database.execute('SELECT at,kind,detail FROM timeline WHERE job_id=? ORDER BY n',(key,))];return result

def crm_receive(path,key,payload,mode):
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',key):raise ValueError('Neplatný idempotency klíč.')
    if not isinstance(payload,dict) or set(payload)!={'orderId','customer','email','totalHalers','currency'} or not isinstance(payload['totalHalers'],int) or isinstance(payload['totalHalers'],bool) or not 0<payload['totalHalers']<=9999999999:raise ValueError('Neplatný cílový záznam.')
    # Reuse the independent business validation on the transformed contract as well.
    transform({'eventId':key,'orderId':payload['orderId'],'customer':payload['customer'],'email':payload['email'],'total':str(Decimal(payload['totalHalers'])/100),'currency':payload['currency'],'mode':'normal'})
    digest=fingerprint(payload)
    with connection(path) as database,database:
        database.execute('BEGIN IMMEDIATE');old=database.execute('SELECT * FROM crm_records WHERE external_key=?',(key,)).fetchone()
        if old:return (200,{'externalKey':key,'duplicate':True}) if old['hash']==digest else (409,{'error':'Konflikt idempotency klíče.'})
        existing=database.execute('SELECT 1 FROM crm_records WHERE order_id=?',(payload['orderId'],)).fetchone()
        if existing:return 409,{'error':'Objednávka již má jinou událost.'}
        database.execute('INSERT INTO crm_attempts VALUES(?,1) ON CONFLICT(external_key) DO UPDATE SET calls=calls+1',(key,));calls=database.execute('SELECT calls FROM crm_attempts WHERE external_key=?',(key,)).fetchone()[0]
        if mode=='reject':return 422,{'error':'Simulované trvalé odmítnutí CRM.'}
        if mode=='outage' or mode in ['transient','rate_limit'] and calls==1:return (429 if mode=='rate_limit' else 503),{'error':'Simulovaná dočasná nedostupnost.'}
        database.execute('INSERT INTO crm_records VALUES(?,?,?,?)',(key,payload['orderId'],canonical(payload),digest))
        if mode=='after_commit' and calls==1:return 503,{'error':'Zápis proběhl, potvrzení se nedoručilo.'}
        return 201,{'externalKey':key,'duplicate':False}
