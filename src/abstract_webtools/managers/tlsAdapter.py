from ..abstract_webtools import *
class TLSAdapter(HTTPAdapter):
    def __init__(self, ssl_manager=None,ciphers=None, certification: Optional[str] = None, ssl_options: Optional[List[str]] = None):
        if ssl_manager == None:
            ssl_manager = SSLManager(ciphers=ciphers, ssl_options=ssl_options, certification=certification)
        self.ssl_manager = ssl_manager
        self.ciphers = ssl_manager.ciphers
        self.certification = ssl_manager.certification
        self.ssl_options = ssl_manager.ssl_options
        self.ssl_context = self.ssl_manager.ssl_context
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)
class TLSAdapterSingleton:
    _instance: Optional[TLSAdapter] = None
    
    @staticmethod
    def get_instance(ciphers: Optional[List[str]] = None, certification: Optional[str] = None, ssl_options: Optional[List[str]] = None) -> TLSAdapter:
        if (not TLSAdapterSingleton._instance) or (
            TLSAdapterSingleton._instance.ciphers != ciphers or 
            TLSAdapterSingleton._instance.certification != certification or 
            TLSAdapterSingleton._instance.ssl_options != ssl_options
        ):
            TLSAdapterSingleton._instance = TLSAdapter(ciphers=ciphers, certification=certification, ssl_options=ssl_options)
        return TLSAdapterSingleton._instance
