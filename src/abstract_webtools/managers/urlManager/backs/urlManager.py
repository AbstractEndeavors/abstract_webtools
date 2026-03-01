import re
import logging
import requests
from urllib.parse import urlparse, urlunparse, urljoin

logging.basicConfig(level=logging.INFO)

class urlManager:
    """
    Revised urlManager for managing and cleaning URLs.
    
    It splits URLs into their components, normalizes them (trimming spaces, lowercasing
    scheme and domain, removing default ports, and cleaning up paths), and then creates
    a list of potential variants (with/without www, http/https) so that a valid version
    can be determined.
    
    Now handles url=None gracefully: sets internals to None/empty and methods return None or empty values without errors.
    """
    def __init__(self, url=None, session=None):
            self._url = url  # Allow None
            self.session = session or requests.Session()
            if self._url is None:
                self.clean_urls = []
                self.url = None
                self.protocol = None
                self.domain = None
                self.path = ""
                self.query = ""
                self.all_urls = []
            else:
                self.clean_urls = self.clean_url()
                self.url = self.get_correct_url() or self._url
                self.protocol, self.domain, self.path, self.query = self.url_to_pieces(self.url)
                self.all_urls = []

    def url_to_pieces(self, url):
        """
        Split a URL into protocol, domain, path, and query components.
        Uses urlparse for robustness.
        """
        if url is None:
            return None, None, "", ""
        parsed = urlparse(url)
        protocol = parsed.scheme or None
        domain = parsed.netloc or None
        path = parsed.path or ""
        query = parsed.query or ""
        return protocol, domain, path, query

    def clean_url(self, url=None) -> list:
        """
        Normalize and clean the URL, then return a list of potential URL variants.
        Now uses ALL_URL_KEYS for scheme/www/extention cycling.
        """
        url = (url or self._url)
        if url is None:
            return []
        url = url.strip()
        if not url:
            return []

        # Add default scheme if missing
        if not re.match(r'https?://', url, re.IGNORECASE):
            url = f"{ALL_URL_KEYS['scheme'][0]}://{url}"

        parsed = urlparse(url)
        scheme = parsed.scheme.lower() if parsed.scheme else ALL_URL_KEYS["scheme"][0]
        netloc = parsed.netloc.lower()

        # Fix bareword case (e.g., "thedailydialectics")
        if not netloc and parsed.path:
            netloc = parsed.path.strip('/')
            parsed = parsed._replace(netloc=netloc, path="")

        # Strip default ports
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                netloc = host

        # Split into domain+ext
        ext_found = False
        for ext in sorted(ALL_EXTENTIONS, key=len, reverse=True):
            if netloc.endswith(ext):
                base_domain = netloc[:-len(ext)]
                ext_found = True
                break
        if not ext_found:
            base_domain, ext = netloc, ""

        # Generate variants from ALL_URL_KEYS
        variants = []
        for s in ALL_URL_KEYS["scheme"]:
            for www in ALL_URL_KEYS["netloc"]["www"]:
                for ext_cand in (ALL_URL_KEYS["netloc"]["extentions"][0] + ALL_URL_KEYS["netloc"]["extentions"][1]):
                    if ext and not ext_cand.startswith(ext):
                        continue  # preserve given extension
                    candidate_netloc = f"{'www.' if www else ''}{base_domain}{ext_cand or ext}"
                    candidate_url = urlunparse((s, candidate_netloc, parsed.path, parsed.params, parsed.query, ''))
                    variants.append(candidate_url)

        # Deduplicate + sort (prefer https)
        seen = set()
        unique_variants = [v for v in variants if not (v in seen or seen.add(v))]
        unique_variants.sort(key=lambda v: (not v.startswith('https'), v))
        return unique_variants


    def get_correct_url(self, url=None, clean_urls=None) -> str:
        """
        Attempts each URL variant by making an HTTP HEAD request (lighter than GET).
        Returns the first variant that returns a 200 OK response.
        """
        if self._url is None:
            return None
        clean_urls = clean_urls or self.clean_urls
        url = url or self._url
        if not clean_urls:
            clean_urls = self.clean_url(url)
        for candidate in clean_urls:
            try:
                response = self.session.head(candidate, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    return candidate
            except requests.exceptions.RequestException as e:
                logging.info(f"Failed to reach {candidate}: {e}")
        return None

    def update_url(self, url):
        """
        Update the URL and refresh related attributes.
        """
        self._url = url
        if self._url is None:
            self.clean_urls = []
            self.url = None
            self.protocol = None
            self.domain = None
            self.path = ""
            self.query = ""
            self.all_urls = []
        else:
            self.clean_urls = self.clean_url(url)
            self.url = self.get_correct_url() or url
            self.protocol, self.domain, self.path, self.query = self.url_to_pieces(self.url)
            self.all_urls = []

    def get_domain(self, url=None):
        if self._url is None and url is None:
            return None
        url = url or self.url
        return urlparse(url).netloc

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, new_url):
        self._url = new_url

    def is_valid_url(self, url=None):
        """
        Check if the given URL is valid.
        """
        if url is None and self._url is None:
            return False
        url = url or self.url
        if url is None:
            return False
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)

    def make_valid(self, href, url=None):
        """
        Validate a href. If it's not already valid, join it with the base URL.
        """
        if self._url is None and url is None:
            return None
        if self.is_valid_url(href):
            return href
        base = url or self.url
        if base is None:
            return None
        new_link = urljoin(base, href)
        if self.is_valid_url(new_link):
            return new_link
        return None

    def get_relative_href(self, base, href):
        """
        For a relative href, join it with the base URL and strip any query or fragment.
        """
        if base is None:
            return None
        joined = urljoin(base, href)
        parsed = urlparse(joined)
        clean_href = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return clean_href

    def url_basename(self, url=None):
        if self._url is None and url is None:
            return ""
        url = url or self.url
        if url is None:
            return ""
        path = urlparse(url).path
        return path.strip('/').split('/')[-1]

    def base_url(self, url=None):
        if self._url is None and url is None:
            return None
        url = url or self.url
        if url is None:
            return None
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, '/', '', '', ''))

    def urljoin(self, base, path):
        if base is None:
            return None
        return urljoin(base, path)

class urlManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(url=None, session=requests.Session()):
        if urlManagerSingleton._instance is None:
            urlManagerSingleton._instance = urlManager(url, session=session)
        elif urlManagerSingleton._instance.session != session or urlManagerSingleton._instance.url != url:
            urlManagerSingleton._instance = urlManager(url, session=session)
        return urlManagerSingleton._instance
def get_url(url=None,url_mgr=None):
    url_mgr = get_url_mgr(url=url,url_mgr=url_mgr)
    return url_mgr.url
def get_url_mgr(url=None,url_mgr=None):
    return url_mgr or urlManager(url)

