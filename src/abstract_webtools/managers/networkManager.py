from typing import Optional, List
import requests
from ..abstract_webtools import *
from .sslManager import SSLManager
from .cipherManager import CipherManager

class TLSAdapter(HTTPAdapter):
    def __init__(self, ssl_manager: SSLManager=None):
        ssl_manager = ssl_manager or SSLManager()
        self.ssl_context = ssl_manager.ssl_context
        super().__init__()
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

class NetworkManager:
    def __init__(self, user_agent_manager=None, ssl_manager=None, proxies=None, cookies=None,
                 ciphers=None, certification: Optional[str]=None, ssl_options: Optional[List[str]]=None):
        self.ua_mgr = user_agent_manager or UserAgentManager()
        self.ssl_mgr = ssl_manager or SSLManager(
            ciphers=ciphers or CipherManager().ciphers_string,
            ssl_options=ssl_options,
            certification=certification
        )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.ua_mgr.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        })
        adapter = TLSAdapter(self.ssl_mgr)
        self.session.mount("https://", adapter)
        self.session.mount("http://", HTTPAdapter())

        if proxies:
            self.session.proxies = proxies
        if cookies:
            if isinstance(cookies, requests.cookies.RequestsCookieJar):
                self.session.cookies = cookies
            elif isinstance(cookies, dict):
                jar = requests.cookies.RequestsCookieJar()
                for k,v in cookies.items(): jar.set(k,v)
                self.session.cookies = jar
            # if string: up to you—parse or ignore

        # retries (optional)
        from requests.adapters import Retry
        self.session.adapters['https://'].max_retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429,500,502,503,504])
