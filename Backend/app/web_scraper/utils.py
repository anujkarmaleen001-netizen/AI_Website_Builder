"""
Utility functions for the scraper
"""
import re
from urllib.parse import urlparse, urljoin
from typing import Optional
from collections import Counter


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing trailing slashes and fragments
    """
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized


def get_base_url(url: str) -> str:
    """
    Extract base URL (scheme + netloc)
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def make_absolute_url(base_url: str, relative_url: str) -> str:
    """
    Convert relative URL to absolute URL
    """
    return urljoin(base_url, relative_url)


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def sanitize_filename(name: str) -> str:
    """
    Remove invalid characters from filename
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def get_color_frequency(colors: list) -> list:
    """
    Sort colors by frequency
    """
    counter = Counter(colors)
    return [color for color, count in counter.most_common()]


def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
