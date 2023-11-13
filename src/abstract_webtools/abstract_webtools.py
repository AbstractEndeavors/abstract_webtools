"""
# `abstract_webtools.py` Documentation

This script, `abstract_webtools.py`, is a component of the `abstract_webtools` module and is a part of the `abstract_essentials` package. It provides a set of tools and functions to interact with and parse web content.

## Contents

1. **Imports**
   - Essential modules and classes for web requests, SSL configurations, and URL parsing are imported at the beginning.

2. **Core Functions**

   - `get_status(url: str) -> int or None`:
     Fetches the HTTP status code for a given URL.

   - `clean_url(url: str) -> list`:
     Returns variations of the given URL with different protocols.

   - `get_correct_url(url: str, session: requests.Session) -> str or None`:
     Identifies the correct URL from possible variations using HTTP requests.

   - `try_request(url: str, session: requests.Session) -> requests.Response or None`:
     Attempts to make an HTTP request to a given URL.

   - `is_valid(url: str) -> bool`:
     Validates if a given URL is structurally correct.

   - `desktop_user_agents() -> list`:
     Returns a list of popular desktop user-agent strings.

   - `get_user_agent(user_agent: str) -> dict`:
     Returns a dictionary containing the user-agent header.

3. **TLSAdapter Class**

   A custom HTTPAdapter class that manages SSL options and ciphers for web requests.

   - `TLSAdapter.__init__(self, ssl_options: int)`: 
     Initializes the adapter with specific SSL options.

   - Several methods to handle cipher strings, creation of cipher strings, and initialization of the pool manager with custom SSL configurations.

4. **Advanced Web Functions**

   - `get_Source_code(url: str, user_agent: str) -> str or None`:
     Retrieves the source code of a website with a custom user-agent.

   - `parse_react_source(url: str) -> list`:
     Extracts JavaScript and JSX source code from the specified URL.

   - `get_all_website_links(url: str) -> list`:
     Lists all the internal URLs found on a specific webpage.

   - `parse_all(url: str) -> dict`:
     Parses source code to extract details about elements, attributes, and class names.

   - `extract_elements(url: str, element_type: str, attribute_name: str, class_name: str)`:
     Extracts specific portions of source code based on provided filters. The function signature seems to be cut off, so the full details aren't available.

## Usage

The functions and classes provided in this module allow users to interact with websites, from simple actions like getting the status code of a URL to more advanced functionalities such as parsing ReactJS source codes or extracting specific HTML elements from a website.

To utilize this module, simply import the required function or class and use it in your application. The functions have been designed to be intuitive and the provided docstrings give clear guidance on their usage.

Author: putkoff
Version: 1.0
"""
# -*- coding: UTF-8 -*-
# Google Chrome Driver
import os
import ssl
import re
import yt_dlp
import socket
import shutil
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import xml.etree.ElementTree as ET
from typing import Optional,List,Union
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse, urljoin
from requests.packages.urllib3.util import ssl_
from requests.packages.urllib3.poolmanager import PoolManager
from abstract_utilities import get_time_stamp,get_sleep,sleep_count_down,eatInner,eatAll,eatOuter,ThreadManager
logging.basicConfig(level=logging.INFO)

class DynamicRateLimiterManager:
    def __init__(self):
        # Key: Service Name, Value: DynamicRateLimiter instance
        self.services = {}
    
    def add_service(self, service_name="default", low_limit=10, high_limit=30, limit_epoch=60,starting_tokens=10,epoch_cycle_adjustment=True):
        if service_name in self.services:
            print(f"Service {service_name} already exists!")
            return
        self.services[service_name] = DynamicRateLimiter(service_name=service_name, low_limit=low_limit, high_limit=limit_epoch, limit_epoch=60,starting_tokens=starting_tokens,epoch_cycle_adjustment=epoch_cycle_adjustment)
    
    def request(self, service_name):
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found!")
        
        limiter = self.services[service_name]
        can_request = limiter.request()
        
        # Log the outcome of the request attempt
        self.log_request(service_name, can_request)
        
        return can_request
    
    def log_request(self, service_name, success):
        # Placeholder logging method, replace with actual logging implementation
        print(f"[{service_name}] Request {'succeeded' if success else 'denied'}. Current tokens: {self.services[service_name].get_current_tokens()}")
class DynamicRateLimiter:
    def __init__(self, low_limit, high_limit, limit_epoch, starting_tokens=None,epoch_cycle_adjustment:int=None):
        self.low_limit = low_limit
        self.high_limit = high_limit
        self.limit_epoch = limit_epoch  # in seconds
        self.request_status_json = {"succesful":[],"unsuccesful":[],"last_requested":get_time_stamp(),"first_requested":get_time_stamp(),"epoch_left":self.limit_epoch,"last_fail":get_time_stamp(),"count_since_fail":0}
        self.current_limit = starting_tokens or low_limit  # Default to high_limit if starting_tokens isn't provided
        self.epoch_cycle_adjustment = epoch_cycle_adjustment
        # Additional attributes for tracking adjustment logic
        self.last_adjusted_time = get_time_stamp()
        self.successful_epochs_since_last_adjustment = 0
        self.request_count_in_current_epoch = 0

    def _refill_tokens(self):
        time_since_last_request = get_time_stamp() - self.request_status_json["last_requested"]
        new_tokens = (time_since_last_request / self.limit_epoch) * self.current_limit
        self.tokens = min(self.current_limit, self.get_current_tokens())
    def request_tracker(self,success):
        if success:
            self.request_status_json["succesful"].append(get_time_stamp())
        else:
            self.request_status_json["unsuccesful"].append(get_time_stamp())
            self.request_status_json["last_fail"]=get_time_stamp()
            self.request_status_json["count_since_fail"]=0
            self.adjust_limit()
        self.request_status_json["last_requested"]=get_time_stamp()
    def calculate_tokens(self):
        successful = []
        for each in self.request_status_json["succesful"]:
            if (get_time_stamp() - each)<self.limit_epoch:
                successful.append(each)
        self.request_status_json["succesful"]=successful
        unsuccessful = []
        for each in self.request_status_json["unsuccesful"]:
            if (get_time_stamp() - each)<self.limit_epoch:
                unsuccessful.append(each)
        self.request_status_json["unsuccesful"]=unsuccessful
        if len(successful)==0 and len(unsuccessful)==0:
            pass
        elif len(successful)!=0 and len(unsuccessful)==0:
            self.request_status_json["first_requested"] = successful[0]
        elif len(successful)==0 and len(unsuccessful)!=0:
            self.request_status_json["first_requested"] = unsuccessful[0]
        else:
            self.request_status_json["first_requested"] = min(unsuccessful[0],successful[0])
        self.request_status_json["epoch_left"]=self.limit_epoch-(self.request_status_json["last_requested"]-self.request_status_json["first_requested"])
        
        return self.request_status_json
    def get_current_tokens(self):
        self.request_status_json = self.calculate_tokens()
        total_requests = len(self.request_status_json["succesful"])+len(self.request_status_json["unsuccesful"])
        return max(0,self.current_limit-total_requests)
    def get_sleep(self):
        self.request_status_json = self.calculate_tokens()
        self.request_status_json["current_sleep"]=self.request_status_json["epoch_left"]/max(1,self.get_current_tokens())
        return self.request_status_json
    def request(self):
        self._refill_tokens()
        if self.tokens > 0:
            return True  # The request can be made
        else:
            if self.tokens == 0:
                self.request_status_json["count_since_fail"]+=1
                if self.epoch_cycle_adjustment != None:
                    if self.request_status_json["count_since_fail"] >=self.epoch_cycle_adjustment:
                        self.current_limit=min(self.current_limit+1,self.high_limit)
            return False  # The request cannot be made
    def _adjust_limit(self):
        current_time = get_time_stamp()
        if current_time - self.last_adjusted_time >= self.limit_epoch:
            if len(self.clear_epoch()["succesful"]) >= self.tokens:
                # We hit the rate limit this epoch, decrease our limit
                self.tokens = max(1, self.tokens - 1)
            else:
                self.successful_epochs_since_last_adjustment += 1
                if self.successful_epochs_since_last_adjustment >= 5:
                    # We've had 5 successful epochs, increase our limit
                    self.current_limit = min(self.high_limit, self.tokens + 1)
                    self.successful_epochs_since_last_adjustment = 0
            
            # Reset our counters for the new epoch
            self.last_adjusted_time = current_time
            self.request_count_in_current_epoch = 0
    def adjust_limit(self):
        # Set the tokens to succesful requests_made - 1
        self.tokens = len(self.calculate_tokens()["succesful"])

        # Adjust the high_limit
        self.current_limit = self.tokens

        # Log the adjustment
        print(f"Adjusted tokens to: {self.tokens} and high_limit to: {self.current_limit}")
class DynamicRateLimiterManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(service_name="default", low_limit=10, high_limit=30, limit_epoch=60,starting_tokens=10,epoch_cycle_adjustment=True):
        if DynamicRateLimiterManagerSingleton._instance is None:
            DynamicRateLimiterManagerSingleton._instance = DynamicRateLimiterManager(service_name=service_name, low_limit=low_limit, high_limit=limit_epoch, limit_epoch=60,starting_tokens=starting_tokens,epoch_cycle_adjustment=epoch_cycle_adjustment)
        return DynamicRateLimiterManagerSingleton._instance


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
class SSLManager:
    def __init__(self, ciphers=None, ssl_options=None, certification=None):
        self.ciphers = ciphers or CipherManager().ciphers_string
        self.ssl_options = ssl_options or self.get_default_ssl_settings()
        self.certification = certification or ssl.CERT_REQUIRED
        self.ssl_context = self.get_context()
    def get_default_ssl_settings(self):
        return ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_COMPRESSION
    def get_context(self):
        return ssl_.create_urllib3_context(ciphers=self.ciphers, cert_reqs=self.certification, options=self.ssl_options)

class SSLManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(ciphers=None, ssl_options_list=None, certification=None):
        if SSLManagerSingleton._instance is None:
            SSLManagerSingleton._instance = SSLManager(ciphers=ciphers, ssl_options_list=ssl_options_list, certification=certification)
        elif SSLManagerSingleton._instance.cipher_manager.ciphers_string != ciphers or SSLManagerSingleton._instance.ssl_options_list !=ssl_options_list or SSLManagerSingleton._instance.certification !=certification:
            SSLManagerSingleton._instance = SSLManager(ciphers=ciphers, ssl_options_list=ssl_options_list, certification=certification)
        return SSLManagerSingleton._instance
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
class UserAgentManager:
    def __init__(self, os=None, browser=None, version=None,user_agent=None):
        self.os = os or 'Windows'
        self.browser = browser or "Firefox"
        self.version = version or '42.0'
        self.user_agent = user_agent or self.get_user_agent()
        self.header = self.user_agent_header()
    @staticmethod
    def user_agent_db():
        from .big_user_agent_list import big_user_agent_dict
        return big_user_agent_dict

    def get_user_agent(self):
        ua_db = self.user_agent_db()

        if self.os and self.os in ua_db:
            os_db = ua_db[self.os]
        else:
            os_db = random.choice(list(ua_db.values()))

        if self.browser and self.browser in os_db:
            browser_db = os_db[self.browser]
        else:
            browser_db = random.choice(list(os_db.values()))

        if self.version and self.version in browser_db:
            return browser_db[self.version]
        else:
            return random.choice(list(browser_db.values()))

    def user_agent_header(self):
        return {"user-agent": self.user_agent}
class UserAgentManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(user_agent=UserAgentManager().get_user_agent()[0]):
        if UserAgentManagerSingleton._instance is None:
            UserAgentManagerSingleton._instance = UserAgentManager(user_agent=user_agent)
        elif UserAgentManagerSingleton._instance.user_agent != user_agent:
            UserAgentManagerSingleton._instance = UserAgentManager(user_agent=user_agent)
        return UserAgentManagerSingleton._instance
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

