import json
from datetime import datetime, timezone
import pytest
import requests
from app.providers.http import JsonClient
from app.core.exceptions import *

URL='https://api.open-meteo.com/v1/forecast'
class Response:
    def __init__(self,status=200,data=None,raw=None,headers=None):
        self.status_code=status
        self.raw=raw if raw is not None else json.dumps(data if data is not None else {'ok':True}).encode()
        self.headers=headers or {}
        self.closed=False
    def __enter__(self): return self
    def __exit__(self,*args): self.closed=True
    def iter_content(self,size): yield self.raw
class Session:
    def __init__(self,*events): self.events=list(events); self.calls=[]
    def get(self,*args,**kwargs):
        self.calls.append((args,kwargs))
        event=self.events.pop(0)
        if isinstance(event,Exception): raise event
        return event

def test_success():
    response=Response()
    session=Session(response)
    assert JsonClient(session).get(URL,{'name':'São Paulo'})=={'ok':True}
    assert response.closed
    kw=session.calls[0][1]
    assert kw['timeout']==(3.05,10) and kw['allow_redirects'] is False and kw['stream'] is True

@pytest.mark.parametrize('status',[400,401,403,404,301])
def test_no_retry(status):
    session=Session(Response(status))
    with pytest.raises(WeatherProviderError): JsonClient(session).get(URL,{})
    assert len(session.calls)==1

@pytest.mark.parametrize('event',[Response(500),Response(502),Response(503),Response(504),requests.Timeout('secret'),requests.ConnectionError('secret')])
def test_retry_success(event):
    session=Session(event,Response())
    pauses=[]
    assert JsonClient(session,sleep=pauses.append).get(URL,{})=={'ok':True}
    assert len(session.calls)==2 and pauses==[0.25]

@pytest.mark.parametrize('event,kind',[(requests.Timeout('secret'),WeatherTimeoutError),(requests.ConnectionError('secret'),WeatherNetworkError),(Response(503),WeatherProviderError)])
def test_retry_exhaustion(event,kind):
    session=Session(event,event)
    with pytest.raises(kind) as e: JsonClient(session,sleep=lambda _:None).get(URL,{})
    assert len(session.calls)==2 and 'secret' not in str(e.value)
    if isinstance(event,Exception): assert e.value.__cause__ is event

@pytest.mark.parametrize('header,expected',[('120',120),('-1',0),('Thu, 15 Jan 2026 14:21:00 GMT',60),('garbage',None),(None,None)])
def test_rate_limit(header,expected):
    session=Session(Response(429,headers={'Retry-After':header}))
    with pytest.raises(WeatherRateLimitError) as e:
        JsonClient(session,clock=lambda:datetime(2026,1,15,14,20,tzinfo=timezone.utc)).get(URL,{})
    assert e.value.retry_after_seconds==expected and len(session.calls)==1

@pytest.mark.parametrize('raw,kind',[(b'not json',WeatherDataError),(b'\xff',WeatherDataError),(b'[]',WeatherDataError),(b'{"error":true,"reason":"secret"}',WeatherProviderError),(b'x'*2_000_001,WeatherDataError)])
def test_bad_body(raw,kind):
    session=Session(Response(raw=raw))
    with pytest.raises(kind) as e: JsonClient(session).get(URL,{})
    assert 'secret' not in str(e.value) and len(session.calls)==1

def test_cooperative_deadline():
    ticks=iter([0,31])
    with pytest.raises(WeatherTimeoutError): JsonClient(Session(Response()),monotonic=lambda:next(ticks)).get(URL,{})

@pytest.mark.parametrize('url',['http://api.open-meteo.com/v1/forecast','https://evil.example/','https://api.open-meteo.com/other'])
def test_endpoint_allowlist(url):
    session=Session()
    with pytest.raises(WeatherProviderError): JsonClient(session).get(url,{})
    assert not session.calls

def test_503_retry_after_defers():
    session=Session(Response(503,headers={'Retry-After':'90'}))
    with pytest.raises(WeatherRateLimitError) as e: JsonClient(session).get(URL,{})
    assert e.value.retry_after_seconds==90 and len(session.calls)==1
