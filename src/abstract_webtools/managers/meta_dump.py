# meta_dump.py
from abstract_webtools.managers.networkManager import NetworkManager
from abstract_webtools.managers.userAgentManager import UserAgentManager
from abstract_webtools.managers.soupManager.soupManager import soupManager
import json, sys

def dump_all_meta(url: str):
    ua = UserAgentManager(browser="Chrome", operating_system="Windows")
    net = NetworkManager(user_agent_manager=ua)

    r = net.session.get(url, timeout=30)
    r.raise_for_status()

    sm = soupManager(url=url, source_code=r.text, req_mgr=net)
    out = {
        "url": url,
        "title": sm.soup.title.string.strip() if sm.soup.title and sm.soup.title.string else None,
        "meta": sm.all_meta(),
        "citation": sm.citation_dict(),
        "links": sm.all_links(),
        "json_ld": sm.all_jsonld(),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    url = sys.argv[1]
    dump_all_meta(url)
