from ..imports import *
def domain_exists(host: str) -> bool:
    """Check if a domain resolves in DNS."""
    try:
        socket.gethostbyname(host)
        return True
    except socket.error:
        return False

def get_extention(url=None, parsed=None, netloc=None, options=None):
    """
    Split netloc into {www, domain, extention}.
    Cycles through www + extension options until a working one is found.
    """
    options = options or ALL_URL_KEYS["netloc"]

    # Ensure we have a string netloc
    if url and not parsed:
        parsed = urlparse(url)
    if parsed and not netloc:
        netloc = parsed["netloc"] if isinstance(parsed, dict) else parsed.netloc
    if isinstance(netloc, dict):
        netloc = reconstructNetLoc(netloc)

    if not netloc:
        return {"www": False, "domain": "", "extention": ".com"}

    netloc = netloc.lower().strip()

    # detect existing www
    has_www = netloc.startswith("www.")
    if has_www:
        netloc = netloc[len("www.") :]

    # cycle through options
    www_opts = options["www"]
    ext_opts = options["extentions"][0] + options["extentions"][1]  # POPULAR + ALL

    # if the netloc already ends with a known extension, use it
    for ext in sorted(ALL_EXTENTIONS, key=len, reverse=True):
        if netloc.endswith(ext):
            domain = netloc[: -len(ext)]
            return {"www": has_www, "domain": domain, "extention": ext}

    # else, try combinations
    for www in www_opts:
        for ext in ext_opts:
            candidate = f"{'www.' if www else ''}{netloc}{ext}"
            if domain_exists(candidate):
                return {"www": www, "domain": netloc, "extention": ext}

    # fallback
    return {"www": has_www, "domain": netloc, "extention": ".com"}


