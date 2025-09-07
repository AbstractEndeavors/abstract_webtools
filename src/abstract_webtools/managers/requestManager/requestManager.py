from ...abstract_webtools import *
from ..userAgentManager import *
from ..cipherManager import *
from ..sslManager import *
from ..tlsAdapter import *
from ..networkManager import *
from ..seleneumManager import *
from ..urlManager import *
logging.basicConfig(level=logging.INFO)

class requestManager:
    """
    requestManager is a class for making HTTP requests with error handling and retries.
    It supports initializing with a provided source_code without requiring a URL.
    If source_code is provided, it uses that as the response content and skips fetching.
    Enhanced to parse source_code for URLs, PHP blocks, and React/JS data even if not HTML.
    Args:
        url (str or None): The URL to make requests to (default is None).
        url_mgr (urlManager or None): An instance of urlManager (default is None).
        network_manager (NetworkManager or None): An instance of NetworkManager (default is None).
        user_agent_manager (UserAgentManager or None): An instance of UserAgentManager (default is None).
        ssl_manager (SSlManager or None): An instance of SSLManager (default is None).
        tls_adapter (TLSAdapter or None): An instance of TLSAdapter (default is None).
        user_agent (str or None): The user agent string to use for requests (default is None).
        proxies (dict or None): Proxy settings for requests (default is None).
        headers (dict or None): Additional headers for requests (default is None).
        cookies (dict or None): Cookie settings for requests (default is None).
        session (requests.Session or None): A custom requests session (default is None).
        adapter (str or None): A custom adapter for requests (default is None).
        protocol (str or None): The protocol to use for requests (default is 'https://').
        ciphers (str or None): Cipher settings for requests (default is None).
        auth (tuple or None): Authentication credentials (default is None).
        login_url (str or None): The URL for authentication (default is None).
        email (str or None): Email for authentication (default is None).
        password (str or None): Password for authentication (default is None).
        certification (str or None): Certification settings for requests (default is None).
        ssl_options (str or None): SSL options for requests (default is None).
        stream (bool): Whether to stream the response content (default is False).
        timeout (float or None): Timeout for requests (default is None).
        last_request_time (float or None): Timestamp of the last request (default is None).
        max_retries (int or None): Maximum number of retries for requests (default is None).
        request_wait_limit (float or None): Wait time between requests (default is None).

    Methods:
        update_url_mgr(url_mgr): Update the URL manager and reinitialize the SafeRequest.
        update_url(url): Update the URL and reinitialize the SafeRequest.
        re_initialize(): Reinitialize the SafeRequest with the current settings.
        authenticate(s, login_url=None, email=None, password=None, checkbox=None, dropdown=None): Authenticate and make a request.
        fetch_response(): Fetch the response from the server.
        initialize_session(): Initialize the requests session with custom settings.
        process_response_data(): Process the fetched response data.
        get_react_source_code(): Extract JavaScript and JSX source code from <script> tags.
        get_status(url=None): Get the HTTP status code of a URL.
        wait_between_requests(): Wait between requests based on the request_wait_limit.
        make_request(): Make a request and handle potential errors.
        try_request(): Try to make an HTTP request using the provided session.

    Note:
        - The SafeRequest class is designed for making HTTP requests with error handling and retries.
        - It provides methods for authentication, response handling, and error management.
    """
    def __init__(self,url=None,
                 source_code=None,
                 url_mgr=None,
                 network_manager=None,
                 user_agent_manager=None,
                 ssl_manager=None,
                 ssl_options=None,
                 tls_adapter=None,
                 user_agent=None,
                 proxies=None,
                 headers=None,
                 cookies=None,
                 session=None,
                 adapter=None,
                 protocol=None,
                 ciphers=None,
                 spec_login=False,
                 login_referer=None,
                 login_user_agent=None,
                 auth=None,
                 login_url=None,
                 email=None,
                 password=None,
                 checkbox=None,
                 dropdown=None,
                 certification=None,
                 stream=False,
                 timeout=None,
                 last_request_time=None,
                 max_retries=None,
                 request_wait_limit=None):
        self.url_mgr = get_url_mgr(url=url, url_mgr=url_mgr)
        self.url = get_url(url=url, url_mgr=self.url_mgr)
        self._url_mgr = self.url_mgr
        self._url = self.url
        self.user_agent = user_agent
        self.user_agent_manager = user_agent_manager or UserAgentManager(user_agent=self.user_agent)
        self.headers = headers or self.user_agent_manager.header or {'Accept': '*/*'}
        self.user_agent = self.user_agent_manager.user_agent
        self.ciphers = ciphers or CipherManager().ciphers_string
        self.certification = certification
        self.ssl_options = ssl_options
        self.ssl_manager = ssl_manager or SSLManager(ciphers=self.ciphers, ssl_options=self.ssl_options, certification=self.certification)
        self.tls_adapter = tls_adapter or TLSAdapter(ssl_manager=self.ssl_manager, certification=self.certification, ssl_options=self.ssl_manager.ssl_options)
        self.network_manager = network_manager or NetworkManager(user_agent_manager=self.user_agent_manager, ssl_manager=self.ssl_manager, tls_adapter=self.tls_adapter, user_agent=user_agent, proxies=proxies, cookies=cookies, ciphers=ciphers, certification=certification, ssl_options=ssl_options)
        self.stream = stream
        self.tls_adapter = self.network_manager.tls_adapter
        self.ciphers = self.network_manager.ciphers
        self.certification = self.network_manager.certification
        self.ssl_options = self.network_manager.ssl_options
        self.proxies = self.network_manager.proxies
        self.timeout = timeout
        self.cookies = self.network_manager.cookies
        self.session = session or requests.Session()
        self.auth = auth
        self.spec_login = spec_login
        self.password = password
        self.email = email
        self.checkbox = checkbox
        self.dropdown = dropdown
        self.login_url = login_url
        self.login_user_agent = login_user_agent
        self.login_referer = login_referer
        self.protocol = protocol or 'https://'
        self.stream = stream if isinstance(stream, bool) else False
        self.initialize_session()
        self.last_request_time = last_request_time
        self.max_retries = max_retries or 3
        self.request_wait_limit = request_wait_limit or 1.5
        self._response = None
        self.status_code = None
        self.source_code = None
        self.source_code_bytes = None
        self.source_code_json = {}
        self.react_source_code = []
        self.extracted_urls = []
        self.php_blocks = []
        self._response_data = None
        if source_code is not None:
            self._response = source_code
            self.process_response_data()
        else:
            self.re_initialize()

    def update_url_mgr(self, url_mgr):
        self.url_mgr = url_mgr
        self.re_initialize()

    def update_url(self, url):
        self.url_mgr.update_url(url=url)
        self.re_initialize()

    def re_initialize(self):
        self._response = None
        if self.url_mgr.url is not None:
            self.make_request()
        self.source_code = None
        self.source_code_bytes = None
        self.source_code_json = {}
        self.react_source_code = []
        self.extracted_urls = []
        self.php_blocks = []
        self._response_data = None
        self.process_response_data()

    @property
    def response(self):
        """Lazy-loading of response."""
        if self._response is None and self.url_mgr.url is not None:
            self._response = self.fetch_response()
        return self._response

    def authenticate(self, session, login_url=None, email=None, password=None, checkbox=None, dropdown=None):
        login_urls = login_url or [self.url_mgr.url, self.url_mgr.domain, self.url_mgr.url_join(url=self.url_mgr.domain, path='login'), self.url_mgr.url_join(url=self.url_mgr.domain, path='auth')]
        s = session
        if not isinstance(login_urls, list):
            login_urls = [login_urls]
        for login_url in login_urls:
            login_url_mgr = urlManager(login_url)
            login_url = login_url_mgr.url
            r = s.get(login_url)
            soup = BeautifulSoup(r.content, "html.parser")
            # Find the token or any CSRF protection token
            token = soup.find('input', {'name': 'token'}).get('value') if soup.find('input', {'name': 'token'}) else None
            if token is not None:
                break
        login_data = {}
        if email is not None:
            login_data['email'] = email
        if password is not None:
            login_data['password'] = password
        if checkbox is not None:
            login_data['checkbox'] = checkbox
        if dropdown is not None:
            login_data['dropdown'] = dropdown
        if token is not None:
            login_data['token'] = token
        s.post(login_url, data=login_data)
        return s

    def fetch_response(self) -> requests.Response | None | str | bytes:
        """Actually fetches the response from the server."""
        return self.try_request()

    def spec_auth(self, session=None, email=None, password=None, login_url=None, login_referer=None, login_user_agent=None):
        s = session or requests.Session()
        domain = self.url_mgr.url_join(self.url_mgr.get_correct_url(self.url_mgr.domain), 'login') if login_url is None else login_url
        login_url = self.url_mgr.get_correct_url(url=domain)
        login_referer = login_referer or self.url_mgr.url_join(url=login_url, path='?role=fast&to=&s=1&m=1&email=YOUR_EMAIL')
        login_user_agent = login_user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:50.0) Gecko/20100101 Firefox/50.0'
        headers = {"Referer": login_referer, 'User-Agent': login_user_agent}
        payload = {'email': email, 'pass': password}
        page = s.get(login_url)
        soup = BeautifulSoup(page.content, 'lxml')
        action_url = soup.find('form')['action']
        s.post(action_url, data=payload, headers=headers)
        return s

    def initialize_session(self):
        s = self.session
        if self.auth:
            s = self.auth
        elif self.spec_login:
            s = self.spec_auth(session=s, email=self.email, password=self.password, login_url=self.login_url, login_referer=self.login_referer, login_user_agent=self.login_user_agent)
        elif any([self.password, self.email, self.login_url, self.checkbox, self.dropdown]):
            s = self.authenticate(session=s, login_url=self.login_url, email=self.email, password=self.password, checkbox=self.checkbox, dropdown=self.dropdown)
        s.proxies = self.proxies
        s.cookies["cf_clearance"] = self.network_manager.cookies
        s.headers.update(self.headers)
        s.mount(self.protocol, self.network_manager.tls_adapter)
        return s

    def process_response_data(self):
        """Processes the fetched response data."""
        if not self.response:
            return  # No data to process
        if isinstance(self.response, (str, bytes)):
            if isinstance(self.response, str):
                self.source_code = self.response
                self.source_code_bytes = self.response.encode('utf-8')  # Assume UTF-8
            else:
                self.source_code_bytes = self.response
                try:
                    self.source_code = self.response.decode('utf-8')
                except UnicodeDecodeError:
                    self.source_code = self.response.decode('latin-1')  # Fallback
            # Check if it's JSON
            try:
                data = json.loads(self.source_code)
                self.source_code_json = data.get("response", data)
            except json.JSONDecodeError:
                pass
        else:
            self.source_code = self.response.text
            self.source_code_bytes = self.response.content
            if self.response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = json.loads(self.source_code)
                    self.source_code_json = data.get("response", data)
                except json.JSONDecodeError:
                    pass
        self.extract_urls()
        self.extract_php_blocks()
        self.get_react_source_code()

    def extract_urls(self):
        """Extract URLs from source_code using regex."""
        if not self.source_code:
            return
        url_pattern = r'https?://[^\s<>"\']+'
        self.extracted_urls = re.findall(url_pattern, self.source_code)

    def extract_php_blocks(self):
        """Extract PHP blocks from source_code if present."""
        if not self.source_code:
            return
        php_pattern = r'<\?php(.*?)?\?>'
        self.php_blocks = re.findall(php_pattern, self.source_code, re.DOTALL)

    def get_react_source_code(self) -> list:
        """
        Extracts JavaScript and JSX source code from <script> tags if HTML-like.
        If not HTML and looks like JS/React code, appends the whole source_code.
        """
        if not self.source_code:
            return []
        # Check if likely JS code (e.g., contains 'import', 'function', 'React')
        is_js_like = any(keyword in self.source_code.lower() for keyword in ['import ', 'function ', 'react', 'export ', 'const ', 'let ', 'var '])
        # Check if HTML-like
        is_html_like = self.source_code.strip().startswith('<') or '<html' in self.source_code.lower() or '<!doctype' in self.source_code.lower()
        if not is_html_like and is_js_like:
            self.react_source_code.append(self.source_code)
            return self.react_source_code
        content = self.source_code_bytes or self.source_code.encode('utf-8')
        soup = BeautifulSoup(content, "html.parser")
        script_tags = soup.find_all('script', type=lambda t: t and ('javascript' in t.lower() or 'jsx' in t.lower()))
        for script_tag in script_tags:
            if script_tag.string:
                self.react_source_code.append(script_tag.string)
        # If no scripts found but JS-like, append whole
        if not script_tags and is_js_like:
            self.react_source_code.append(self.source_code)
        return self.react_source_code

    def get_status(self, url: str = None) -> int | None:
        """
        Gets the HTTP status code of the given URL.
        """
        url = url or self.url_mgr.url
        if url is None:
            return None
        try:
            response = requests.head(url, timeout=5)
            return response.status_code
        except requests.RequestException:
            return None

    def wait_between_requests(self):
        """
        Wait between requests based on the request_wait_limit.
        """
        if self.last_request_time:
            sleep_time = self.request_wait_limit - (time.time() - self.last_request_time)
            if sleep_time > 0:
                logging.info(f"Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)

    def make_request(self):
        """
        Make a request and handle potential errors, with retries.
        """
        if self.url_mgr.url is None:
            return None

        self.wait_between_requests()
        for _ in range(self.max_retries):
            try:
                self._response = self.try_request()
                if self._response:
                    if not isinstance(self._response, (str, bytes)):
                        self.status_code = self._response.status_code
                        if self._response.status_code == 200:
                            self.last_request_time = time.time()
                            return self._response
                        elif self._response.status_code == 429:
                            logging.warning(f"Rate limited by {self.url_mgr.url}. Retrying...")
                            time.sleep(5)
                    else:
                        # String/bytes from Selenium path
                        self.status_code = 200
                        return self._response
            except requests.Timeout as e:
                logging.error(f"Request to {self.url_mgr.url} timed out: {e}")
            except requests.ConnectionError:
                logging.error(f"Connection error for URL {self.url_mgr.url}.")
            except requests.RequestException as e:
                logging.error(f"Request exception for URL {self.url_mgr.url}: {e}")

        logging.error(f"Failed to retrieve content from {self.url_mgr.url} after {self.max_retries} retries")
        return None

    def try_request(self) -> requests.Response | str | bytes | None:
        """
        Tries Selenium first, then falls back to requests if Selenium fails.
        """
        if self.url_mgr.url is None:
            return None

        # 1. Try Selenium
        try:
            return get_selenium_source(self.url_mgr.url)
        except Exception as e:
            logging.warning(f"Selenium failed for {self.url_mgr.url}, falling back to requests: {e}")

        # 2. Fallback: requests
        try:
            resp = self.session.get(
                self.url_mgr.url,
                timeout=self.timeout or 10,
                stream=self.stream
            )
            return resp
        except requests.RequestException as e:
            logging.error(f"Requests fallback also failed for {self.url_mgr.url}: {e}")
            return None

        @property
        def url(self):
            return self.url_mgr.url

        @url.setter
        def url(self, new_url):
            self._url = new_url
class SafeRequestSingleton:
    _instance = None
    @staticmethod
    def get_instance(url=None,headers:dict=None,max_retries=3,last_request_time=None,request_wait_limit=1.5):
        if SafeRequestSingleton._instance is None:
            SafeRequestSingleton._instance = SafeRequest(url,url_mgr=urlManagerSingleton,headers=headers,max_retries=max_retries,last_request_time=last_request_time,request_wait_limit=request_wait_limit)
        elif SafeRequestSingleton._instance.url != url or SafeRequestSingleton._instance.headers != headers or SafeRequestSingleton._instance.max_retries != max_retries or SafeRequestSingleton._instance.request_wait_limit != request_wait_limit:
            SafeRequestSingleton._instance = SafeRequest(url,url_mgr=urlManagerSingleton,headers=headers,max_retries=max_retries,last_request_time=last_request_time,request_wait_limit=request_wait_limit)
        return SafeRequestSingleton._instance
def get_source(url=None,url_mgr=None,source_code=None,req_mgr=None):
    req_mgr = get_req_mgr(req_mgr=req_mgr,url=url,url_mgr=url_mgr,source_code=source_code)
    return req_mgr.source_code
def get_req_mgr(url=None,url_mgr=None,source_code=None,req_mgr=None):
    url = get_url(url=url,url_mgr=url_mgr)
    url_mgr = get_url_mgr(url=url,url_mgr=url_mgr )
    req_mgr = req_mgr  or requestManager(url_mgr=url_mgr,url=url,source_code=source_code)
    return req_mgr
