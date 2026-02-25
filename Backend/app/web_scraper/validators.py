"""
URL Validation and robots.txt Checker
"""
import requests
from urllib.parse import urlparse, urljoin
from typing import Optional, Tuple
from .utils import is_valid_url, get_base_url


class URLValidator:
    """
    Validates URLs and checks robots.txt compliance
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraperBot/1.0)'
        })
    
    def validate(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL and return (is_valid, error_message)
        """
        # Check URL format
        if not is_valid_url(url):
            return False, "Invalid URL format"
        
        # Check if URL is accessible
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code >= 400:
                return False, f"URL returned status code {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        return True, None
    
    def check_robots_txt(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL is allowed by robots.txt
        Returns (is_allowed, robots_txt_content)
        """
        base_url = get_base_url(url)
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                robots_txt = response.text
                
                # Simple robots.txt parsing
                # Look for User-agent: * and Disallow rules
                lines = robots_txt.split('\n')
                applies_to_all = False
                
                for line in lines:
                    line = line.strip()
                    
                    if line.lower().startswith('user-agent:'):
                        if '*' in line:
                            applies_to_all = True
                        else:
                            applies_to_all = False
                    
                    if applies_to_all and line.lower().startswith('disallow:'):
                        disallowed_path = line.split(':', 1)[1].strip()
                        if disallowed_path and disallowed_path != '/':
                            path = urlparse(url).path
                            if path.startswith(disallowed_path):
                                return False, robots_txt
                
                return True, robots_txt
            else:
                # No robots.txt found - assume allowed
                return True, None
        except Exception:
            # If robots.txt can't be fetched, assume allowed
            return True, None
    
    def full_validation(self, url: str) -> dict:
        """
        Perform full validation including URL check and robots.txt
        """
        result = {
            'url': url,
            'is_valid': False,
            'is_allowed': False,
            'error': None,
            'robots_txt': None
        }
        
        # Validate URL
        is_valid, error = self.validate(url)
        result['is_valid'] = is_valid
        result['error'] = error
        
        if not is_valid:
            return result
        
        # Check robots.txt
        is_allowed, robots_txt = self.check_robots_txt(url)
        result['is_allowed'] = is_allowed
        result['robots_txt'] = robots_txt
        
        return result
