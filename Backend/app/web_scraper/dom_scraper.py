"""
DOM Scraper Module
Extracts content and structure from web pages
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from .utils import clean_text, make_absolute_url


class DOMScraper:
    """
    Scrapes and extracts content from web pages
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraperBot/1.0)'
        })
    
    def scrape(self, url: str) -> Dict:
        """
        Scrape a URL and extract content
        """
        result = {
            'url': url,
            'title': None,
            'meta_description': None,
            'headings': {},
            'navigation': {},
            'sections': [],
            'text_content': '',
            'error': None
        }
        
        try:
            # Fetch page
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result['error'] = f"HTTP {response.status_code}"
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                result['title'] = title_tag.get_text().strip()
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                result['meta_description'] = meta_desc.get('content', '').strip()
            
            # Extract headings
            result['headings'] = self._extract_headings(soup)
            
            # Extract navigation
            result['navigation'] = self._extract_navigation(soup)
            
            # Extract main text content
            result['text_content'] = self._extract_text_content(soup)
            
            # Extract sections
            result['sections'] = self._extract_sections(soup)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Extract all heading tags (H1-H6)
        """
        headings = {}
        
        for level in range(1, 7):
            tag = f'h{level}'
            found = soup.find_all(tag)
            if found:
                headings[tag] = [clean_text(h.get_text()) for h in found if h.get_text().strip()]
        
        return headings
    
    def _extract_navigation(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Extract navigation menus
        """
        navigation = {
            'header': [],
            'footer': []
        }
        
        # Header navigation
        header = soup.find('header') or soup.find('nav')
        if header:
            links = header.find_all('a')
            navigation['header'] = [clean_text(link.get_text()) for link in links if link.get_text().strip()]
        
        # Footer navigation
        footer = soup.find('footer')
        if footer:
            links = footer.find_all('a')
            navigation['footer'] = [clean_text(link.get_text()) for link in links if link.get_text().strip()]
        
        return navigation
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main text content from page
        """
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        return clean_text(text)[:1000]  # First 1000 chars
   
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract major sections from the page
        """
        sections = []
        
        # Look for section tags
        section_tags = soup.find_all(['section', 'article', 'main'])
        
        for i, section in enumerate(section_tags[:5]):  # Limit to 5 sections
            section_data = {
                'index': i,
                'tag': section.name,
                'text': clean_text(section.get_text())[:200],  # First 200 chars
                'has_images': bool(section.find('img')),
                'heading': None
            }
            
            # Try to find section heading
            heading = section.find(['h1', 'h2', 'h3'])
            if heading:
                section_data['heading'] = clean_text(heading.get_text())
            
            sections.append(section_data)
        
        return sections
    
    def scrape_multiple(self, urls: List[str], max_pages: int = 10) -> List[Dict]:
        """
        Scrape multiple URLs
        """
        results = []
        
        for i, url in enumerate(urls[:max_pages]):
            print(f"[INFO] Scraping {i+1}/{min(len(urls), max_pages)}: {url}")
            result = self.scrape(url)
            results.append(result)
        
        return results
