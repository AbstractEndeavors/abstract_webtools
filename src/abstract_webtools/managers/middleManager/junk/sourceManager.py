from .imports import get_url_mgr,get_url,get_req_mgr,get_source

def get_req_tools(url=None,
                 url_mgr=None,
                source_code=None,
                req_mgr=None):
                 
    basics_js = {
                "urls":{
                    "url":url,
                    "url_mgr":url_mgr
                    },
                "sources":{
                    "source_code":source_code,
                    "req_mgr":req_mgr
                    }
               }
    for key,values in basics_js.items():
        if key == 'urls':
            url = values.get("url")
            url_mgr= values.get("url_mgr")
            url_mgr = get_url_mgr(url=url,url_mgr=url_mgr)
            url = get_url(url=url,url_mgr=url_mgr)
            basics_js['url']=url
            basics_js['url_mgr']=url_mgr
        if key == 'sources':
            source_code = values.get("source_code")
            req_mgr= values.get("req_mgr")
            req_mgr = get_req_mgr(url=url,url_mgr=url_mgr,source_code=source_code,req_mgr=req_mgr)
            source_code = get_source(url=url,url_mgr=url_mgr,source_code=source_code,req_mgr=req_mgr)
            basics_js['source_code']=source_code
            basics_js['req_mgr']=req_mgr
    return basics_js
