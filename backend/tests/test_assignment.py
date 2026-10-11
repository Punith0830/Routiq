from fastapi.testclient import TestClient
from app.assignment import create_assignment_app


def test_assignment_faq_and_cors_boundary():
    client = TestClient(create_assignment_app(['https://routiq-pink.vercel.app'], ['testserver']))
    origin = {'Origin': 'https://routiq-pink.vercel.app'}
    assert client.get('/health').json()['live_ai'] is False
    preflight = client.options('/api/coach/chat', headers={**origin, 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
    assert preflight.status_code == 200
    assert preflight.headers['access-control-allow-origin'] == origin['Origin']
    reply = client.post('/api/coach/chat', headers=origin, json={'message': 'Can you suggest a small starting habit?'})
    assert reply.status_code == 200
    assert reply.json()['source'] == 'prepared_faq'
    blocked = client.post('/api/coach/chat', headers={'Origin': 'https://unrelated.example'}, json={'message': 'Hello'})
    assert blocked.status_code == 403
    assert 'access-control-allow-origin' not in blocked.headers
    assert client.get('/api/habits').status_code == 404


def test_assignment_no_data_claim_or_validation_echo():
    client = TestClient(create_assignment_app([], ['testserver']))
    today = client.post('/api/coach/chat', json={'message': 'How am I doing today?'}).json()
    assert today['source'] == 'scope_limit'
    invalid = client.post('/api/coach/chat', json={'message': 'Hello', 'secret': 'private-sentinel'})
    assert invalid.status_code == 422
    assert 'private-sentinel' not in invalid.text
    assert client.get('/health', headers={'Host': 'unrelated.example'}).status_code == 400
