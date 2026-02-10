import pytest
import fakeredis
from app import app as flask_app


@pytest.fixture
def app():
    """Flask app fixture with test config"""
    flask_app.config.update({
        "TESTING": True,
        "RATELIMIT_ENABLED": False
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner fixture"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    import shortener
    import app as app_module

    monkeypatch.setattr(shortener, "r", fake_redis)
    monkeypatch.setattr(app_module, "r", fake_redis)

    try:
        from app import limiter
        limiter.enabled = False
    except:
        pass

    yield fake_redis
    fake_redis.flushall()