import re
import urllib.parse
import requests
from urllib.parse import urlparse, urlunparse, urljoin

from ...abstract_webtools import *

class urlManager:
    """
    Revised urlManager for managing and cleaning URLs.
    
    It splits URLs into their components, normalizes them (trimming spaces, lowercasing
    scheme and domain, removing default ports, and cleaning up paths), and then creates
    a list of potential variants (with/without www, http/https) so that a valid version
    can be determined.
    """
    def __init__(self, url=None, session=None):
        url = url or 'www.example.com'
        self._url = url
        self.session = session or requests
        self.clean_urls = self.clean_url(url)
        self.url = self.get_correct_url(clean_urls=self.clean_urls) or url
        self.protocol, self.domain, self.path, self.query = self.url_to_pieces(self.url)
        self.all_urls = []
    
    def url_to_pieces(self, url):
        """
        Split a URL into protocol, domain, path, and query components.
        Uses urlparse for robustness.
        """
        try:
            parsed = urlparse(url)
            protocol = parsed.scheme if parsed.scheme else None
            domain = parsed.netloc if parsed.netloc else None
            path = parsed.path or ""
            query = parsed.query or ""
        except Exception as e:
            print(f'The URL {url} was not reachable: {e}')
            protocol, domain, path, query = None, None, "", ""
        return protocol, domain, path, query

    def clean_url(self, url=None) -> list:
        """
        Normalize and clean the URL, then return a list of potential URL variants.
        
        This method:
          - Strips whitespace.
          - Adds a scheme (defaults to https) if missing.
          - Lowercases the scheme and domain.
          - Removes default ports.
          - Cleans up the path (removing duplicate slashes and trailing slash).
          - Generates variants with and without 'www', and with both http and https.
        """
        url = url or self._url
        url = url.strip()
        # Ensure the URL has a scheme
        if not re.match(r'https?://', url):
            url = 'https://' + url

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Remove default port numbers if present
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                netloc = host
        
        # Normalize the path: remove duplicate slashes and a trailing slash
        path = re.sub(r'//+', '/', parsed.path).rstrip('/')
        
        # Rebuild the cleaned URL without query or fragment
        cleaned_url = urlunparse((scheme, netloc, path, '', '', ''))
        
        variants = []
        # Add the primary variant
        variants.append(cleaned_url)
        # Generate a variant with/without 'www'
        if netloc.startswith('www.'):
            no_www = netloc[4:]
            variants.append(urlunparse((scheme, no_www, path, '', '', '')))
        else:
            variants.append(urlunparse((scheme, f"www.{netloc}", path, '', '', '')))
        
        # Also generate variants with the alternate scheme
        alt_scheme = 'http' if scheme == 'https' else 'https'
        for variant in list(variants):
            parsed_variant = urlparse(variant)
            alt_variant = urlunparse((alt_scheme, parsed_variant.netloc, parsed_variant.path, '', '', ''))
            variants.append(alt_variant)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                unique_variants.append(v)
                seen.add(v)
        return unique_variants

    def get_correct_url(self, url=None, clean_urls=None) -> str:
        """
        Attempts each URL variant by making an HTTP GET request.
        Returns the first variant that returns a 200 OK response.
        """
        if url is None and clean_urls is None:
            url = self._url
            clean_urls = self.clean_urls
        if url is not None and clean_urls is None:
            clean_urls = self.clean_url(url)
        elif url is None and clean_urls is not None:
            url = self._url

        for candidate in clean_urls:
            try:
                response = self.session.get(candidate, timeout=5)
                if response.status_code == 200:
                    return candidate
            except requests.exceptions.RequestException as e:
                print(f"Failed to reach {candidate}: {e}")
        return None

    def update_url(self, url):
        """
        Update the URL and refresh related attributes.
        """
        self._url = url
        self.clean_urls = self.clean_url(url)
        self.url = self.get_correct_url(clean_urls=self.clean_urls) or url
        self.protocol, self.domain, self.path, self.query = self.url_to_pieces(self.url)
        self.all_urls = []

    def get_domain(self, url=None):
        url = url or self.url
        return urlparse(url).netloc

    def url_join(self, base_url, path):
        """
        Joins a base URL with a relative path.
        """
        base_url = base_url.strip().rstrip('/')
        path = path.strip().lstrip('/')
        return f"{base_url}/{path}"

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
        url = url or self.url
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    
    def make_valid(self, href, url=None):
        """
        Validate a href. If it's not already valid, join it with the base URL.
        """
        if self.is_valid_url(href):
            return href
        base = url or self.url
        new_link = urljoin(base, href)
        if self.is_valid_url(new_link):
            return new_link
        return False

    def get_relative_href(self, base, href):
        """
        For a relative href, join it with the base URL and strip any query or fragment.
        """
        joined = urljoin(base, href)
        parsed = urlparse(joined)
        clean_href = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return clean_href

    def url_basename(self, url=None):
        url = url or self.url
        path = urlparse(url).path
        return path.strip('/').split('/')[-1]

    def base_url(self, url=None):
        url = url or self.url
        match = re.match(r'https?://[^?#/]+/', url)
        if match:
            return match.group()
        return None

    def urljoin(self, base, path):
        return urljoin(base, path)

class urlManagerSingleton:
    _instance = None

    @staticmethod
    def get_instance(url=None, session=requests):
        if urlManagerSingleton._instance is None:
            urlManagerSingleton._instance = urlManager(url, session=session)
        elif urlManagerSingleton._instance.session != session or urlManagerSingleton._instance.url != url:
            urlManagerSingleton._instance = urlManager(url, session=session)
        return urlManagerSingleton._instance

def get_url(url=None, url_mgr=None):
    if not url and not url_mgr:
        return None
    if url:
        url_mgr = urlManager(url)
    return url_mgr.url

def get_url_mgr(url=None, url_mgr=None):
    if url_mgr is None and url:
         url_mgr = urlManager(url=url)
    if url_mgr and url is None:
        url = url_mgr.url
    return url_mgr
