# sslManager.py
import ssl, certifi

class SSLManager:
    def __init__(self, ciphers=None, ssl_options=None, certification=None, cafile=None):
        self.ciphers = ciphers or CipherManager().ciphers_string
        self.ssl_options = ssl_options or self.get_default_ssl_settings()
        self.certification = certification or ssl.CERT_REQUIRED
        self.cafile = cafile or certifi.where()          # << add this
        self.ssl_context = self.get_context()

    def get_default_ssl_settings(self):
        return ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_COMPRESSION

    def get_context(self):
        ctx = ssl_.create_urllib3_context(
            ciphers=self.ciphers,
            cert_reqs=self.certification,
            options=self.ssl_options,
        )
        # load CA roots
        ctx.load_verify_locations(cafile=self.cafile)    # << add this
        return ctx