class UrlManager:
    """
    UrlManager is a class for managing URLs, including cleaning, validating, and finding the correct version.

    Args:
        url (str or None): The URL to manage (default is None).
        session (requests.Session): A custom requests session (default is the requests module's session).

    Attributes:
        session (requests.Session): The requests session used for making HTTP requests.
        clean_urls (list): List of cleaned URL variations.
        url (str): The current URL.
        protocol (str): The protocol part of the URL (e.g., "https").
        domain (str): The domain part of the URL (e.g., "example.com").
        path (str): The path part of the URL (e.g., "/path/to/resource").
        query (str): The query part of the URL (e.g., "?param=value").
        all_urls (list): List of all URLs (not used in the provided code).

    Methods:
        url_to_pieces(url): Split a URL into its protocol, domain, path, and query components.
        clean_url(url): Return a list of potential URL versions with and without 'www' and 'http(s)'.
        get_correct_url(url): Get the correct version of the URL from possible variations.
        update_url(url): Update the URL and related attributes.
        get_domain(url): Get the domain name from a URL.
        url_join(url, path): Join a base URL with a path.
        is_valid_url(url): Check if a URL is valid.
        make_valid(href, url): Make a URL valid by joining it with a base URL.
        get_relative_href(url, href): Get the relative href URL by joining it with a base URL.

    Note:
        - The UrlManager class provides methods for managing URLs, including cleaning and validating them.
        - It also includes methods for joining and validating relative URLs.
    """

    def __init__(self, url=None, session=None):
        """
        Initialize a UrlManager instance.

        Args:
            url (str or None): The URL to manage (default is None).
            session (requests.Session): A custom requests session (default is the requests module's session).
        """
        self._url=url or 'www.example.com'
        self.url = url or 'www.example.com'
        self.session= session or requests
        self.clean_urls = self.clean_url(url=url)
        self.url = self.get_correct_url(clean_urls=self.clean_urls)
        url_pieces = self.url_to_pieces(url=self.url)
        self.protocol,self.domain,self.path,self.query=url_pieces
        self.all_urls = []
    def url_to_pieces(self, url):
        
        try:
            match = re.match(r'^(https?)?://?([^/]+)(/[^?]+)?(\?.+)?', url)
            if match:
                protocol = match.group(1) if match.group(1) else None
                domain = match.group(2) if match.group(1) else None
                path = match.group(3) if match.group(3) else ""  # Handle None
                query = match.group(4) if match.group(4) else ""  # Handle None
        except:
            print(f'the url {url} was not reachable')
            protocol,domain,path,query=None,None,"",""
        return protocol, domain, path, query

    def clean_url(self,url=None) -> list:
        """
        Given a URL, return a list with potential URL versions including with and without 'www.', 
        and with 'http://' and 'https://'.
        """
        if url == None:
            url=self.url
        urls=[]
        if url:
            # Remove http:// or https:// prefix
            cleaned = url.replace("http://", "").replace("https://", "")
            no_subdomain = cleaned.replace("www.", "", 1)
            
            urls = [
                f"https://{cleaned}",
                f"http://{cleaned}",
            ]

            # Add variants without 'www' if it was present
            if cleaned != no_subdomain:
                urls.extend([
                    f"https://{no_subdomain}",
                    f"http://{no_subdomain}",
                ])

            # Add variants with 'www' if it wasn't present
            else:
                urls.extend([
                    f"https://www.{cleaned}",
                    f"http://www.{cleaned}",
                ])

        return urls

    def get_correct_url(self,url=None,clean_urls=None) -> (str or None):
        """
        Gets the correct URL from the possible variations by trying each one with an HTTP request.

        Args:
            url (str): The URL to find the correct version of.
            session (type(requests.Session), optional): The requests session to use for making HTTP requests.
                Defaults to requests.

        Returns:
            str: The correct version of the URL if found, or None if none of the variations are valid.
        """
        if url==None and clean_urls != None:
            if self.url:
                url=self.url or clean_urls[0]
        if url!=None and clean_urls==None:
            clean_urls=self.clean_url(url)
        elif url==None and clean_urls==None:
            url=self.url
            clean_urls=self.clean_urls
        # Get the correct URL from the possible variations
        for url in clean_urls:
            try:
                source = self.session.get(url)
                return url
            except requests.exceptions.RequestException as e:
                print(e)
        return None
    def update_url(self,url):
        # These methods seem essential for setting up the UrlManager object.
        self.url = url
        self.clean_urls = self.clean_url()
        self.correct_url = self.get_correct_url()
        self.url =self.correct_url
        self.protocol,self.domain,self.path,self.query=self.url_to_pieces(url=self.url)
        self.all_urls = []
    def get_domain(self,url):
        return urlparse(url).netloc
    def url_join(self,url,path):
        url = eatOuter(url,['/'])
        path = eatInner(path,['/'])
        slash=''
        if path[0] not in ['?','&']:
            slash = '/'
        url = url+slash+path
        return url
    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, new_url):
        self._url = new_url
    @staticmethod
    def is_valid_url(url):
        """
        Check if the given URL is valid.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    @staticmethod
    def make_valid(href,url):
        def is_valid_url(url):
            """
            Check if the given URL is valid.
            """
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        if is_valid_url(href):
            return href
        new_link=urljoin(url,href)
        if is_valid_url(new_link):
            return new_link
        return False
    @staticmethod
    def get_relative_href(url,href):
        # join the URL if it's relative (not an absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        return href
    def url_basename(url):
        path = urllib.parse.urlparse(url).path
        return path.strip('/').split('/')[-1]


    def base_url(url):
        return re.match(r'https?://[^?#]+/', url).group()


    def urljoin(base, path):
        if isinstance(path, bytes):
            path = path.decode()
        if not isinstance(path, str) or not path:
            return None
        if re.match(r'^(?:[a-zA-Z][a-zA-Z0-9+-.]*:)?//', path):
            return path
        if isinstance(base, bytes):
            base = base.decode()
        if not isinstance(base, str) or not re.match(
                r'^(?:https?:)?//', base):
            return None
        return urllib.parse.urljoin(base, path)
class UrlManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(url=None,session=requests):
        if UrlManagerSingleton._instance is None:
            UrlManagerSingleton._instance = UrlManager(url,session=session)
        elif UrlManagerSingleton._instance.session != session or UrlManagerSingleton._instance.url != url:
            UrlManagerSingleton._instance = UrlManager(url,session=session)
        return UrlManagerSingleton._instance
class SafeRequest:
    """
    SafeRequest is a class for making HTTP requests with error handling and retries.

    Args:
        url (str or None): The URL to make requests to (default is None).
        url_manager (UrlManager or None): An instance of UrlManager (default is None).
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
        update_url_manager(url_manager): Update the URL manager and reinitialize the SafeRequest.
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
    def __init__(self,
                 url=None,
                 source_code=None,
                 url_manager=None,
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
                 email = None,
                 password=None,
                 checkbox=None,
                 dropdown=None,
                 certification=None,
                 stream=False,
                 timeout = None,
                 last_request_time=None,
                 max_retries=None,
                 request_wait_limit=None):
        self._url=url
        self.url=url
        if url_manager == None:
            url_manager = UrlManager(url=self.url)
        self.url_manager=url_manager
        self._url_manager = self.url_manager
        self.user_agent = user_agent
        self.user_agent_manager = user_agent_manager or UserAgentManager(user_agent=self.user_agent)
        self.headers= headers or self.user_agent_manager.header or {'Accept': '*/*'}
        self.user_agent= self.user_agent_manager.user_agent
        self.ciphers=ciphers or CipherManager().ciphers_string
        self.certification=certification
        self.ssl_options=ssl_options
        self.ssl_manager = ssl_manager or SSLManager(ciphers=self.ciphers, ssl_options=self.ssl_options, certification=self.certification)
        self.tls_adapter=tls_adapter or  TLSAdapter(ssl_manager=self.ssl_manager,certification=self.certification,ssl_options=self.ssl_manager.ssl_options)
        self.network_manager= network_manager or NetworkManager(user_agent_manager=self.user_agent_manager,ssl_manager=self.ssl_manager, tls_adapter=self.tls_adapter,user_agent=user_agent,proxies=proxies,cookies=cookies,ciphers=ciphers, certification=certification, ssl_options=ssl_options)
        self.stream=stream
        self.tls_adapter=self.network_manager.tls_adapter
        self.ciphers=self.network_manager.ciphers
        self.certification=self.network_manager.certification
        self.ssl_options=self.network_manager.ssl_options
        self.proxies=self.network_manager.proxies
        self.timeout=timeout
        self.cookies=self.network_manager.cookies
        self.session = session or requests.session()
        self.auth = auth
        self.spec_login=spec_login
        self.password=password
        self.email = email
        self.checkbox=checkbox
        self.dropdown=dropdown
        self.login_url=login_url
        self.login_user_agent=login_user_agent
        self.login_referer=login_referer
        self.protocol=protocol or 'https://'
        
        self.stream=stream if isinstance(stream,bool) else False
        self.initialize_session()
        self.last_request_time=last_request_time
        self.max_retries = max_retries or 3
        self.request_wait_limit = request_wait_limit or 1.5
        self._response=None
        self.make_request()
        self.source_code = None
        self.source_code_bytes=None
        self.source_code_json = {}
        self.react_source_code=[]
        self._response_data = None
        self.process_response_data()
    def update_url_manager(self,url_manager):
        self.url_manager=url_manager
        self.re_initialize()
    def update_url(self,url):
        self.url_manager.update_url(url=url)
        self.re_initialize()
    def re_initialize(self):
        self._response=None
        self.make_request()
        self.source_code = None
        self.source_code_bytes=None
        self.source_code_json = {}
        self.react_source_code=[]
        self._response_data = None
        self.process_response_data()
    @property
    def response(self):
        """Lazy-loading of response."""
        if self._response is None:
            self._response = self.fetch_response()
        return self._response
    def authenticate(self,session, login_url=None, email=None, password=None,checkbox=None,dropdown=None):
        login_urls = login_url or [self.url_manager.url,self.url_manager.domain,self.url_manager.url_join(url=self.url_manager.domain,path='login'),self.url_manager.url_join(url=self.url_manager.domain,path='auth')]
        s = session
        if not isinstance(login_urls,list):
            login_urls=[login_urls]
        for login_url in login_urls:
            login_url_manager = UrlManager(login_url)
            login_url = login_url_manager.url
            
            r = s.get(login_url)
            soup = BeautifulSoup(r.content, "html.parser")
            # Find the token or any CSRF protection token
            token = soup.find('input', {'name': 'token'}).get('value') if soup.find('input', {'name': 'token'}) else None
            if token != None:
                break
        login_data = {}
        if email != None:
            login_data['email']=email
        if password != None:
            login_data['password'] = password
        if checkbox != None:
            login_data['checkbox'] = checkbox
        if dropdown != None:
            login_data['dropdown']=dropdown
        if token != None:
            login_data['token'] = token
        s.post(login_url, data=login_data)
        return s

    def fetch_response(self) -> Union[requests.Response, None]:
        """Actually fetches the response from the server."""
        # You can further adapt this method to use retries or other logic you had
        # in your original code, but the main goal here is to fetch and return the response
        return self.try_request()
    def spec_auth(self, session=None, email=None, password=None, login_url=None, login_referer=None, login_user_agent=None):
        s = session or requests.session()
        
        domain = self.url_manager.url_join(self.url_manager.get_correct_url(self.url_manager.domain),'login') if login_url is None else login_url
        login_url = self.url_manager.get_correct_url(url=domain)
        
        login_referer = login_referer or self.url_manager.url_join(url=login_url, path='?role=fast&to=&s=1&m=1&email=YOUR_EMAIL')
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
            s= self.auth
        elif self.spec_login:
            s=self.spec_auth(session=s,email=self.email, password=self.password, login_url=self.login_url, login_referer=self.login_referer, login_user_agent=self.login_user_agent)
        elif any([self.password, self.email, self.login_url, self.checkbox, self.dropdown]):
            s=self.authenticate(session=s, login_url=self.login_url, email=self.email, password=self.password, checkbox=self.checkbox, dropdown=self.dropdown)
        s.proxies = self.proxies
        s.cookies["cf_clearance"] = self.network_manager.cookies
        s.headers.update(self.headers)
        s.mount(self.protocol, self.network_manager.tls_adapter)
        return s
    def process_response_data(self):
        """Processes the fetched response data."""
        if not self.response:
            return  # No data to process
        
        self.source_code = self.response.text
        self.source_code_bytes = self.response.content
        
        if self.response.headers.get('content-type') == 'application/json':
            data = convert_to_json(self.source_code)
            if data:
                self.source_code_json = data.get("response", data)
        
        self.get_react_source_code()
    def get_react_source_code(self) -> list:
        """
        Fetches the source code of the specified URL and extracts JavaScript and JSX source code (React components).

        Args:
            url (str): The URL to fetch the source code from.

        Returns:
            list: A list of strings containing JavaScript and JSX source code found in <script> tags.
        """
        if self.url_manager.url is None:
            return []
        soup = BeautifulSoup(self.source_code_bytes,"html.parser")
        script_tags = soup.find_all('script', type=lambda t: t and ('javascript' in t or 'jsx' in t))
        for script_tag in script_tags:
            self.react_source_code.append(script_tag.string)


    def get_status(url:str=None) -> int:
        """
        Gets the HTTP status code of the given URL.

        Args:
            url (str): The URL to check the status of.

        Returns:
            int: The HTTP status code of the URL, or None if the request fails.
        """
        # Get the status code of the URL
        return try_request(url=url).status_code
    def wait_between_requests(self):
        """
        Wait between requests based on the request_wait_limit.
        """
        if self.last_request_time:
            sleep_time = self.request_wait_limit - (get_time_stamp() - self.last_request_time)
            if sleep_time > 0:
                logging.info(f"Sleeping for {sleep_time:.2f} seconds.")
                get_sleep(sleep_time)

    def make_request(self):
        """
        Make a request and handle potential errors.
        """
        # Update the instance attributes if they are passed

        self.wait_between_requests()
        for _ in range(self.max_retries):
            try:
                self.try_request()  # 10 seconds timeout
                if self.response:
                    if self.response.status_code == 200:
                        self.last_request_time = get_time_stamp()
                        return self.response
                    elif self.response.status_code == 429:
                        logging.warning(f"Rate limited by {self.url_manager.url}. Retrying...")
                        get_sleep(5)  # adjust this based on the server's rate limit reset time
            except requests.Timeout as e:
                logging.error(f"Request to {cleaned_url} timed out: {e}")
            except requests.ConnectionError:
                logging.error(f"Connection error for URL {self.url_manager.url}.")
            except requests.Timeout:
                logging.error(f"Request timeout for URL {self.url_manager.url}.")
            except requests.RequestException as e:
                logging.error(f"Request exception for URL {self.url_manager.url}: {e}")

        logging.error(f"Failed to retrieve content from {self.url_manager.url} after {self.max_retries} retries.")
        return None
    def try_request(self) -> Union[requests.Response, None]:
        """
        Tries to make an HTTP request to the given URL using the provided session.

        Args:
            timeout (int): Timeout for the request.

        Returns:
            requests.Response or None: The response object if the request is successful, or None if the request fails.
        """
        try:
            return self.session.get(url=self.url_manager.url, timeout=self.timeout,stream=self.stream)
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def get_limited_request(self,request_url,service_name="default"):
        manager = DynamicRateLimiterManagerSingleton.get_instance()  # Get the singleton instance
        unwanted_response=True
        # Check with the rate limiter if we can make a request
        while True:
            if not manager.request(service_name):
                print("Rate limit reached for coin_gecko. Waiting for the next epoch...")
                sleep_count_down(manager.services[service_name].get_sleep()["current_sleep"])  # Wait for the limit_epoch duration
            # Make the actual request
            response = try_request(request_url=request_url)
            
            # If you get a rate-limit error (usually 429 status code but can vary), adjust the rate limiter
            if response.status_code ==429:
                print(response.json())
                manager.services[service_name].request_tracker(False)
                print("Rate limited by coin_gecko. Adjusted limit. Retrying...")
                if len(manager.services[service_name].calculate_tokens()["succesful"])<2:
                    sleep_count_down(manager.services[service_name].limit_epoch)  # Wait for the limit_epoch duration
                else:
                    manager.services[service_name].current_limit-=1
                    sleep_count_down(manager.services[service_name].limit_epoch/len(manager.services[service_name].calculate_tokens()["succesful"]))  # Wait for the limit_epoch duration
            # Return the data if the request was successful
            if response.status_code == 200:
                manager.services[service_name].request_tracker(True)
                return response.json()
            elif response.status_code not in [200,429]:
                print(f"Unexpected response: {response.status_code}. Message: {response.text}")
                return None
    @property
    def url(self):
        return self.url_manager.url

    @url.setter
    def url(self, new_url):
        self._url = new_url
