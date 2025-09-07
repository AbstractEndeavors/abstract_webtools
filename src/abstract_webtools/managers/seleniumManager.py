import os, time, re, json, logging, urllib3, requests,tempfile, shutil, socket, atexit, errno
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup          # if you prefer, keep using your parser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from abstract_security import get_env_value
from abstract_utilities import *
from .urlManager import *               # your urlManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)

# ---- Chrome options (keep yours; add safe fallbacks) ----
chrome_options = Options()
_bin = get_env_value('CHROME_BINARY')
if _bin:
    chrome_options.binary_location = _bin
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.experimental_options["prefs"] = chrome_prefs

MIN_HTML_BYTES = 2048  # tune: consider <2KB suspicious for real pages
# --- NEW helpers: unique temp profile + free port + options builder ---

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def _make_profile_dir(base="/var/tmp/selenium-profiles") -> str:
    os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(prefix="cw-", dir=base)

def _make_chrome_options(binary_path: str | None = None,
                         user_data_dir: str | None = None) -> tuple[Options, str]:
    opts = Options()
    if binary_path:
        opts.binary_location = binary_path
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-extensions")

    prof = user_data_dir or _make_profile_dir()
    opts.add_argument(f"--user-data-dir={prof}")
    opts.add_argument(f"--remote-debugging-port={_free_port()}")

    prefs = {"profile.managed_default_content_settings.images": 2}
    opts.add_experimental_option("prefs", prefs)
    return opts, prof


def _looks_like_html(text_or_bytes: bytes | str) -> bool:
    if not text_or_bytes:
        return False
    s = text_or_bytes if isinstance(text_or_bytes, str) else text_or_bytes.decode("utf-8", "ignore")
    if len(s) < MIN_HTML_BYTES:
        return False
    lowered = s.lower()
    return ("<html" in lowered and "</html>" in lowered) or "<body" in lowered

def _requests_fallback(url: str, headers: dict | None = None, timeout: float = 15.0):
    """Plain requests fallback. Returns `requests.Response | None`."""
    try:
        sess = requests.Session()
        sess.headers.update(headers or {"User-Agent": "Mozilla/5.0"})
        # honor simple redirects and cert issues as needed
        resp = sess.get(url, timeout=timeout, allow_redirects=True, verify=False)
        return resp
    except Exception as e:
        logging.warning(f"requests fallback failed for {url}: {e}")
        return None

def _wait_until_ready(driver, timeout: float = 10.0):
    """Waits for DOM readiness and presence of <body>."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )
    except Exception:
        pass
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        pass
    # small settle delay for late JS injections
    time.sleep(0.3)
def normalize_url(url, base_url=None):
    manager = seleniumManager(url)
    base_url = manager.base_url
    if url.startswith(base_url):
        url = url[len(base_url):]
    normalized_url = urljoin(base_url, url.split('#')[0])
    if not normalized_url.startswith(base_url):
        return None
    return normalized_url
# ---- Singleton driver manager (your class; small fixes) ----
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class seleniumManager(metaclass=SingletonMeta):
    def __init__(self, url):
        if getattr(self, "initialized", False):
            return
        self.initialized = True

        p = urlparse(url)
        self.domain = p.netloc
        self.scheme = p.scheme or "https"
        self.base_url = f"{self.scheme}://{self.domain}"

        self.site_dir = os.path.join("/var/tmp", "cw-sites", self.domain)
        os.makedirs(self.site_dir, exist_ok=True)

        self._sessions: dict[str, dict] = {}  # key -> {"driver": ..., "profile": ...}
        atexit.register(lambda sm=self: sm.close_all())

    def get_url_to_path(self, url):
        url = eatAll(str(url), ['',' ','\n','\t','\\','/'])
        p = urlparse(url)
        if p.netloc == self.domain:
            parts = [x for x in p.path.split('/') if x]
            d = self.site_dir
            for seg in parts[:-1]:
                d = os.path.join(d, seg)
                os.makedirs(d, exist_ok=True)
            last = parts[-1] if parts else "index.html"
            ext = os.path.splitext(last)[-1] or ".html"
            if not hasattr(self, "page_type"):
                self.page_type = []
            self.page_type.append(ext if not self.page_type else self.page_type[-1])
            return os.path.join(d, last)

    def get_with_netloc(self, url):
        p = urlparse(url)
        if p.netloc == '':
            url = f"{self.scheme}://{self.domain}/{url.strip().lstrip('/')}"
        return url

    def get_driver(self, url) -> tuple[str, webdriver.Chrome]:
        bin_path = get_env_value('CHROME_BINARY')
        opts, prof = _make_chrome_options(binary_path=bin_path, user_data_dir=None)
        driver = webdriver.Chrome(options=opts)
        key = f"{url}#{time.time()}"
        self._sessions[key] = {"driver": driver, "profile": prof}
        return key, driver

    def close_driver(self, key: str):
        sess = self._sessions.pop(key, None)
        if not sess: return
        try:
            try: sess["driver"].quit()
            except Exception: pass
        finally:
            shutil.rmtree(sess.get("profile") or "", ignore_errors=True)

    def close_all(self):
        for key in list(self._sessions.keys()):
            self.close_driver(key)



# ---- Hardened page-source retrieval with fallback ----
def get_selenium_source(url, max_retries: int = 2, request_fallback: bool = True, timeout: float = 12.0):
    url_mgr = urlManager(url)
    if not url_mgr.url:
        return None
    url = str(url_mgr.url)

    manager = seleniumManager(url)
    key, driver = manager.get_driver(url)

    last_exc = None
    try:
        for attempt in range(1, max_retries + 1):
            try:
                driver.get(url)
                _wait_until_ready(driver, timeout=timeout)
                html = driver.page_source or ""
                if not _looks_like_html(html):
                    html = driver.execute_script(
                        "return document.documentElement ? document.documentElement.outerHTML : '';"
                    ) or html
                if _looks_like_html(html):
                    return html
                logging.warning(f"Selenium returned suspicious HTML (len={len(html)}) for {url} "
                                f"[attempt {attempt}/{max_retries}]")
            except Exception as e:
                last_exc = e
                logging.warning(f"Selenium attempt {attempt}/{max_retries} failed for {url}: {e}")
            time.sleep(0.5 * attempt)

        if request_fallback:
            resp = _requests_fallback(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp is not None:
                ctype = (resp.headers.get("content-type") or "").lower()
                body = resp.text if hasattr(resp, "text") else (
                    resp.content.decode("utf-8", "ignore") if hasattr(resp, "content") else ""
                )
                if "application/json" in ctype:
                    try:
                        return json.dumps(resp.json())
                    except Exception:
                        return body
                return body if _looks_like_html(body) or body else None
    finally:
        # critical: release the user-data-dir to avoid “already in use”
        manager.close_driver(key)

    if last_exc:
        logging.error(f"Unable to retrieve page for {url}: {last_exc}")
    return None

def get_driver(self, url):
    # always new
    bin_path = get_env_value('CHROME_BINARY')
    opts, prof = _make_chrome_options(binary_path=bin_path, user_data_dir=None)
    driver = webdriver.Chrome(options=opts)
    # store so close_all() can clean up
    key = f"{url}#{time.time()}"
    self._sessions[key] = {"driver": driver, "profile": prof}
    return driver
