from celery import Celery
from config import Config
from bs4 import BeautifulSoup
import redis, requests, json

celery = Celery('tasks',
                broker=Config.RATELIMIT_STORAGE_URL,
                backend=Config.RATELIMIT_STORAGE_URL)

r = redis.Redis(host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True)

@celery.task
def fetch_url_preview(short_code, long_url):
    try:
        response = requests.get(long_url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "No title"
        description = ""

        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            description = desc_tag.get("content", "")

        preview_data = {
            "title": title[:100],
            "description": description[:200],
        }
        r.setex(f"preview:{short_code}", 86400 * 7, json.dumps(preview_data))
        return f"Preview saved for {short_code}"
    except Exception as e:
        return f"Failed to fetch preview:{str(e)}"

@celery.task
def cleanup_expired_links():
    user_keys = r.keys("user:*:links")
    for key in user_keys:
        links = r.smembers(key)
        for link_code in links:
            if not r.exists(f"url:{link_code}"):
                r.srem(key, link_code)
    return "Cleanup completed"

celery.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'worker.cleanup_expired_links',
        'schedule': 3600.0,
    },
}