class SafeRequestSingleton:
    _instance = None
    @staticmethod
    def get_instance(url=None,headers:dict=None,max_retries=3,last_request_time=None,request_wait_limit=1.5):
        if SafeRequestSingleton._instance is None:
            SafeRequestSingleton._instance = SafeRequest(url,url_manager=UrlManagerSingleton,headers=headers,max_retries=max_retries,last_request_time=last_request_time,request_wait_limit=request_wait_limit)
        elif SafeRequestSingleton._instance.url != url or SafeRequestSingleton._instance.headers != headers or SafeRequestSingleton._instance.max_retries != max_retries or SafeRequestSingleton._instance.request_wait_limit != request_wait_limit:
            SafeRequestSingleton._instance = SafeRequest(url,url_manager=UrlManagerSingleton,headers=headers,max_retries=max_retries,last_request_time=last_request_time,request_wait_limit=request_wait_limit)
        return SafeRequestSingleton._instance
class SoupManager:
    """
    SoupManager is a class for managing and parsing HTML source code using BeautifulSoup.

    Args:
        url (str or None): The URL to be parsed (default is None).
        source_code (str or None): The HTML source code (default is None).
        url_manager (UrlManager or None): An instance of UrlManager (default is None).
        request_manager (SafeRequest or None): An instance of SafeRequest (default is None).
        parse_type (str): The type of parser to be used by BeautifulSoup (default is "html.parser").

    Methods:
        re_initialize(): Reinitialize the SoupManager with the current settings.
        update_url(url): Update the URL and reinitialize the SoupManager.
        update_source_code(source_code): Update the source code and reinitialize the SoupManager.
        update_request_manager(request_manager): Update the request manager and reinitialize the SoupManager.
        update_url_manager(url_manager): Update the URL manager and reinitialize the SoupManager.
        update_parse_type(parse_type): Update the parsing type and reinitialize the SoupManager.
        all_links: A property that provides access to all discovered links.
        _all_links_get(): A method to load all discovered links.
        get_all_website_links(tag="a", attr="href"): Get all URLs belonging to the same website.
        meta_tags: A property that provides access to all discovered meta tags.
        _meta_tags_get(): A method to load all discovered meta tags.
        get_meta_tags(): Get all meta tags in the source code.
        find_all(element, soup=None): Find all instances of an HTML element in the source code.
        get_class(class_name, soup=None): Get the specified class from the HTML source code.
        has_attributes(tag, *attrs): Check if an HTML tag has the specified attributes.
        get_find_all_with_attributes(*attrs): Find all HTML tags with specified attributes.
        get_all_desired_soup(tag=None, attr=None, attr_value=None): Get HTML tags based on specified criteria.
        extract_elements(url, tag=None, class_name=None, class_value=None): Extract portions of source code based on filters.
        find_all_with_attributes(class_name=None, *attrs): Find classes with associated href or src attributes.
        get_images(tag_name, class_name, class_value): Get images with specific class and attribute values.
        discover_classes_and_meta_images(tag_name, class_name_1, class_name_2, class_value, attrs): Discover classes and meta images.

    Note:
        - The SoupManager class is designed for parsing HTML source code using BeautifulSoup.
        - It provides various methods to extract data and discover elements within the source code.
    """
    def __init__(self,url=None,source_code=None,url_manager=None,request_manager=None, parse_type="html.parser"):
        self.soup=[]
        self.url=url
        if url_manager == None:
            url_manager=UrlManager(url=self.url)
        if self.url != None and url_manager != None and url_manager.url != UrlManager(url=url).url:
            url_manager.update_url(url=self.url)
        self.url_manager= url_manager
        self.url=self.url_manager.url
        if request_manager == None:
            request_manager = SafeRequest(url_manager=self.url_manager)
        self.request_manager = request_manager
        if self.request_manager.url_manager != self.url_manager:
           self.request_manager.update_url_manager(url_manager=self.url_manager)
        self.parse_type = parse_type
        if source_code != None:
            self.source_code = source_code
        else:
            self.source_code = self.request_manager.source_code_bytes
        self.soup= BeautifulSoup(self.source_code, self.parse_type)
        self._all_links_data = None
        self._meta_tags_data = None
    def re_initialize(self):
        self.soup= BeautifulSoup(self.source_code, self.parse_type)
        self._all_links_data = None
        self._meta_tags_data = None
    def update_url(self,url):
        self.url_manager.update_url(url=url)
        self.url=self.url_manager.url
        self.request_manager.update_url(url=url)
        self.source_code = self.request_manager.source_code_bytes
        self.re_initialize()
    def update_source_code(self,source_code):
        self.source_code = source_code
        self.re_initialize()
    def update_request_manager(self,request_manager):
        self.request_manager = request_manager
        self.url_manager=self.request_manager.url_manager
        self.url=self.url_manager.url
        self.source_code = self.request_manager.source_code_bytes
        self.re_initialize()
    def update_url_manager(self,url_manager):
        self.url_manager=url_manager
        self.url=self.url_manager.url
        self.request_manager.update_url_manager(url_manager=self.url_manager)
        self.source_code = self.request_manager.source_code_bytes
        self.re_initialize()
    def update_parse_type(self,parse_type):
        self.parse_type=parse_type
        self.re_initialize()
    @property
    def all_links(self):
        """This is a property that provides access to the _all_links_data attribute.
        The first time it's accessed, it will load the data."""
        if self._all_links_data is None:
            print("Loading all links for the first time...")
            self._all_links_data = self._all_links_get()
        return self._all_links_data
    def _all_links_get(self):
        """A method that loads the data (can be replaced with whatever data loading logic you have)."""
        return self.get_all_website_links()
    def get_all_website_links(self,tag="a",attr="href") -> list:
        """
        Returns all URLs that are found on the specified URL and belong to the same website.

        Args:
            url (str): The URL to search for links.

        Returns:
            list: A list of URLs that belong to the same website as the specified URL.
        """
        all_urls=[self.url_manager.url]
        domain = self.url_manager.domain
        all_desired=self.get_all_desired_soup(tag=tag,attr=attr)
        for tag in all_desired:
            href = tag.attrs.get(attr)
            if href == "" or href is None:
                # href empty tag
                continue
            href=self.url_manager.get_relative_href(self.url_manager.url,href)
            if not self.url_manager.is_valid_url(href):
                # not a valid URL
                continue
            if href in all_urls:
                # already in the set
                continue
            if domain not in href:
                # external link
                continue
            all_urls.append(href)
                
        return all_urls


    @property
    def meta_tags(self):
        """This is a property that provides access to the _all_links_data attribute.
        The first time it's accessed, it will load the data."""
        if self._meta_tags_data is None:
            print("Loading all links for the first time...")
            self._meta_tags_data = self._all_links_get()
        return self._meta_tags_data
    def _meta_tags_get(self):
        """A method that loads the data (can be replaced with whatever data loading logic you have)."""
        return self.get_meta_tags()
    def get_meta_tags(self):
        tags = self.find_all("meta")
        for meta_tag in tags:
            for attr, values in meta_tag.attrs.items():
                if attr not in self.meta_tags:
                    self.meta_tags[attr] = []
                if values not in self.meta_tags[attr]:
                    self.meta_tags[attr].append(values)

                    
    def find_all(self,element,soup=None):
        soup = self.soup if soup == None else soup
        return soup.find_all(element)
    def get_class(self,class_name,soup=None):
        soup = self.soup if soup == None else soup
        return soup.get(class_name)
    @staticmethod
    def has_attributes(tag, *attrs):
        return any(tag.has_attr(attr) for attr in attrs)
    def get_find_all_with_attributes(self, *attrs):
        return self.soup.find_all(lambda t: self.has_attributes(t, *attrs))
    def find_tags_by_attributes(self, tag: str = None, attr: str = None, attr_values: List[str] = None) ->List:
        if not tag:
            tags = self.soup.find_all(True)  # get all tags
        else:
            tags = self.soup.find_all(tag)  # get specific tags
            
        extracted_tags = []
        for t in tags:
            if attr:
                attribute_value = t.get(attr)
                if not attribute_value:  # skip tags without the desired attribute
                    continue
                if attr_values and not any(value in attribute_value for value in attr_values):  # skip tags without any of the desired attribute values
                    continue
            extracted_tags.append(t)
        return extracted_tags


    def extract_elements(self,url:str=None, tag:str=None, class_name:str=None, class_value:str=None) -> list:
        """
        Extracts portions of the source code from the specified URL based on provided filters.

        Args:
            url (str): The URL to fetch the source code from.
            element_type (str, optional): The HTML element type to filter by. Defaults to None.
            attribute_name (str, optional): The attribute name to filter by. Defaults to None.
            class_name (str, optional): The class name to filter by. Defaults to None.

        Returns:
            list: A list of strings containing portions of the source code that match the provided filters.
        """
        elements = []
        # If no filters are provided, return the entire source code
        if not tag and not class_name and not class_value:
            elements.append(str(self.soup))
            return elements
        # Find elements based on the filters provided
        if tag:
            elements.extend([str(tags) for tags in self.get_all_desired(tag)])
        if class_name:
            elements.extend([str(tags) for tags in self.get_all_desired(tag={class_name: True})])
        if class_value:
            elements.extend([str(tags) for tags in self.get_all_desired(class_name=class_name)])
        return elements
    def find_all_with_attributes(self, class_name=None, *attrs):
        """
        Discovers classes in the HTML content of the provided URL 
        that have associated href or src attributes.

        Args:
            base_url (str): The URL from which to discover classes.

        Returns:
            set: A set of unique class names.
        """

    
        unique_classes = set()
        for tag in self.get_find_all_with_attributes(*attrs):
            class_list = self.get_class(class_name=class_name, soup=tag)
            unique_classes.update(class_list)
        return unique_classes
    def get_images(self, tag_name, class_name, class_value):
        images = []
        for tag in self.soup.find_all(tag_name):
            if class_name in tag.attrs and tag.attrs[class_name] == class_value:
                content = tag.attrs.get('content', '')
                if content:
                    images.append(content)
        return images
    def extract_text_sections(self) -> list:
        """
        Extract all sections of text from an HTML content using BeautifulSoup.

        Args:
            html_content (str): The HTML content to be parsed.

        Returns:
            list: A list containing all sections of text.
        """
        # Remove any script or style elements to avoid extracting JavaScript or CSS code
        for script in self.soup(['script', 'style']):
            script.decompose()

        # Extract text from the remaining elements
        text_sections = self.soup.stripped_strings
        return [text for text in text_sections if text]
    def discover_classes_and_meta_images(self, tag_name, class_name_1, class_name_2, class_value, attrs):
        """
        Discovers classes in the HTML content of the provided URL 
        that have associated href or src attributes. Also, fetches 
        image references from meta tags.

        Args:
            base_url (str): The URL from which to discover classes and meta images.

        Returns:
            tuple: A set of unique class names and a list of meta images.
        """
    
        unique_classes = self.find_all_with_attributes(class_name=class_name_1, *attrs)
        images = self.get_images(tag_name=tag_name, class_name=class_name_2, class_value=class_value)
        return unique_classes, images
    def get_all_tags_and_attribute_names(self):
        tag_names = set()  # Using a set to ensure uniqueness
        attribute_names = set()
        get_all = self.find_tags_by_attributes()
        for tag in get_all:  # True matches all tags
            tag_names.add(tag.name)
            for attr in tag.attrs:
                attribute_names.add(attr)
        tag_names_list = list(tag_names)
        attribute_names_list = list(attribute_names)
        return {"tags":tag_names_list,"attributes":attribute_names_list}

    def get_all_attribute_values(self):
        attribute_values={}
        get_all = self.find_tags_by_attributes()
        for tag in get_all:  # True matches all tags
            for attr, value in tag.attrs.items():
                # If attribute is not yet in the dictionary, add it with an empty set
                if attr not in attribute_values:
                    attribute_values[attr] = set()
                # If the attribute value is a list (e.g., class), extend the set with the list
                if isinstance(value, list):
                    attribute_values[attr].update(value)
                else:
                    attribute_values[attr].add(value)
        for attr, values in attribute_values.items():
            attribute_values[attr] = list(values)
        return attribute_values
    
    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, new_url):
        self._url = new_url

