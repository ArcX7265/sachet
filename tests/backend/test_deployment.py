import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from app import main
from app.accounts import provision, disable


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('SACHET_DB_PATH', str(tmp_path/'deployment.sqlite3'))
    monkeypatch.setenv('DEMO_MODE', 'false')
    with TestClient(main.app) as client:
        yield client


def login(client, username='pilot', password='a-long-pilot-password'):
    return client.post('/v1/auth/login', json={'username':username,'password':password})


def headers(response):
    assert response.status_code == 200, response.text
    return {'Authorization':'Bearer '+response.json()['token']}


def test_account_roles_ownership_and_persistence(client):
    provision('pilot','user','a-long-pilot-password')
    provision('other','user','another-long-password')
    provision('reviewer','analyst','reviewer-long-password')
    h=headers(login(client))
    assert client.post('/v1/sessions',json={'role':'admin'}).status_code==403
    assert client.post('/v1/auth/login',json={'username':'pilot','password':'a-long-pilot-password','role':'admin'}).status_code==422
    assert client.get('/v1/sessions/current',headers=h).json()['role']=='user'
    case=client.post('/v1/cases',headers=h,json={'title':'Hosted case'}).json()
    assert client.get('/v1/analyst/candidates',headers=h).status_code==403
    assert client.get('/v1/cases/'+case['id'],headers=headers(login(client,'other','another-long-password'))).status_code==404
    assert client.post('/v1/cases',headers=headers(login(client,'reviewer','reviewer-long-password')),json={}).status_code==403
    client.delete('/v1/sessions/current',headers=h)
    assert client.get('/v1/cases',headers=h).status_code==401
    assert client.get('/v1/cases',headers=headers(login(client))).json()['cases'][0]['id']==case['id']


def test_failed_login_is_generic_and_rate_limited(client):
    provision('pilot','user','a-long-pilot-password')
    assert login(client,password='incorrect-password').json()==login(client,'unknown','incorrect-password').json()
    for _ in range(9):
        assert login(client,password='incorrect-password').status_code==401
    assert login(client).status_code==429


def test_password_reset_role_change_and_disable_revoke_sessions(client):
    provision('pilot','user','a-long-pilot-password')
    old=headers(login(client))
    provision('pilot','admin','updated-long-password')
    assert client.get('/v1/cases',headers=old).status_code==401
    current=headers(login(client,password='updated-long-password'))
    assert client.get('/v1/sessions/current',headers=current).json()['role']=='admin'
    disable('pilot')
    assert client.get('/v1/sessions/current',headers=current).status_code==401
    assert login(client,password='updated-long-password').status_code==401


def test_cron_auth_and_expired_case_access(client,monkeypatch):
    secret='test-cron-secret-that-is-long-enough'
    monkeypatch.setenv('CRON_SECRET',secret)
    provision('pilot','user','a-long-pilot-password')
    h=headers(login(client))
    case=client.post('/v1/cases',headers=h,json={}).json()
    case['retention_until']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    with main.db(write=True) as c:
        c.execute('UPDATE cases SET data=? WHERE id=?',(json.dumps(case),case['id']))
    assert client.get('/v1/cases/'+case['id'],headers=h).status_code==410
    assert client.get('/internal/cron/expire').status_code==401
    assert client.get('/internal/cron/expire',headers=h).status_code==401
    assert client.get('/internal/cron/expire',headers={'Authorization':'Bearer '+secret}).status_code==200
    assert client.get('/v1/cases/'+case['id'],headers=h).status_code==404


def test_simultaneous_event_updates_keep_both_revisions(client):
    provision('pilot','user','a-long-pilot-password')
    h=headers(login(client))
    case=client.post('/v1/cases',headers=h,json={}).json()
    def add(index):
        return client.post('/v1/cases/'+case['id']+'/events',headers=h,json={'text':f'Your balance is ready. Message {index}', 'idempotency_key':f'parallel-{index}'})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(add,range(2)))
    assert [r.status_code for r in responses]==[200,200]
    current=client.get('/v1/cases/'+case['id'],headers=h).json()
    assert current['revision']==2
    assert sorted(e['revision'] for e in current['events'])==[1,2]


def test_vercel_rejects_demo_and_missing_database(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.delenv('DATABASE_URL',raising=False)
    with pytest.raises(RuntimeError,match='DATABASE_URL'):
        with TestClient(main.app):
            pass
    monkeypatch.setenv('DATABASE_URL','postgresql://unused')
    monkeypatch.setenv('DEMO_MODE','true')
    with pytest.raises(RuntimeError,match='DEMO_MODE'):
        with TestClient(main.app):
            pass


def test_vercel_lifespan_does_not_start_background_loop(client,monkeypatch):
    if not main.postgres_enabled():
        pytest.skip('Serverless lifecycle requires the PostgreSQL verification run')
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.setenv('CRON_SECRET','a'*32)
    async def forbidden():
        pytest.fail('Serverless startup must not start a permanent cleanup loop')
    monkeypatch.setattr(main,'retention_loop',forbidden)
    async def check():
        async with main.lifespan(main.app):
            pass
    asyncio.run(check())
