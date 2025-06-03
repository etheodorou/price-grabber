import time, random, logging, requests
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)

def _build_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=5, backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    })
    return s

_session = _build_session()

def get(url: str, **kwargs) -> requests.Response:
    """One-liner wrapper with random jitter & simple log."""
    sleep = random.uniform(0.3, 1.0)
    time.sleep(sleep)
    logger.debug("GET %s (sleep %.2fs)", url, sleep)
    resp = _session.get(url, timeout=20, **kwargs)
    resp.raise_for_status()
    return resp