class SoupManagerSingleton():
    _instance = None
    @staticmethod
    def get_instance(url_manager,request_manager,parse_type="html.parser",source_code=None):
        if SoupManagerSingleton._instance is None:
            SoupManagerSingleton._instance = SoupManager(url_manager,request_manager,parse_type=parse_type,source_code=source_code)
        elif parse_type != SoupManagerSingleton._instance.parse_type  or source_code != SoupManagerSingleton._instance.source_code:
            SoupManagerSingleton._instance = SoupManager(url_manager,request_manager,parse_type=parse_type,source_code=source_code)
        return SoupManagerSingleton._instance
class VideoDownloader:
    """
    VideoDownloader is a class for downloading videos from URLs using YouTube-DL.

    Args:
        link (str or list): The URL(s) of the video(s) to be downloaded.
        temp_directory (str or None): The directory to store temporary video files (default is None, uses video_directory/temp_files).
        video_directory (str or None): The directory to store downloaded videos (default is None, uses 'videos' in the current working directory).
        remove_existing (bool): Whether to remove existing video files with the same name (default is True).

    Methods:
        count_outliers(speed, threshold): Count speed outliers below the threshold.
        filter_outliers(speeds): Filter out speed outliers in the list of speeds.
        remove_temps(file_name): Remove temporary video files based on the file name.
        move_video(): Move the downloaded video to the final directory.
        yt_dlp_downloader(url, ydl_opts={}, download=True): Download video information using YouTube-DL.
        progress_callback(d): Callback function to monitor download progress.
        download(): Download video(s) based on the provided URL(s).
        monitor(): Monitor the download progress.
        start(): Start the download and monitoring threads.

    Note:
        - The VideoDownloader class uses YouTube-DL to download videos.
        - It allows downloading from multiple URLs.
        - You need to have YouTube-DL installed to use this class.
    """
    def __init__(self, link,temp_directory=None,video_directory=None,remove_existing=True):
        if video_directory==None:
            video_directory=os.path.join(os.getcwd(),'videos')
        if temp_directory == None:
            temp_directory=os.path.join(video_directory,'temp_files')
        self.thread_manager = ThreadManager()
        self.pause_event = self.thread_manager.add_thread('pause_event')
        self.link = link
        self.temp_directory = temp_directory
        self.video_directory = video_directory
        self.remove_existing=remove_existing
        self.video_urls=self.link if isinstance(self.link,list) else [self.link]
        self.starttime = None
        self.downloaded = 0
        self.time_interval=60
        self.monitoring=True
        self.temp_file_name = None
        self.file_name = None
        self.dl_speed = None
        self.dl_eta=None
        self.total_bytes_est=None
        self.percent_speed=None
        self.percent=None
        self.speed_track = []
        self.video_url=None
        self.last_checked = get_time_stamp()
        self.num=0
        self.start()
    def count_outliers(self,speed,threshold):
        if speed < threshold:
            self.outlier_count+=1
        else:
            self.outlier_count=0
    def filter_outliers(self,speeds):
        # Step 1: Compute initial average
        initial_avg = sum(speeds) / len(speeds)
        
        # Step 2: Remove speeds 25% under the average
        threshold = initial_avg * 0.75  # 25% under average
        filtered_speeds = [speed for speed in speeds if speed >= threshold]
        
        # Step 3: Compute the new average of the filtered list
        if filtered_speeds:  # Ensure the list is not empty
            self.count_outliers(speeds[-1],threshold)
            return filtered_speeds
        else:
            # This can happen if all values are outliers, it's up to you how to handle it
            self.outlier_count=0
            return speeds
    def remove_temps(self,file_name):
        for temp_vid in os.listdir(self.temp_directory):
            if len(file_name)<=len(temp_vid):
                if temp_vid[:len(file_name)] == file_name:
                    os.remove(os.path.join(self.temp_directory,temp_vid))
                    print(f"removing {temp_vid} from {self.temp_directory}")
    def move_video(self):
        if os.path.exists(self.temp_file_path):
            shutil.move(self.temp_file_path, self.video_directory)
            print(f"moving {self.file_name} from {self.temp_directory} to {self.video_directory}")
            self.remove_temps(self.file_name)
            return True
        if os.path.exists(self.complete_file_path):
            print(f"{self.file_name} already existed in {self.video_directory}; removing it from {self.temp_directory}")
            self.remove_temps(self.file_name)
            return True
        return False
    def yt_dlp_downloader(self,url,ydl_opts={},download=True):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.info_dict=ydl.extract_info(url=url, download=download)
            return True
        except:
            return False
    def progress_callback(self, d):
        self.status_dict = d
        keys = ['status',
                'downloaded_bytes',
                'fragment_index',
                'fragment_count',
                'filename',
                'tmpfilename',
                'max_progress',
                'progress_idx',
                'elapsed',
                'total_bytes_estimate',
                'speed',
                'eta',
                '_eta_str',
                '_speed_str',
                '_percent_str',
                '_total_bytes_str',
                '_total_bytes_estimate_str',
                '_downloaded_bytes_str',
                '_elapsed_str',
                '_default_template']
        if self.status_dict['status'] == 'finished':
            print("Done downloading, moving video to final directory...")
            self.move_video()
            return
        if get_time_stamp()-self.last_checked>5:
            print(self.status_dict['_default_template'])
            self.last_checked = get_time_stamp()
            if (get_time_stamp()-self.start_time/5)>6:
                self.speed_track.append(self.status_dict['speed'])
                self.speed_track=self.filter_outliers(self.speed_track)
                
    def download(self):
        if not os.path.exists(self.video_directory):
            os.makedirs(self.video_directory,exist_ok=True)
        if not os.path.exists(self.temp_directory):
            os.makedirs(self.temp_directory,exist_ok=True)
        for self.num,video_url in enumerate(self.video_urls):
            if video_url != self.video_url or self.video_url == None:
                self.video_url=video_url
                self.info_dict=None
                result = self.yt_dlp_downloader(url=self.video_url,ydl_opts={'quiet': True, 'no_warnings': True},download=False)
                if self.info_dict != None and result:
                    self.start_time = get_time_stamp()
                    self.downloaded = 0
                    self.video_title = self.info_dict.get('title', None)
                    self.video_ext = self.info_dict.get('ext', 'mp4')
                    self.file_name =f"{self.video_title}.{self.video_ext}"
                    self.temp_file_path = os.path.join(self.temp_directory, self.file_name)
                    self.complete_file_path = os.path.join(self.video_directory, self.file_name)
                    if not self.move_video():
                        self.dl_speed = []
                        self.percent=None
                        self.dl_eta=None
                        self.total_bytes_est=None
                        self.percent_speed=None
                        self.speed_track = []
                        self.outlier_count=0
                        ydl_opts = {
                            'outtmpl': self.temp_file_path,
                            'noprogress':True,
                            'progress_hooks': [self.progress_callback]  
                        }
                        
                       
                        print("Starting download...")  # Check if this point in code is reached
                        result = self.yt_dlp_downloader(url=self.video_url,ydl_opts=ydl_opts,download=True)
                        if result:
                            print("Download finished!")  # Check if download completes
                        else:
                            print(f'error downloding {self.video_url}')
                        self.move_video()
                    else:
                        print(f"The video from {self.video_url} already exists in the directory {self.video_directory}. Skipping download.")
                else:
                    print(f"could not find video info from {self.video_url} Skipping download.")
        if self.num==len(self.video_urls)-1:
            self.monitoring=False
            self.time_interval=0
            
    def monitor(self):
        while self.monitoring:
            self.thread_manager.wait(name='pause_event',n=self.time_interval)# check every minute
            if self.monitoring:
                if 'eta' in self.status_dict:
                    if self.outlier_count>=3 and (self.status_dict['eta']/60)>10:
                        self.start()

    def start(self):
        download_thread = self.thread_manager.add_thread(name='download_thread',target=self.download)
        monitor_thread = self.thread_manager.add_thread(name='monitor_thread',target_function=self.monitor)
        self.thread_manager.start(name='download_thread')
        self.thread_manager.start(name='monitor_thread')
        self.thread_manager.join(name='download_thread')
        self.thread_manager.join(name='monitor_thread')
