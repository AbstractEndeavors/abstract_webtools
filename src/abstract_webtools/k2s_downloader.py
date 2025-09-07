import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from abstract_security import *
from abstract_webtools import *
from abstract_utilities import safe_dump_to_file,safe_read_from_json
DOWNLOAD_DIR = os.path.abspath("./downloads")

class K2SDownloader:
    def __init__(self,env_path=None,download_dir=None,json_file_path=None):
        self.download_dir = download_dir or DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)
        self.json_file_path = json_file_path
        
        self.env_path = env_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = self._init_driver()
        self.logged_in = False

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless")
        
        # Configure download preferences
        prefs = {
            "download.default_directory": self.download_dir,  # Set custom download directory
            "download.prompt_for_download": False,            # Disable download prompt
            "download.directory_upgrade": True,              # Allow directory override
            "safebrowsing.enabled": True                     # Enable safe browsing
        }
        options.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options)

    def login(self):
        userName = get_env_value('userName',path=self.env_path)
        passWord = get_env_value('passWord',path=self.env_path)

        self.driver.get("https://k2s.cc/auth/login")
        time.sleep(3)

        
        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "input-password-auto-complete-on")
        email_input.send_keys(userName)
        password_input.send_keys(passWord)
        password_input.send_keys(Keys.RETURN)

        #WebDriverWait(self.driver, 20).until(
        #    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Logout')]"))
        #)
        self.logged_in = True
        print("Login successful")
        #except Exception as e:
        #    print(f"Login failed: {e}")
        #    with open('login_error.html', 'w', encoding='utf-8') as f:
        #        f.write(self.driver.page_source)

    def download_file(self, url,download_dir=None):
        if not self.logged_in:
            self.login()
        download_dir = download_dir or self.download_dir
        print(f"Navigating to: {url}")
        self.driver.get(url)
        time.sleep(5)

        if 'captcha' in self.driver.page_source.lower():
            print("CAPTCHA detected. Manual intervention required.")
            return

        try:
            download_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="/download"], button[class*="download"]'))
            )
            print("Download button found; attempting to click or fetch URL")
            download_url = download_button.get_attribute('href')

            if download_url:
                response = self.session.get(download_url, stream=True)
                file_name = self._extract_filename(response, download_url)
                file_path = os.path.join(download_dir, file_name)
                if not os.path.isfile(file_path):
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded: {file_path}")
                return file_path
            else:
                download_button.click()
                print("Button clicked. Waiting for download...")
                time.sleep(30)  # adjust as needed
        except Exception as e:
            print(f"Download failed for {url}: {e}")

    def _extract_filename(self, response, url):
        cd = response.headers.get('Content-Disposition', '')
        if 'filename=' in cd:
            return cd.split('filename=')[-1].strip('"')
        return url.split('/')[-1].split('?')[0]
def get_json_key_value(json_data,key):
    if json_data and isinstance(json_data,dict):
        return json_data.get(key)
def compare_keys(json_data,comp_json_data,key):
    json_key_value = get_json_key_value(json_data,key)
    comp_json_key_value = get_json_key_value(comp_json_data,key)
    if json_key_value and comp_json_key_value and comp_json_key_value==json_key_value:
        return True
def check_json_data(json_list,new_data):
    keys = ['k2s','link','name']
    for json_data in json_list:
        for key in keys:
            result = compare_keys(json_data,new_data,key)
            if result:
                return result

class dlsManager:
    def __init__(self, downloader):
        self.downloader = downloader
        self.json_file_path = self.downloader.json_file_path
        self.download_dir = self.downloader.download_dir
        all_dls= None
        if self.json_file_path:
            all_dls = safe_read_from_json(self.json_file_path)
        self.all_dls = all_dls or  []
        self.last_data = None
    def is_prev_dl(self, data):
        if check_json_data(self.all_dls,data):
            self.last_data = None
            return True
        self.last_data = data
        return False

    def dl_k2s_link(self, k2s_link):
        if k2s_link:
            print(f"Downloading: {k2s_link}")
            self.downloader.download_file(k2s_link,self.download_dir)
            time.sleep(10)
            if self.json_file_path:
                self.all_dls.append(self.last_data)
                safe_dump_to_file(data=self.all_dls,
                                  file_path=self.json_file_path)


def get_soup(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"Failed to fetch soup for {url}: {e}")
        return None

def get_k2s_link(soup):
    match = re.search(r'https://k2s\.cc/file/[^"<]+', str(soup))
    return match.group(0) if match else None

def get_sections_content(content,get_post_attribute,dls_mgr):
    results=[]
    if not content:
        return []
    for section in content:
        data = get_post_attribute(section)
        if data and data.get('k2s') and not dls_mgr.is_prev_dl(data):
            dls_mgr.dl_k2s_link(data['k2s'])
            results.append(data)
    return results
