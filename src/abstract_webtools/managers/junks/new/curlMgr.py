import os
import requests
import os
import subprocess
import stat

def get_site(website, destination_dir, filename):
    # Ensure the directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Adjust directory permissions if needed (e.g. rwxr-xr-x -> 0o755)
    os.chmod(destination_dir, 0o755)

    # Construct the complete file path
    destination_path = os.path.join(destination_dir, filename)

    # Use curl to download the site
    # The example user-agent is arbitrary; you can change it to your needs
    os.system(
        f'curl -L --output "{destination_path}" '
        f'-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
        f'Safari/537.36" -H "Accept: */*" "{website}"'
    )

def download_site(website, destination_dir, filename):
    os.makedirs(destination_dir, exist_ok=True)
    os.chmod(destination_dir, 0o755)  # set directory permissions if needed

    destination_path = os.path.join(destination_dir, filename)

    # GET the resource
    response = requests.get(website, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*"
    }, allow_redirects=True)

    # Raise an exception if the download fails
    response.raise_for_status()

    # Write content to file
    with open(destination_path, "wb") as f:
        f.write(response.content)
website = 'https://www.pornhub.com'
destination = '/home/computron/Documents/doge'
get_site(website,destination,'doge')
