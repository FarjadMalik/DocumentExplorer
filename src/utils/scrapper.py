import requests
import requests_cache
import csv
import time

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from bs4 import BeautifulSoup
from typing import Optional

# Install requests cache: caches requests to avoid repeat network calls
requests_cache.install_cache("webcache", expire_after=3600)  # 1-hour cache

from src.utils.logger import get_logger

logger = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_page(url: str, timeout: float = 10.0) -> str:
    """Fetch raw HTML with retry logic and caching."""

    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests_cache.CachedSession().get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_html_text(url: str, timeout: int = 10) -> str:
    """
    Fetches an HTML page from `url`, parses with BeautifulSoup, and returns the formatted text.
    
    Args:
        url (str): The URL to fetch.
        timeout (int): Timeout for the HTTP request in seconds.

    Returns:
        str: Formatted text extracted from the HTML.
    """
    try:
        # 1. Fetch the page
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise exception for bad HTTP status

        # 2. Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # 3. Get all text in the page
        text = soup.get_text(separator="\n", strip=True)
        return text

    except requests.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        return ""
    
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_html_soup(url: str, timeout: int = 10) -> BeautifulSoup | None:
    """    
    Args:
        url (str): The URL to fetch.
        timeout (int): Timeout for the HTTP request in seconds.

    Returns:
        BeautifulSoup: soup for the html page
    """
    try:
        # Fetch the page
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise exception for bad HTTP status

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # text = soup.get_text(separator="\n", strip=True)
        return soup

    except requests.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_html_paragraphs(url: str, timeout: int = 10) -> list[str]:
    """
    Docstring for fetch_html_paragraphs
    
    :param url: Description
    :type url: str
    :param timeout: Description
    :type timeout: int
    :return: Description
    :rtype: list[str]
    """
    try:
        soup = fetch_html_soup(url, timeout)
        if soup is None:
            return list([])
        
        # Extract text from all <p> tags
        paragraphs = []
        for p in soup.find_all("p"):
            # Get trimmed text from the tag
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        return paragraphs

    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        return list([])

def get_page(session, page_num: int, base_url: str = ""):
    """Fetch a given page number of events; returns BeautifulSoup of the page."""
    params = {"page": page_num}
    resp = session.get(base_url, params=params, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def parse_table(soup):
    """Parse the events table from a BeautifulSoup object and yield dicts per row."""
    rows = soup.select("table tr")[1:]  # skip header row
    for tr in rows:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        # as per table header: Date, Time (utc), Latitude, Longitude, Magnitude, Depth (km), Region, Mode, Map
        if len(cols) < 9:
            # skip incomplete row or footer
            continue
        yield {
            "Date": cols[0],
            "Time (utc)": cols[1],
            "Latitude": cols[2],
            "Longitude": cols[3],
            "Magnitude": cols[4],
            "Depth (km)": cols[5],
            "Region": cols[6],
            "Mode": cols[7],
            "Map": cols[8],
        }

def find_last_page(soup):
    """Find the maximum page number from pagination links in the page."""
    # Look for the “next page” nav, but better to scan all <a> in pagination for the highest number
    page_links = soup.select("a[href*='page=']")
    max_page = 1
    for a in page_links:
        href = a.get("href")
        if href:
            # extract query param page=
            try:
                part = href.split("page=")[-1]
                num = int(part.split("&")[0])
                if num > max_page:
                    max_page = num
            except ValueError:
                pass
    return max_page

def scrape_all(output_csv: str, base_url: str = ""):
    with requests.Session() as session:
        # optional headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Python scraper for NSMC events; +https://yourdomain.example)"
        })

        # determine how many pages
        first_soup = get_page(session, 1, base_url)
        last_page = find_last_page(first_soup)
        print(f"Detected {last_page} pages of events.")

        # open CSV and write header
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Date","Time (utc)","Latitude","Longitude","Magnitude","Depth (km)","Region","Mode","Map"])
            writer.writeheader()

            # iterate each page
            for page in range(1, last_page + 1):
                print(f"Scraping page {page}/{last_page}")
                soup = get_page(session, page, base_url)
                for row in parse_table(soup):
                    writer.writerow(row)
                # polite pause
                time.sleep(0.5)
