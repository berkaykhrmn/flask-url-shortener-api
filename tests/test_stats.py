def test_stats_basic(client):
    """Test basic stats endpoint"""
    client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'stats1'
    })

    response = client.get('/stats/stats1')

    assert response.status_code == 200
    data = response.get_json()

    assert data['short_code'] == 'stats1'
    assert data['total_clicks'] == 0
    assert data['unique_ips'] == 0


def test_stats_after_clicks(client):
    """Test stats after some clicks"""
    client.post('/shorten', json={
        'url': 'https://example.com',
        'custom_code': 'stats2'
    })

    client.get('/stats2')
    client.get('/stats2')

    response = client.get('/stats/stats2')
    data = response.get_json()

    assert data['total_clicks'] == 2
    assert data['unique_ips'] == 1