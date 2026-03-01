class CipherManager:
    @staticmethod
    def  get_default_ciphers()-> list:
        return [
            "ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-SHA384", "ECDHE-ECDSA-AES256-SHA384",
            "ECDHE-RSA-AES256-SHA", "ECDHE-ECDSA-AES256-SHA",
            "ECDHE-RSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-SHA256",
            "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-ECDSA-AES128-SHA256",
            "AES256-SHA", "AES128-SHA"
        ]

    def __init__(self,cipher_list=None):
        if cipher_list == None:
            cipher_list=self.get_default_ciphers()
        self.cipher_list = cipher_list
        self.create_list()
        self.ciphers_string = self.add_string_list()
    def add_string_list(self):
        if len(self.cipher_list)==0:
            return ''
        return','.join(self.cipher_list)
    def create_list(self):
        if self.cipher_list == None:
            self.cipher_list= []
        elif isinstance(self.cipher_list, str):
            self.cipher_list=self.cipher_list.split(',')
        if isinstance(self.cipher_list, str):
            self.cipher_list=[self.cipher_list]
class CipherManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(cipher_list=None):
        if CipherManagerSingleton._instance is None:
            CipherManagerSingleton._instance = CipherManager(cipher_list=cipher_list)
        elif CipherManagerSingleton._instance.cipher_list != cipher_list:
            CipherManagerSingleton._instance = CipherManager(cipher_list=cipher_list)
        return CipherManagerSingleton._instance
