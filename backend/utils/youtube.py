from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    parsed_url = urlparse(url)

    hostname = parsed_url.hostname

    if hostname is None:
        return False

    hostname = hostname.lower()

    return hostname in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }