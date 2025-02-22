from urllib.parse import urljoin

MAX_PAGE_SIZE = 200


def strava_url(path: str) -> str:
    return urljoin("https://www.strava.com/api/v3/", path.lstrip("/"))
