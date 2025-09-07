import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

visited = set()

def download_page(url, destination_dir):
    """Download a single page to the destination directory."""

    # Create directory if needed
    os.makedirs(destination_dir, exist_ok=True)
    os.chmod(destination_dir, 0o755)  # optional: set directory perms

    # Download
    response = requests.get(url)
    response.raise_for_status()

    # Build a safe file name for the HTML file
    # E.g., for "https://example.com/about/", you might store "about.html"
    parsed = urlparse(url)
    filename = "index.html" if not parsed.path or parsed.path.endswith("/") else os.path.basename(parsed.path)
    if not filename.endswith(".html"):
        filename += ".html"

    filepath = os.path.join(destination_dir, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)

    return response.text, filepath

def crawl(url, destination_dir):
    """Recursively download a site starting from `url`."""
    if url in visited:
        return
    visited.add(url)

    try:
        html, _ = download_page(url, destination_dir)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")

    # Find all <a> tags with an href
    for link_tag in soup.find_all("a", href=True):
        link = link_tag["href"]

        # Convert a relative URL to an absolute one
        absolute_link = urljoin(url, link)

        # (Optional) Check domain if you only want to crawl the same site
        # or skip mailto:, javascript:, etc.
        if absolute_link.startswith("http"):
            # Recurse
            crawl(absolute_link, destination_dir)

if __name__ == "__main__":
    start_url = "https://svscomics.com/category/giantess/page/24"
    destination = "/home/svc"

    crawl(start_url, destination)
