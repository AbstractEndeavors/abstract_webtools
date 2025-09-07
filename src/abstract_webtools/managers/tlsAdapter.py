# tls_adapter.py
from typing import Optional, List
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# If these live in your package root, adjust the import as needed:
from ..abstract_webtools import SSLManager

class TLSAdapter(HTTPAdapter):
    """
    Requests adapter that injects a preconfigured SSLContext (from SSLManager)
    into both the main pool and any proxy pools.
    """
    def __init__(
        self,
        ssl_manager: Optional[SSLManager] = None,
        ciphers: Optional[List[str]] = None,
        certification: Optional[int] = None,   # e.g. ssl.CERT_REQUIRED
        ssl_options: Optional[int] = None
    ) -> None:
        self.ssl_manager = ssl_manager or SSLManager(
            ciphers=ciphers,
            ssl_options=ssl_options,
            certification=certification,
        )
        # expose a few attrs if you compare in the singleton
        self.ciphers = self.ssl_manager.ciphers
        self.certification = self.ssl_manager.certification
        self.ssl_options = self.ssl_manager.ssl_options
        self.ssl_context = self.ssl_manager.ssl_context
        super().__init__()

    def init_poolmanager(self, *args, **kwargs) -> None:
        kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs) -> PoolManager:
        proxy_kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


class TLSAdapterSingleton:
    _instance: Optional[TLSAdapter] = None

    @staticmethod
    def get_instance(
        ciphers: Optional[List[str]] = None,
        certification: Optional[int] = None,
        ssl_options: Optional[int] = None
    ) -> TLSAdapter:
        inst = TLSAdapterSingleton._instance
        if (
            inst is None
            or inst.ciphers != ciphers
            or inst.certification != certification
            or inst.ssl_options != ssl_options
        ):
            inst = TLSAdapter(
                ciphers=ciphers,
                certification=certification,
                ssl_options=ssl_options,
            )
            TLSAdapterSingleton._instance = inst
        return inst
