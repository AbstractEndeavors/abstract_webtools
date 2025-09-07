from extention_list import get_extention,popular_extentions
from urllib.parse import urlparse, urljoin
from abstract_utilities import *
def try_request(url,timeout=None):
    if timeout == None:
        timeout= 5
    elif timeout == 0:
        timeout = None
    try:
        result = requests.get(url, timeout=timeout)  # Set timeout to 5 seconds
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        result = None
    return result
def is_result_200(result):
    try:
        if result.status_code == 200:
            return True
    except:
        return False
    return False
def url_to_pieces(url):
    """
    Split a URL into protocol, domain, path, and query components.
    Uses urlparse for robustness.
    """
    parsed_url = {'parsed':'', 'scheme':'', 'netloc':'', 'subdomain':'', 'domain':url,'extention':'', 'path':'', 'params':'', 'query':'', 'fragment':''}
    try:
        parsed = urlparse(url)
        parsed_url['parsed']= parsed
        parsed_url['scheme'] = parsed.scheme if parsed.scheme else ""
        parsed_url['netloc'] = parsed.netloc if parsed.netloc else ""
        parsed_url['path'] = parsed.path or ""
        parsed_url['params'] = parsed.params or ""
        parsed_url['query'] = parsed.query or ""
        parsed_url['fragment'] = parsed.fragment or ""
        if parsed_url['netloc'] == '' and parsed_url['path']:
            parsed_url['netloc'] = parsed_url['path']
            if '/' in parsed_url['path']:
                parsed_url['netloc'] = parsed_url['path'].split('/')[0]
                parsed_url['path'] = '/'+'/'.join(parsed_url['path'].split('/')[1:])
            else:
                parsed_url['path']=''
        if parsed_url['netloc']:
            if parsed_url['netloc'].startswith('www.'):
                parsed_url['subdomain']= 'www.'
                parsed_url['domain'] = parsed_url['netloc'][len('www.'):]
            else:
                parsed_url['domain'] = parsed_url['netloc']
            parsed_url.update(get_extention(parsed_url['domain']))
    except Exception as e:
        print(f'The URL {url} was not reachable: {e}')
    return parsed_url
def correct_domains(url):
    urls = [url]
    protocols = {'https':['','www.'],'http':['','www.'],'':['','www.']}
    parsed_url = url_to_pieces(url)
    scheme,subdomain,extentions = parsed_url['scheme'], parsed_url['subdomain'],make_list(parsed_url['extention'] or popular_extentions)
    subdomains = protocols.get(scheme)
    if subdomain in subdomains:
        subdomains.remove(subdomain)
    protocols[scheme] = subdomains
    for extention in extentions:
        link = f"{parsed_url['domain']}{extention}{parsed_url['path']}{parsed_url['params']}"
        for key,values in protocols.items():
            for value in values:
                new_link = f"{value}{link}"
                if key:
                    new_link = f"{key}://{new_link}"
                urls.append(new_link)
    return urls
def tryAllDomains(url):
    urls = correct_domains(url)
    for i, url in enumerate(urls):
        result = try_request(url)
        if is_result_200(result):
            return url
def tryDomain(url):
    request_mgr = requestManager(url)
    return request_mgr.source_code
url='thedailydialectics'
input(tryAllDomains(url))
