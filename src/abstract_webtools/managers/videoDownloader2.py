from abstract_webtools import requestManager, urlManager, soupManager, requests, linkManager
import threading,os,re,yt_dlp,urllib.request,m3u8_To_MP4,subprocess
from abstract_utilities import get_logFile,safe_dump_to_file

from m3u8 import M3U8  # Install: pip install m3u8
from urllib.parse import urljoin
from yt_dlp.postprocessor.ffmpeg import FFmpegFixupPostProcessor
from abstract_math import divide_it,add_it,multiply_it,subtract_it
from abstract_pandas import *
class VideoDownloader:
    def __init__(self, url, title=None, download_directory=os.getcwd(), user_agent=None, video_extention='mp4', 
                 download_video=True, get_info=False, auto_file_gen=True, standalone_download=False, output_filename=None):
        self.url = url
        self.monitoring = True
        self.pause_event = threading.Event()
        self.get_download = download_video
        self.get_info = get_info
        self.user_agent = user_agent
        self.title = title
        self.auto_file_gen = auto_file_gen
        self.standalone_download = standalone_download
        self.video_extention = video_extention
        self.download_directory = download_directory
        self.output_filename = output_filename  # New parameter for custom filename
        self.header = {}  # Placeholder for UserAgentManagerSingleton if needed
        self.base_name = os.path.basename(self.url)
        self.file_name, self.ext = os.path.splitext(self.base_name)
        self.video_urls = [self.url]
        self.info = {}
        self.starttime = None
        self.downloaded = 0
        self.video_urls = url if isinstance(url, list) else [url]
        self.send_to_dl()

    def get_request(self, url):
        self.request_manager = requestManagerSingleton.get_instance(url=url)
        return self.request_manager

    def send_to_dl(self):
        if self.standalone_download:
            self.standalone_downloader()
        else:
            self.start()

    def get_headers(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.headers
        else:
            logger.error(f"Failed to retrieve headers for {url}. Status code: {response.status_code}")
            return {}

    @staticmethod
    def get_directory_path(directory, name, video_extention):
        file_path = os.path.join(directory, f"{name}.{video_extention}")
        i = 0
        while os.path.exists(file_path):
            file_path = os.path.join(directory, f"{name}_{i}.{video_extention}")
            i += 1
        return file_path

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        self.downloaded = total_size - bytes_remaining

    def download(self):
        for video_url in self.video_urls:
            # Use custom filename if provided, otherwise generate a short temporary one
            if self.output_filename:
                outtmpl = os.path.join(self.download_directory, self.output_filename)
            else:
                temp_id = re.sub(r'[^\w\d.-]', '_', video_url)[-20:]  # Short temp ID from URL
                outtmpl = os.path.join(self.download_directory, f"temp_{temp_id}.%(ext)s")
            
            ydl_opts = {
                'external_downloader': 'ffmpeg',
                'outtmpl': outtmpl,
                'noprogress': True,
                'quiet': True,  # Reduce verbosity in logs
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.info = ydl.extract_info(video_url, download=self.get_download)
                    self.downloading = False
                    self.starttime = get_time_stamp()  # Assuming get_time_stamp() exists
                    if self.auto_file_gen:
                        file_path = ydl.prepare_filename(self.info)
                        if self.get_info:
                            self.info['file_path'] = file_path  # Fixed typo 'aath'
                    if self.get_info:
                        self.stop()
                        return self.info
            except Exception as e:
                logger.error(f"Failed to download {video_url}: {str(e)}")
            self.stop()
        return self.info

    def monitor(self):
        while self.monitoring:
            logger.info("Monitoring...")
            self.pause_event.wait(60)  # Check every minute
            if self.starttime:
                elapsed_time = subtract_it(get_time_stamp(),self.starttime)
                if self.downloaded != 0 and elapsed_time != 0:
                    cumulative_time = add_it(self.downloaded,elapsed_time)
                    percent = divide_it(self.downloaded,cumulative_time)
                else:
                    percent = 0
                if elapsed_time != 0:
                    try:
                        downloaded_minutes = divide_it(elapsed_time,60)
                        estimated_download_minutes = divide_it(downloaded_minutes,percent)
                        estimated_download_time =  subtract_it(estimated_download_minutes,downloaded_minutes)
                    except ZeroDivisionError:
                        logger.warning("Caught a division by zero in monitor!")
                        continue
                if downloaded_minutes != 0 and subtract_it(percent,downloaded_minutes) != 0:
                    estimated_download_minutes = divide_it(downloaded_minutes,percent)
                    estimated_download_time =  subtract_it(estimated_download_minutes,downloaded_minutes)
                    logger.info(f"Estimated download time: {estimated_download_time} minutes")
                if estimated_download_time >= 1.5:
                    logger.info("Restarting download due to slow speed...")
                    self.start()  # Restart download

    def start(self):
        self.download_thread = threading.Thread(target=self.download)
        self.download_thread.daemon = True
        self.monitor_thread = threading.Thread(target=self.monitor)
        self.download_thread.start()
        self.monitor_thread.start()
        self.download_thread.join()
        self.monitor_thread.join()

    def stop(self):
        self.monitoring = False
        self.pause_event.set()

def download_image(url, save_path=None):
    """
    Downloads an image from a URL and saves it to the specified path.
    
    Args:
        url (str): The URL of the image to download
        save_path (str, optional): Path to save the image. If None, uses the filename from URL
        
    Returns:
        str: Path where the image was saved, or None if download failed
    """
    try:
        # Send GET request to the URL
        response = requests.get(url, stream=True)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Set decode_content=True to automatically handle Content-Encoding
            response.raw.decode_content = True
            
            # If no save_path provided, extract filename from URL
            if save_path is None:
                # Get filename from URL
                filename = url.split('/')[-1]
                save_path = filename
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Write the image content to file
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Image successfully downloaded to {save_path}")
            return save_path
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None
def get_thumbnails(directory,info):
    thumbnails_dir = os.path.join(directory,'thumbnails')
    os.makedirs(thumbnails_dir, exist_ok=True)
    thumbnails = info.get('thumbnails',[])
    for i,thumbnail_info in enumerate(thumbnails):
        thumbnail_url = thumbnail_info.get('url')
        thumbnail_base_url = thumbnail_url.split('?')[0]
        baseName = os.path.basename(thumbnail_base_url)
        fileName,ext = os.path.splitext(baseName)
        baseName = f"{fileName}{ext}"
        resolution = info['thumbnails'][i].get('resolution')
        if resolution:
            baseName = f"{resolution}_{baseName}"
        img_id = info['thumbnails'][i].get('id')
        if img_id:
            baseName = f"{img_id}_{baseName}"
        thumbnail_path = os.path.join(thumbnails_dir,baseName)
        info['thumbnails'][i]['path']=thumbnail_path
        download_image(thumbnail_url, save_path=thumbnail_path)
    return info
def download_audio(directory, info):
    """
    Download the highest-quality audio (e.g., hls-audio-128000-Audio) from info.json and save it to a directory.
    
    Args:
        directory (str): Base directory for saving files (e.g., /var/www/clownworld/data/downloads/videos/videos/1897210679465328845/)
        info (dict): Dictionary containing video metadata from info.json, including 'formats' and 'video_id'
    
    Returns:
        dict: Updated info with the audio file path
    """
    # Create an 'audio' subdirectory
    audio_dir = os.path.join(directory, 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    # Find the highest-quality audio format (e.g., hls-audio-128000-Audio with 128 kbps)
    audio_formats = [f for f in info.get('formats', []) if f['format_id'].startswith('hls-audio')]
    if not audio_formats:
        logger.info("No audio formats found in info.json")
        return info
    # Sort by bitrate (tbr) to get the highest quality
    audio_format = max(audio_formats, key=lambda x: x.get('tbr', 0))
    audio_url = audio_format.get('url')
    audio_ext = audio_format.get('ext', 'mp4')  # Default to MP4 if not specified

    # Extract video_id for filename
    video_id = info.get('video_id', 'unknown_video')
    title = info.get('title', 'audio').replace(' ', '_')  # Clean title for filename
    filename = f"{title}_{video_id}.{audio_ext}"
    audio_path = os.path.join(audio_dir, filename)

    # Download and process the M3U8/HLS audio stream
    try:
        # Fetch the M3U8 playlist
        response = requests.get(audio_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.19 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate'
        })
        response.raise_for_status()

        # Parse the M3U8 playlist
        m3u8_obj = M3U8(response.text)
        base_url = '/'.join(audio_url.split('/')[:-1]) + '/'  # Base URL for relative segment paths

        # Download all TS segments
        segments = []
        for segment in m3u8_obj.segments:
            segment_url = urljoin(base_url, segment.uri)
            segment_response = requests.get(segment_url, headers=response.request.headers)
            segment_response.raise_for_status()
            segments.append(segment_response.content)

        # Save segments to temporary files for processing with ffmpeg
        temp_dir = os.path.join(audio_dir, 'temp_segments')
        os.makedirs(temp_dir, exist_ok=True)
        segment_paths = []
        for i, segment_data in enumerate(segments):
            segment_path = os.path.join(temp_dir, f'segment_{i}.ts')
            with open(segment_path, 'wb') as f:
                f.write(segment_data)
            segment_paths.append(segment_path)

        # Use ffmpeg to concatenate TS segments into a single MP4 audio file
        output_path = audio_path
        try:
            ffmpeg.input('concat:' + '|'.join(segment_paths), format='concat', safe=0).output(
                output_path, c='copy', loglevel='quiet'
            ).run()
        except Exception as e:
            logger.info(f"FFmpeg error: {e.stderr.decode()}")

        # Clean up temporary segment files
        for segment_path in segment_paths:
            os.remove(segment_path)
        os.rmdir(temp_dir)

        # Update info with the audio path

        info['audio_path'] = audio_path
        info['audio_url'] = f"https://clownworld.biz/data/downloads/videos/videos/{video_id}/audio/{filename}"

    except requests.RequestException as e:
        logger.info(f"Failed to download audio: {str(e)}")
    except Exception as e:
        logger.info(f"Error processing audio: {str(e)}")

    return info
