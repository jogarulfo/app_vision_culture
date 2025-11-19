import requests


def fetch_summary(title: str, sentences: int = 2) -> str:
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "")
    except Exception:
        pass
    return ""
