class MySocketClient:
    def __init__(self, ip_address=None, port=None,domain=None):
        self.sock
        self.ip_address= ip_address or None
        self.port = port  or None
        
        self.domain = domain  or None
    def receive_data(self):
        chunks = []
        while True:
            chunk = self.sock.recv(4096)
            if chunk:
                chunks.append(chunk)
            else:
                break
        return b''.join(chunks).decode('utf-8')
    def _parse_socket_response_as_json(self, data, *args, **kwargs):
        return self._parse_json(data[data.find('{'):data.rfind('}') + 1], *args, **kwargs)
    def process_data(self):
        data = self.receive_data()
        return self._parse_socket_response_as_json(data)
    def _parse_json(self,json_string):
        return json.loads(json_string)
    def get_ip(self,domain=None):
        try:
            return self.sock.gethostbyname(domain if domain != None else self.domain)
        except self.sock.gaierror:
            return None
    def grt_host_name(self,ip_address=None):
        return self.sock.gethostbyaddr(ip_address if ip_address != None else self.ip_address)
    def toggle_sock(self):
        if self.sock != None:
            self.sock.close()
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if host and socket:
                self.sock.connect((host, port))
class MySocketClient():
    _instance = None
    @staticmethod
    def get_instance(ip_address='local_host',port=22,domain="example.com"):
        if MySocketClientSingleton._instance is None:
            MySocketClientSingleton._instance = MySocketClient(ip_address=ip_address,port=port,domain=domain)
        elif MySocketClientSingleton._instance.ip_address != ip_address or MySocketClientSingleton._instance.port != port or UrlManagerSingleton._instance.domain != domain:
            MySocketClientSingleton._instance = MySocketClient(ip_address=ip_address,port=port,domain=domain)
        return MySocketClient
