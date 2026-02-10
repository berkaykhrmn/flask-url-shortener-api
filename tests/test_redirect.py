def test_redirect_success(client):
    """Test successful redirect"""
    response = client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'test456'
    })

    response = client.get('/test456', follow_redirects=False)

    assert response.status_code == 302
    assert response.location == 'https://example.com'


def test_redirect_not_found(client):
    """Test 404 for non-existent short code"""
    response = client.get('/nonexistent')

    assert response.status_code == 404
    data = response.get_json()
    assert 'not found' in data['message'].lower()


def test_redirect_increments_clicks(client, mock_redis):
    """Test that redirect increments click counter"""
    client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'clicktest'
    })

    for _ in range(3):
        client.get('/clicktest')

    clicks = mock_redis.get('clicks:clicktest')
    assert int(clicks) == 3