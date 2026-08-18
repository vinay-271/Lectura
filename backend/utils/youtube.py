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

def extract_video_id(url: str) -> str | None:
    parsed_url = urlparse(url)

    hostname = parsed_url.hostname

    if hostname is None:
        return None

    hostname = hostname.lower()

    if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        return parsed_url.query.split("v=", 1)[1].split("&", 1)[0] if "v=" in parsed_url.query else None

    if hostname in {"youtu.be", "www.youtu.be"}:
        return parsed_url.path.strip("/").split("/")[0] or None

    return None