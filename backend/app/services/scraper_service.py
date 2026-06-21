import httpx
from bs4 import BeautifulSoup
from typing import Optional


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch a URL and return the raw HTML text, or None on failure."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except Exception:
        return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "lxml")
    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def scrape_job_page(url: str) -> tuple[str, str]:
    """
    Returns (raw_html, clean_text). clean_text is empty string on failure.
    """
    html = fetch_url(url)
    if not html:
        return "", ""
    text = extract_text_from_html(html)
    return html, text
