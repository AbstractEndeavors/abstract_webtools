import os, subprocess, requests

def curl_download(website, destination_path, user_agent=None):
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    ua = user_agent or ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/91.0.4472.124 Safari/537.36")
    subprocess.run([
        "curl","-L","--output", destination_path,
        "-H", f"User-Agent: {ua}",
        "-H", "Accept: */*",
        website
    ], check=True)

def requests_download(website, destination_path, headers=None):
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    hdr = {"User-Agent": ("Mozilla/5.0 ... Chrome/91.0 Safari/537.36"),
           "Accept": "*/*"}
    if headers: hdr.update(headers)
    r = requests.get(website, headers=hdr, allow_redirects=True, timeout=30)
    r.raise_for_status()
    with open(destination_path, "wb") as f:
        f.write(r.content)

if __name__ == "__main__":
    pass  # no side effects
