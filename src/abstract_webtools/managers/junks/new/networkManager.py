from ..abstract_webtools import *
from ..big_user_agent_list import *
class NetworkManager:
    def __init__(self, user_agent_manager=None,ssl_manager=None, tls_adapter=None,user_agent=None,proxies=None,cookies=None,ciphers=None, certification: Optional[str] = None, ssl_options: Optional[List[str]] = None):
        if ssl_manager == None:
            ssl_manager = SSLManager(ciphers=ciphers, ssl_options=ssl_options, certification=certification)
        self.ssl_manager=ssl_manager
        if tls_adapter == None:
            tls_adapter=TLSAdapter(ssl_manager=ssl_manager,ciphers=ciphers, certification=certification, ssl_options=ssl_options)
        self.tls_adapter=tls_adapter
        self.ciphers=tls_adapter.ciphers
        self.certification=tls_adapter.certification
        self.ssl_options=tls_adapter.ssl_options
        self.proxies=None or {}
        self.cookies=cookies or "cb4c883efc59d0e990caf7508902591f4569e7bf-1617321078-0-150"
