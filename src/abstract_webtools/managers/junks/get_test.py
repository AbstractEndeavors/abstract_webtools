from abstract_webtools import *



url = 'https://pump.fun'
input()
print('starting')
#SELENIUM/DOMAIN MANAGER
domain_mgr = seleniumManager(url)
print(domain_mgr.domain)

#URL MANAGER
url_mgr = urlManager(url=domain_mgr.domain)
url = url_mgr.url
print(url)

#REQUEST MANAGER
req_mgr = requestManager(url=url,url_mgr=url_mgr)
source_code = req_mgr.source_code
print(source_code)

#SOUP MANAGER
soup_mgr = soupManager(url_mgr=url_mgr,req_mgr=req_mgr)
soup = soup_mgr.soup
print(soup)
all_attributes = soup_mgr.get_all_attribute_values()
print(all_attributes)

#LINK MANAGER
link_mgr = linkManager(url)
all_domains = link_mgr.find_all_domain()
print(all_domains)

all_desired_links = link_mgr.all_desired_links
print(all_desired_links)

all_desired_image_links = link_mgr.all_desired_image_links
print(all_desired_image_links)