class VideoDownloaderSingleton():
    _instance = None
    @staticmethod
    def get_instance(url_manager,request_manager,title=None,video_extention='mp4',download_directory=os.getcwd(),user_agent=None,download=True,get_info=False):
        if VideoDownloaderSingleton._instance is None:
            VideoDownloaderSingleton._instance = VideoDownloader(url=url,title=title,video_extention=video_extention,download_directory=download_directory,download=download,get_info=get_info,user_agent=user_agent)
        elif VideoDownloaderSingleton._instance.title != title or video_extention != VideoDownloaderSingleton._instance.video_extention or url != VideoDownloaderSingleton._instance.url or download_directory != VideoDownloaderSingleton._instance.download_directory or user_agent != VideoDownloaderSingleton._instance.user_agent:
            VideoDownloaderSingleton._instance = VideoDownloader(url=url,title=title,video_extention=video_extention,download_directory=download_directory,download=download,get_info=get_info,user_agent=user_agent)
        return VideoDownloaderSingleton._instance

class LinkManager:
    """
    LinkManager is a class for managing and extracting links and image links from a web page.

    Args:
        url (str): The URL of the web page (default is "https://example.com").
        source_code (str or None): The source code of the web page (default is None).
        url_manager (UrlManager or None): An instance of UrlManager (default is None).
        request_manager (SafeRequest or None): An instance of SafeRequest (default is None).
        soup_manager (SoupManager or None): An instance of SoupManager (default is None).
        image_link_tags (str): HTML tags to identify image links (default is 'img').
        img_link_attrs (str): HTML attributes to identify image link URLs (default is 'src').
        link_tags (str): HTML tags to identify links (default is 'a').
        link_attrs (str): HTML attributes to identify link URLs (default is 'href').
        strict_order_tags (bool): Flag to indicate if tags and attributes should be matched strictly (default is False).
        img_attr_value_desired (list or None): Desired attribute values for image links (default is None).
        img_attr_value_undesired (list or None): Undesired attribute values for image links (default is None).
        link_attr_value_desired (list or None): Desired attribute values for links (default is None).
        link_attr_value_undesired (list or None): Undesired attribute values for links (default is None).
        associated_data_attr (list): HTML attributes to associate with the extracted links (default is ["data-title", 'alt', 'title']).
        get_img (list): HTML attributes used to identify associated images (default is ["data-title", 'alt', 'title']).

    Methods:
        re_initialize(): Reinitialize the LinkManager with the current settings.
        update_url_manager(url_manager): Update the URL manager with a new instance.
        update_url(url): Update the URL and reinitialize the LinkManager.
        update_source_code(source_code): Update the source code and reinitialize the LinkManager.
        update_soup_manager(soup_manager): Update the SoupManager and reinitialize the LinkManager.
        update_desired(...): Update the desired settings and reinitialize the LinkManager.
        find_all_desired(...): Find all desired links or image links based on the specified criteria.
        find_all_domain(): Find all unique domain names in the extracted links.

    Note:
        - The LinkManager class helps manage and extract links and image links from web pages.
        - The class provides flexibility in specifying criteria for link extraction.
    """
    def __init__(self,url="https://example.com",source_code=None,url_manager=None,request_manager=None,soup_manager=None,image_link_tags='img',img_link_attrs='src',link_tags='a',link_attrs='href',strict_order_tags=False,img_attr_value_desired=None,img_attr_value_undesired=None,link_attr_value_desired=None,link_attr_value_undesired=None,associated_data_attr=["data-title",'alt','title'],get_img=["data-title",'alt','title']):
        if url_manager==None:
            url_manager=UrlManager(url=url)
        self.url_manager= url_manager
        self.url=self.url_manager.url
        if request_manager==None:
            request_manager = SafeRequest(url_manager=self.url_manager)
        self.request_manager=request_manager
        if soup_manager == None:
            soup_manager = SoupManager(url_manager=self.url_manager,request_manager=self.request_manager)
        self.soup_manager = soup_manager
        if source_code != None:
            self.source_code=source_code
        else:
            self.source_code=self.request_manager.source_code_bytes
        if self.source_code != self.soup_manager.source_code:
            self.soup_manager.update_source_code(source_code=self.source_code)
        self.strict_order_tags=strict_order_tags
        self.image_link_tags=image_link_tags
        self.img_link_attrs=img_link_attrs
        self.link_tags=link_tags
        self.link_attrs=link_attrs
        self.img_attr_value_desired=img_attr_value_desired
        self.img_attr_value_undesired=img_attr_value_undesired
        self.link_attr_value_desired=link_attr_value_desired
        self.link_attr_value_undesired=link_attr_value_undesired
        self.associated_data_attr=associated_data_attr
        self.get_img=get_img
        self.all_desired_image_links=self.find_all_desired_links(tag=self.image_link_tags,
                                                                 attr=self.img_link_attrs,
                                                                 attr_value_desired=self.img_attr_value_desired,
                                                                 attr_value_undesired=self.img_attr_value_undesired)
        self.all_desired_links=self.find_all_desired_links(tag=self.link_tags,
                                                           attr=self.link_attrs,
                                                           attr_value_desired=self.link_attr_value_desired,
                                                           attr_value_undesired=self.link_attr_value_undesired,
                                                           associated_data_attr=self.associated_data_attr,
                                                           get_img=get_img)
    def re_initialize(self):
        self.all_desired_image_links=self.find_all_desired_links(tag=self.image_link_tags,attr=self.img_link_attrs,strict_order_tags=self.strict_order_tags,attr_value_desired=self.img_attr_value_desired,attr_value_undesired=self.img_attr_value_undesired)
        self.all_desired_links=self.find_all_desired_links(tag=self.link_tags,attr=self.link_attrs,strict_order_tags=self.strict_order_tags,attr_value_desired=self.link_attr_value_desired,attr_value_undesired=self.link_attr_value_undesired,associated_data_attr=self.associated_data_attr,get_img=self.get_img)
    def update_url_manager(self,url_manager):
        self.url_manager=url_manager
        self.url=self.url_manager.url
        self.request_manager.update_url_manager(url_manager=self.url_manager)
        self.soup_manager.update_url_manager(url_manager=self.url_manager)
        self.source_code=self.soup_manager.source_code
        self.re_initialize()
    def update_url(self,url):
        self.url=url
        self.url_manager.update_url(url=self.url)
        self.url=self.url_manager.url
        self.request_manager.update_url(url=self.url)
        self.soup_manager.update_url(url=self.url)
        self.source_code=self.soup_manager.source_code
        self.re_initialize()
    def update_source_code(self,source_code):
        self.source_code=source_code
        if self.source_code != self.soup_manager.source_code:
            self.soup_manager.update_source_code(source_code=self.source_code)
        self.re_initialize()
    def update_soup_manager(self,soup_manager):
        self.soup_manager=soup_manager
        self.source_code=self.soup_manager.source_code
        self.re_initialize()
    def update_desired(self,img_attr_value_desired=None,img_attr_value_undesired=None,link_attr_value_desired=None,link_attr_value_undesired=None,image_link_tags=None,img_link_attrs=None,link_tags=None,link_attrs=None,strict_order_tags=None,associated_data_attr=None,get_img=None):
       self.strict_order_tags = strict_order_tags or self.strict_order_tags
       self.img_attr_value_desired=img_attr_value_desired or self.img_attr_value_desired
       self.img_attr_value_undesired=img_attr_value_undesired or self.img_attr_value_undesired
       self.link_attr_value_desired=link_attr_value_desired or self.link_attr_value_desired
       self.link_attr_value_undesired=link_attr_value_undesired or self.link_attr_value_undesired
       self.image_link_tags=image_link_tags or self.image_link_tags
       self.img_link_attrs=img_link_attrs or self.img_link_attrs
       self.link_tags=link_tags or self.link_tags
       self.link_attrs=link_attrs or self.link_attrs
       self.associated_data_attr=associated_data_attr or self.associated_data_attr
       self.get_img=get_img or self.get_img
       self.re_initialize()
    def find_all_desired(self,tag='img',attr='src',strict_order_tags=False,attr_value_desired=None,attr_value_undesired=None,associated_data_attr=None,get_img=None):
        def make_list(obj):
            if isinstance(obj,list) or obj==None:
                return obj
            return [obj]
        def get_desired_value(attr,attr_value_desired=None,attr_value_undesired=None):
            if attr_value_desired:
                for value in attr_value_desired:
                    if value not in attr:
                        return False
            if attr_value_undesired:
                for value in attr_value_undesired:
                    if value in attr:
                        return False
            return True
        attr_value_desired,attr_value_undesired,associated_data_attr,tags,attribs=make_list(attr_value_desired),make_list(attr_value_undesired),make_list(associated_data_attr),make_list(tag),make_list(attr)
        desired_ls = []
        assiciated_data=[]
        for i,tag in enumerate(tags):
            attribs_list=attribs
            if strict_order_tags:
                if len(attribs)<=i:
                    attribs_list=[None]
                else:
                    attribs_list=make_list(attribs[i])
            for attr in attribs_list:
                for component in self.soup_manager.soup.find_all(tag):
                    if attr in component.attrs and get_desired_value(attr=component[attr],attr_value_desired=attr_value_desired,attr_value_undesired=attr_value_undesired):
                        if component[attr] not in desired_ls:
                            desired_ls.append(component[attr])
                            assiciated_data.append({"value":component[attr]})
                            if associated_data_attr:
                                for data in associated_data_attr:
                                    if data in component.attrs:
                                        assiciated_data[-1][data]=component.attrs[data]
                                        if get_img and component.attrs[data]:
                                            if data in get_img and len(component.attrs[data])!=0:
                                                for each in self.soup_manager.soup.find_all('img'):
                                                    if 'alt' in each.attrs:
                                                        if each.attrs['alt'] == component.attrs[data] and 'src' in each.attrs:
                                                            assiciated_data[-1]['image']=each.attrs['src']
        desired_ls.append(assiciated_data)
        return desired_ls
    def find_all_domain(self):
        domains_ls=[self.url_manager.protocol+'://'+self.url_manager.domain]
        for desired in all_desired[:-1]:
            if url_manager.is_valid_url(desired):
                parse = urlparse(desired)
                domain = parse.scheme+'://'+parse.netloc
                if domain not in domains_ls:
                    domains_ls.append(domain)
    def find_all_desired_links(self,tag='img', attr='src',attr_value_desired=None,strict_order_tags=False,attr_value_undesired=None,associated_data_attr=None,all_desired=None,get_img=None):
        all_desired = all_desired or self.find_all_desired(tag=tag,attr=attr,strict_order_tags=strict_order_tags,attr_value_desired=attr_value_desired,attr_value_undesired=attr_value_undesired,associated_data_attr=associated_data_attr,get_img=get_img)
        assiciated_attrs = all_desired[-1]
        valid_assiciated_attrs = []
        desired_links=[]
        for i,attr in enumerate(all_desired[:-1]):
            valid_attr=self.url_manager.make_valid(attr,self.url_manager.protocol+'://'+self.url_manager.domain) 
            if valid_attr:
                desired_links.append(valid_attr)
                valid_assiciated_attrs.append(assiciated_attrs[i])
                valid_assiciated_attrs[-1]["link"]=valid_attr
        desired_links.append(valid_assiciated_attrs)
        return desired_links

