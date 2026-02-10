import pytest


def test_shorten_basic(client):
    """Test basic URL shortening"""
    response = client.post('/shorten', json={
        'url': 'https://example.com'
    })

    assert response.status_code == 201
    data = response.get_json()

    assert 'short_url' in data
    assert 'original_url' in data
    assert data['original_url'] == 'https://example.com'
    assert data['custom_used'] is False
    assert data['already_existed'] is False


def test_shorten_without_protocol(client):
    """Test URL without http/https gets prefixed"""
    response = client.post('/shorten', json={
        'url': 'example.com'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['original_url'] == 'https://example.com'


def test_shorten_custom_code(client):
    """Test custom short code"""
    response = client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'mycode'
    })

    assert response.status_code == 201
    data = response.get_json()

    assert 'mycode' in data['short_url']
    assert data['custom_used'] is True


def test_shorten_custom_code_invalid(client):
    """Test invalid custom code (too short)"""
    response = client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'abc'
    })

    assert response.status_code == 400


def test_shorten_custom_code_duplicate(client):
    """Test duplicate custom code returns existing"""
    client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'test123'
    })

    response = client.post('/shorten', json={
        'url': 'https://different.com',
        'custom_code': 'test123'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['already_existed'] is True
    assert data['original_url'] == 'https://example.com'


def test_shorten_same_url_twice(client):
    """Test same URL returns existing short code"""
    response1 = client.post('/shorten', json={
        'url': 'https://example.com/same'
    })
    short_code1 = response1.get_json()['short_url'].split('/')[-1]

    response2 = client.post('/shorten', json={
        'url': 'https://example.com/same'
    })

    assert response2.status_code == 200
    data = response2.get_json()
    assert data['already_existed'] is True
    short_code2 = data['short_url'].split('/')[-1]

    assert short_code1 == short_code2