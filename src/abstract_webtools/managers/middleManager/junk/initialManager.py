from .imports import get_url_mgr,get_url
def get_url_tools(url=None,
                 url_mgr=None
                 ):
    basics_js = {
            "urls":{
                "url":url,
                "url_mgr":url_mgr
                }
    for key,values in basics_js.items():
        if key == 'urls':
            url = values.get("url")
            url_mgr= values.get("url_mgr")
            url_mgr = get_url_mgr(url=url,url_mgr=url_mgr)
            url = get_url(url=url,url_mgr=url_mgr)
            basics_js['url']=url
            basics_js['url_mgr']=url_mgr
    return basics_js
