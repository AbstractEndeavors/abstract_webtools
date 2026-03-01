from player_responses import *
input(get_preselected_player_response_values(url="https://www.youtube.com/watch?v=34MJuKR5rAY"))
from src.abstract_webtools import *
info_mgr = infoRegistry()


url = 'https://www.youtube.com/shorts/rLlWcvLBluI'
print(info_mgr.infoRegistryDirectory)
# First call → fetches with yt_dlp and caches
dl = VideoDownloader(url, get_info=True,download_video=True)
##info = info_mgr.get_video_info(url)
##
##print(info.get('file_path'))  # absolute path to downloaded video
print(dl.registry.list_cached_videos())  # show everything cached
all_data = get_all_data('https://www.youtube.com/shorts/rLlWcvLBluI')
