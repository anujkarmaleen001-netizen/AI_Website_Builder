"""
Sitemap Parser Module
Parses XML sitemaps and extracts URLs with priorities
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from .utils import make_absolute_url, is_valid_url


class SitemapParser:
    """
    Parses XML sitemaps and extracts URLs
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraperBot/1.0)'
        })
    
    def parse(self, sitemap_url: str, max_urls: int = 50) -> List[Dict]:
        """
        Parse sitemap and return list of URLs with metadata
        """
        urls = []
        
        try:
            # Fetch sitemap
            response = self.session.get(sitemap_url, timeout=self.timeout)
            if response.status_code != 200:
                return urls
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle sitemap index
            if 'sitemapindex' in root.tag:
                urls = self._parse_sitemap_index(root, max_urls)
            else:
                urls = self._parse_urlset(root, max_urls)
            
        except Exception as e:
            print(f"[ERROR] Failed to parse sitemap {sitemap_url}: {str(e)}")
        
        return urls
    
    def _parse_sitemap_index(self, root: ET.Element, max_urls: int) -> List[Dict]:
        """
        Parse sitemap index and fetch child sitemaps
        """
        all_urls = []
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Extract child sitemap URLs
        sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
        
        for sitemap in sitemaps:
            if len(all_urls) >= max_urls:
                break
            
            sitemap_url = sitemap.text
            if sitemap_url:
                # Recursively parse child sitemap
                child_urls = self.parse(sitemap_url, max_urls - len(all_urls))
                all_urls.extend(child_urls)
        
        return all_urls
    
    def _parse_urlset(self, root: ET.Element, max_urls: int) -> List[Dict]:
        """
        Parse URL set from sitemap
        """
        urls = []
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Extract URLs
        url_elements = root.findall('.//ns:url', namespace)
        
        for url_elem in url_elements[:max_urls]:
            loc = url_elem.find('ns:loc', namespace)
            if loc is not None and loc.text:
                url_data = {
                    'url': loc.text,
                    'priority': self._get_priority(url_elem, namespace),
                    'lastmod': self._get_lastmod(url_elem, namespace)
                }
                urls.append(url_data)
        
        return urls
    
    def _get_priority(self, url_elem: ET.Element, namespace: dict) -> float:
        """
        Extract priority from URL element
        """
        priority = url_elem.find('ns:priority', namespace)
        if priority is not None and priority.text:
            try:
                return float(priority.text)
            except:
                pass
        return 0.5  # Default priority
    
    def _get_lastmod(self, url_elem: ET.Element, namespace: dict) -> Optional[str]:
        """
        Extract last modification date
        """
        lastmod = url_elem.find('ns:lastmod', namespace)
        if lastmod is not None:
            return lastmod.text
        return None
    
    def discover_and_parse(self, base_url: str, sitemap_locations: List[str], max_urls: int = 50) -> List[Dict]:
        """
        Try multiple sitemap locations and parse the first one that works
        """
        all_urls = []
        
        for sitemap_url in sitemap_locations:
            print(f"[INFO] Trying sitemap: {sitemap_url}")
            urls = self.parse(sitemap_url, max_urls)
            
            if urls:
                print(f"[OK] Found {len(urls)} URLs in sitemap")
                all_urls.extend(urls)
                if len(all_urls) >= max_urls:
                    break
        
        # Sort by priority (higher first)
        all_urls.sort(key=lambda x: x.get('priority', 0.5), reverse=True)
        
        return all_urls[:max_urls]
    
    def categorize_urls(self, urls: List[Dict]) -> Dict[str, List[str]]:
        """
        Categorize URLs by type (homepage, pages, products, posts)
        """
        categories = {
            'homepage': [],
            'pages': [],
            'products': [],
            'posts': [],
            'other': []
        }
        
        for url_data in urls:
            url = url_data['url']
            url_lower = url.lower()
            
            # Homepage
            if url.rstrip('/').count('/') == 2:  # Only domain
                categories['homepage'].append(url)
            # Products
            elif '/product/' in url_lower or '/products/' in url_lower or '/shop/' in url_lower:
                categories['products'].append(url)
            # Blog posts
            elif '/blog/' in url_lower or '/post/' in url_lower or '/article/' in url_lower:
                categories['posts'].append(url)
            # Pages
            elif '/' in url_lower:
                categories['pages'].append(url)
            else:
                categories['other'].append(url)
        
        return categories