def CrawlManager():
    def __init__(self,url=None,source_code=None,parse_type="html.parser"):
        self.url=url
        self.source_code=source_code
        self.parse_type=parse_type
        get_new_source_and_url(self,url)
    def get_new_source_and_url(self,url=None):
        if url == None:
            url = self.url
        self.response = self.response_manager.response
        self.source_code=self.response_manager.source_code
    def get_classes_and_meta_info():
        class_name_1,class_name_2, class_value = 'meta','class','property','og:image'
        attrs = 'href','src'
        unique_classes, images=discover_classes_and_images(self,tag_name,class_name_1,class_name_2,class_value,attrs)
        return unique_classes, images
    def extract_links_from_url(self):
        """
        Extracts all href and src links from a given URL's source code.

        Args:
            base_url (str): The URL from which to extract links.

        Returns:
            dict: Dictionary containing image links and external links under the parent page.
        """
        agg_js = {'images':[],'external_links':[]}
        
        if self.response != None:
            attrs = 'href','src'
            href_links,src_links='',''
            links = [href_links,src_links]
            for i,each in enumerate(attrs):
                 links[i]= [a[attr[i]] for a in get_find_all_with_attributes(self, attrs[i])]
            # Convert all links to absolute links
            absolute_links = [(url, link) for link in links[0] + links[1]]
            # Separate images and external links
            images = [link for link in absolute_links if link.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))]
            external_links = [link for link in absolute_links if urlparse(link).netloc != urlparse(url).netloc]
            agg_js['images']=images
            agg_js['external_links']=external_links
           
        return agg_js


    def correct_xml(xml_string):
        # Parse the XML string
        root = ET.fromstring(xml_string)

        # Loop through each <image:loc> element and correct its text if needed
        for image_loc in root.findall(".//image:loc", namespaces={'image': 'http://www.google.com/schemas/sitemap-image/1.1'}):
            # Replace '&' with '&amp;' in the element's text
            if '&' in image_loc.text:
                image_loc.text = image_loc.text.replace('&', '&amp;')

        # Convert the corrected XML back to string
        corrected_xml = ET.tostring(root, encoding='utf-8').decode('utf-8')
        return corrected_xml


    def determine_values(self):
        # This is just a mockup. In a real application, you'd analyze the URL or its content.

        # Assuming a blog site
        if 'blog' in self.url:
            if '2023' in self.url:  # Assuming it's a current year article
                return ('weekly', '0.8')
            else:
                return ('monthly', '0.6')
        elif 'contact' in self.url:
            return ('yearly', '0.3')
        else:  # Homepage or main categories
            return ('weekly', '1.0')
    def crawl(url, max_depth=3, depth=1):
        
        if depth > max_depth:
            return []

        if url in visited:
            return []

        visited.add(url)

        try:
            
            links = [a['href'] for a in self.soup.find_all('a', href=True)]
            valid_links = []

            for link in links:
                parsed_link = urlparse(link)
                base_url = "{}://{}".format(parsed_link.scheme, parsed_link.netloc)
            
                if base_url == url:  # Avoiding external URLs
                    final_link = urljoin(url, parsed_link.path)
                    if final_link not in valid_links:
                        valid_links.append(final_link)

            for link in valid_links:
                crawl(link, max_depth, depth+1)

            return valid_links

        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return []


    # Define or import required functions here, like get_all_website_links, determine_values, 
    # discover_classes_and_meta_images, and extract_links_from_url.
    def get_meta_info(self):
        
        meta_info = {}
        # Fetch the title if available
        title_tag = parse_title()
        if title_tag:
            meta_info["title"] = title_tag
        # Fetch meta tags
        for meta_tag in soup.find_all('meta'):
            name = meta_tag.get('name') or meta_tag.get('property')
            if name:
                content = meta_tag.get('content')
                if content:
                    meta_info[name] = content

        return meta_info
    def generate_sitemap(self,domain):
        
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            string = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
            
            for url in self.all_site_links:
                string += f'  <url>\n    <loc>{url}</loc>\n'
                preprocess=[]
                self.get_new_source_and_url(url=url)
                links = extract_links_from_url(url)
                
                for img in links['images']:
                    if str(img).lower() not in preprocess:
                        try:
                            escaped_img = img.replace('&', '&amp;')

                            str_write = f'    <image:image>\n      <image:loc>{escaped_img}</image:loc>\n    </image:image>\n'
                            string += str_write
                        except:
                            pass
                        preprocess.append(str(img).lower())
                frequency, priority = determine_values(url)
                string += f'    <changefreq>{frequency}</changefreq>\n'
                string += f'    <priority>{priority}</priority>\n'
                string += f'  </url>\n'
                
            string += '</urlset>\n'
            f.write(string)            
        # Output summary
        print(f'Sitemap saved to sitemap.xml with {len(urls)} URLs.')
        
        # Output class and link details
        for url in urls:
            print(f"\nDetails for {url}:")
            classes, meta_img_refs = discover_classes_and_meta_images(url)

            print("\nClasses with href or src attributes:")
            for class_name in classes:
                print(f"\t{class_name}")
            
            print("\nMeta Image References:")
            for img_ref in meta_img_refs:
                print(f"\t{img_ref}")
            
            links = extract_links_from_url(url)

            print("\nImages:")
            for img in links['images']:
                print(f"\t{img}")
            
            print("\nExternal Links:")
            for ext_link in links['external_links']:
                print(f"\t{ext_link}")
class CrawlManagerSingleton():
    _instance = None
    @staticmethod
    def get_instance(url=None,source_code=None,parse_type="html.parser"):
        if CrawlManagerSingleton._instance is None:
            CrawlManagerSingleton._instance = CrawlManager(url=url,parse_type=parse_type,source_code=source_code)
        elif parse_type != CrawlManagerSingleton._instance.parse_type or url != CrawlManagerSingleton._instance.url  or source_code != CrawlManagerSingleton._instance.source_code:
            CrawlManagerSingleton._instance = CrawlManager(url=url,parse_type=parse_type,source_code=source_code)
        return CrawlManagerSingleton._instance
