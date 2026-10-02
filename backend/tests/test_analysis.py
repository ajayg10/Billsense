from decimal import Decimal
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.analysis import analyze_files, AnalysisError
from app.main import app

client=TestClient(app)
def run(text, opts=None):
    return analyze_files([(text.encode(),'test.csv')],opts)

def test_sample_reconciles_and_evidence():
    r=client.get('/api/v1/samples/student-project').json()
    assert r['metrics']['net']=='370.50'
    assert r['metrics']['positive']=='385.50'
    assert r['metrics']['negative']=='-15.00'
    assert r['comparison']['previous_total']=='220.70'
    assert r['comparison']['change']=='149.80'
    for f in r['findings']:
        assert sum((Decimal(row['amount_decimal']) for row in r['records'] if row['record_id'] in f['evidence_ids']),Decimal(0))==Decimal(f['amount'])
    assert sum(Decimal(s['cost']) for s in r['services'])==Decimal('370.50')
    assert sum(Decimal(s['cost']) for s in r['regions'])==Decimal('370.50')

def test_credit_total_and_decimal_precision():
    r=run('service,cost,currency\nEC2,0.10,USD\nEC2,0.20,USD\nEC2,-0.05,USD\nTotal,0.25,USD\n')
    assert r['metrics']['net']=='0.25'
    assert r['metrics']['positive']=='0.30'
    assert r['meta']['excluded_records']==[5]
    assert r['daily']==[]

def test_wide_normalizes_and_does_not_count_total_column():
    r=run('Service,2026-08,2026-09,Total\nEC2,10,20,30\nS3,2,3,5\nTotal,12,23,35\n', {'current':{'currency':'USD'}})
    assert r['metrics']['net']=='35'
    assert len(r['records'])==4
    assert r['daily']==[]

def test_cur_missing_optional():
    r=run('lineItem/ProductCode,lineItem/UnblendedCost,lineItem/CurrencyCode\nAmazonEC2,10.25,USD\n')
    assert r['meta']['cost_basis']=='unblended'
    assert r['regions']==[{'name':'Unknown','cost':'10.25'}]

@pytest.mark.parametrize('text,code',[
 ('service,cost,currency\nEC2,10,USD\nS3,2,EUR\n','MIXED_CURRENCY'),
 ('service,cost\nEC2,10\n','MISSING_CURRENCY'),
 ('service,cost,currency\nEC2,NaN,USD\n','INVALID_AMOUNT'),
 ('service,cost,currency\nEC2,,USD\n','INVALID_AMOUNT'),
 ('service,cost,cost\nEC2,1,1\n','DUPLICATE_HEADERS'),
 ('service,cost,currency,date\nEC2,10,USD,01/02/2026\n','INVALID_DATE'),
])
def test_invalid_data_is_not_silently_accepted(text,code):
    with pytest.raises(AnalysisError) as e:run(text)
    assert e.value.code==code

def test_negative_net_shares_are_still_meaningful():
    r=run('service,cost,currency\nEC2,10,USD\nEC2,-20,USD\n')
    assert r['metrics']['net']=='-10'
    assert r['services'][0]['share']=='100'

def test_duplicate_records_retained_with_warning():
    r=run('service,cost,currency\nEC2,1,USD\nEC2,1,USD\n')
    assert r['metrics']['net']=='2'
    assert any('duplicate' in w for w in r['warnings'])

def test_api_upload_and_inspection():
    text=b'service,cost,currency\nLambda,1.25,USD\n'
    assert client.post('/api/v1/inspect', files={'file':('cost.csv',text,'text/csv')}).json()['mapping']['cost']=='cost'
    r=client.post('/api/v1/analyze',files={'current':('cost.csv',text,'text/csv')})
    assert r.status_code==200
    assert r.json()['metrics']['net']=='1.25'
    assert r.headers['cache-control']=='no-store'

def test_ai_unavailable_is_graceful(monkeypatch):
    monkeypatch.setenv('AI_ENABLED','false')
    r=client.post('/api/v1/explain',files={'current':('cost.csv',b'service,cost,currency\nEC2,10,USD\n','text/csv')},data={'consent':'true'})
    assert r.status_code==200
    assert r.json()['mode']=='unavailable'

def test_zero_previous_no_percentage():
    a=b'service,cost,currency\nEC2,1,USD\n'
    b=b'service,cost,currency\nEC2,0,USD\n'
    r=analyze_files([(a,'a.csv'),(b,'b.csv')])
    assert r['comparison']['percentage'] is None

def test_mangum_http_api_multipart():
    import base64
    from app.main import handler
    body=b'--bound\r\nContent-Disposition: form-data; name="current"; filename="bill.csv"\r\nContent-Type: text/csv\r\n\r\nservice,cost,currency\nEC2,1.50,USD\n\r\n--bound--\r\n'
    event={'version':'2.0','routeKey':'POST /api/v1/analyze','rawPath':'/api/v1/analyze','rawQueryString':'','headers':{'content-type':'multipart/form-data; boundary=bound','host':'test.example'},'requestContext':{'http':{'method':'POST','path':'/api/v1/analyze','sourceIp':'127.0.0.1','protocol':'HTTP/1.1'},'stage':'$default'},'body':base64.b64encode(body).decode(),'isBase64Encoded':True}
    result=handler(event,{})
    assert result['statusCode']==200
    import json
    assert json.loads(result['body'])['metrics']['net']=='1.50'

def test_invalid_options_are_rejected():
    r=client.post('/api/v1/analyze',files={'current':('x.csv',b'service,cost,currency\nEC2,1,USD\n')},data={'options':'{"current":{"mapping":123}}'})
    assert r.status_code==422
    assert r.json()['error']['code']=='INVALID_OPTIONS'

def test_oversized_body_rejected_before_parsing():
    r=client.post('/api/v1/analyze',content=b'x'*(1024*1024+65537),headers={'Content-Type':'multipart/form-data; boundary=x'})
    assert r.status_code==413
