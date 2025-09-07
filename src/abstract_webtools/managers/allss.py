from abstract_apis import *
from abstract_webtools import *
url = 'https://clownworld.biz/media/download_from_url'
url = 'https://vk.com/video-79421135_456239830'

info = downloadvideo(url)
input(info)
response= postRequest(url,data={"url":url})
input(response.json())
