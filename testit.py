from src.abstract_webtools.managers import *

data = safe_read_from_json('/mnt/24T/testout/video_json.json')

for key,values in data.items():
    link_mgr = linkManager()
    source_code=values.get('html')
    link_mgr = linkManager(source_code=source_code)
    links = link_mgr.find_all_desired_links()
    input(links)
