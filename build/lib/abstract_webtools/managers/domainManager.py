from abstract_webtools import *
import os
from abstract_webtools import *
#from .urlManager import *
from urllib.parse import urlparse
from abstract_utilities import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import urllib3

# Suppress urllib3 warnings and debug logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Suppress Selenium logs
logging.getLogger("selenium").setLevel(logging.WARNING)

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Setup Chrome options
chrome_options = Options()
chrome_options.binary_location = "/home/profiles/solcatcher/.cache/selenium/chrome/linux64/130.0.6723.58/chrome"
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--remote-debugging-port=9222")


class domainManager(metaclass=SingletonMeta):
    def __init__(self, url):
        if not hasattr(self, 'initialized'):  # Prevent reinitialization
            self.initialized = True
            parsed_url = urlparse(url)
            self.domain = parsed_url.netloc
            self.scheme = parsed_url.scheme
            self.site_dir = os.path.join(os.getcwd(), self.domain)
            os.makedirs(self.site_dir, exist_ok=True)
            self.drivers = {}
            self.page_type = []
    def get_url_to_path(self, url):
        url = eatAll(str(url),['',' ','\n','\t','\\','/'])
        parsed_url = urlparse(url)
        if 'data:image' in url:
            input(url)
        if parsed_url.netloc == self.domain:
            paths = parsed_url.path.split('/')
            dir_path =self.site_dir
            for path in paths[:-1]:
                dir_path = os.path.join(dir_path, path)
                os.makedirs(dir_path, exist_ok=True)
        #if 'svg' in url:
        #$    input(url)
         #   dir_path = get_image_name('contents',directory=dir_path,ext='png',url=item_url)


            self.page_type.append(os.path.splitext(paths[-1])[-1] or 'html' if len(self.page_type) == 0 else self.page_type[-1])
            
            dir_path = os.path.join(dir_path, paths[-1])
            return dir_path

    def saved_url_check(self, url):
  
        path = self.get_url_to_path(url)
        return path

    def get_with_netloc(self, url):
        parsed_url = urlparse(url)
        if parsed_url.netloc == '':
            url = f"{self.scheme}://{self.domain}/{url.strip()}"
        return url

    def get_driver(self, url):
        if url and url not in self.drivers:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
            self.drivers[url] = driver
            driver.get(url)
        return self.drivers[url]
def get_selenium_source(url):
    url_mgr = urlManager(url)
    if url_mgr.url:
        url = str(url_mgr.url)
        manager = domainManager(url)
        driver = manager.get_driver(url)
        try:
            # Get page source
            page_source = driver.page_source
            return page_source
        finally:
            # Don't quit the driver unless you're done with all interactions
            pass
driver = get_selenium_source('http://solpump.io/')
input(driver)
