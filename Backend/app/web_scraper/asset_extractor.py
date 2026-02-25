"""
Asset Extractor Module
Extracts images, colors, fonts, and other assets from web pages
"""
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from collections import Counter
from .utils import make_absolute_url, get_base_url, clean_text


class AssetExtractor:
    """
    Extracts assets (images, colors, fonts) from web pages
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraperBot/1.0)'
        })
    
    def extract(self, url: str) -> Dict:
        """
        Extract all assets from a URL
        """
        result = {
            'url': url,
            'logo': None,
            'favicon': None,
            'hero_images': [],
            'colors': [],
            'fonts': [],
            'stylesheets': [],
            'error': None
        }
        
        try:
            # Fetch page
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result['error'] = f"HTTP {response.status_code}"
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = get_base_url(url)
            
            # Extract logo
            result['logo'] = self._extract_logo(soup, base_url)
            
            # Extract favicon
            result['favicon'] = self._extract_favicon(soup, base_url)
            
            # Extract hero/banner images
            result['hero_images'] = self._extract_hero_images(soup, base_url)
            
            # Extract colors
            result['colors'] = self._extract_colors(soup, response.text)
            
            # Extract fonts
            result['fonts'] = self._extract_fonts(soup, response.text)
            
            # Extract stylesheets
            result['stylesheets'] = self._extract_stylesheets(soup, base_url)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_logo(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Try to find the logo image
        """
        # Look for common logo selectors
        logo_selectors = [
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            'img[alt*="logo" i]',
            'a.logo img',
            'div.logo img',
            'header img:first-of-type'
        ]
        
        for selector in logo_selectors:
            try:
                logo = soup.select_one(selector)
                if logo and logo.get('src'):
                    return make_absolute_url(base_url, logo['src'])
            except:
                continue
        
        return None
    
    def _extract_favicon(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Extract favicon URL
        """
        # Try link tags
        favicon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if favicon_link and favicon_link.get('href'):
            return make_absolute_url(base_url, favicon_link['href'])
        
        # Fallback to /favicon.ico
        return make_absolute_url(base_url, '/favicon.ico')
    
    def _extract_hero_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract hero/banner images (large images in the first viewport)
        """
        hero_images = []
        
        # Look for hero sections
        hero_sections = soup.select('section.hero, div.hero, header.hero, div.banner')
        
        for section in hero_sections[:3]:  # Max 3 hero sections
            images = section.find_all('img')
            for img in images:
                if img.get('src'):
                    img_url = make_absolute_url(base_url, img['src'])
                    if img_url not in hero_images:
                        hero_images.append(img_url)
        
        # If no hero sections, take first few large images
        if not hero_images:
            all_images = soup.find_all('img')
            for img in all_images[:5]:
                if img.get('src'):
                    img_url = make_absolute_url(base_url, img['src'])
                    hero_images.append(img_url)
        
        return hero_images[:5]  # Limit to 5
    
    def _extract_colors(self, soup: BeautifulSoup, html: str) -> List[str]:
        """
        Extract colors from inline styles and CSS
        """
        colors = []
        
        # Extract from inline styles
        for elem in soup.find_all(style=True):
            style = elem['style']
            elem_colors = self._extract_colors_from_css(style)
            colors.extend(elem_colors)
        
        # Extract from style tags
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                style_colors = self._extract_colors_from_css(style_tag.string)
                colors.extend(style_colors)
        
        # Count frequency and return top colors
        if colors:
            color_freq = Counter(colors)
            top_colors = [color for color, count in color_freq.most_common(10)]
            return top_colors
        
        return []
    
    def _extract_colors_from_css(self, css_text: str) -> List[str]:
        """
        Extract color values from CSS text
        """
        colors = []
        
        # Extract hex colors
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}', css_text)
        colors.extend(hex_colors)
        
        # Extract rgb/rgba colors
        rgb_colors = re.findall(r'rgba?\([^)]+\)', css_text)
        colors.extend(rgb_colors)
        
        # Extract hsl/hsla colors
        hsl_colors = re.findall(r'hsla?\([^)]+\)', css_text)
        colors.extend(hsl_colors)
        
        return colors
    
    def _extract_fonts(self, soup: BeautifulSoup, html: str) -> List[str]:
        """
        Extract font families used on the page
        """
        fonts = set()
        
        # Extract from Google Fonts links
        font_links = soup.find_all('link', href=lambda x: x and 'fonts.googleapis.com' in x)
        for link in font_links:
            href = link.get('href', '')
            # Extract family parameter
            match = re.search(r'family=([^&:]+)', href)
            if match:
                font_name = match.group(1).replace('+', ' ')
                fonts.add(font_name)
        
        # Extract from @font-face in style tags
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                font_faces = re.findall(r"font-family:\s*['\"]([^'\"]+)['\"]", style_tag.string)
                fonts.update(font_faces)
        
        # Extract from inline styles
        for elem in soup.find_all(style=True):
            style = elem['style']
            font_family = re.findall(r"font-family:\s*['\"]?([^;'\"]+)['\"]?", style)
            fonts.update([f.strip() for f in font_family])
        
        return list(fonts)[:10]  # Top 10 fonts
    
    def _extract_stylesheets(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract external stylesheet URLs
        """
        stylesheets = []
        
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                stylesheet_url = make_absolute_url(base_url, href)
                stylesheets.append(stylesheet_url)
        
        return stylesheets
