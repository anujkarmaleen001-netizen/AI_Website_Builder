"""
Platform Detection Module
Detects the platform/CMS used by a website (WordPress, Shopify, WooCommerce, etc.)
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from .utils import get_base_url, make_absolute_url


class PlatformDetector:
    """
    Detects the platform/CMS of a website
    """
    
    PLATFORMS = {
        'wordpress': 'WordPress',
        'shopify': 'Shopify',
        'woocommerce': 'WooCommerce',
        'wix': 'Wix',
        'squarespace': 'Squarespace',
        'webflow': 'Webflow',
        'generic': 'Generic'
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraperBot/1.0)'
        })
    
    def detect(self, url: str) -> Dict:
        """
        Detect the platform of a website
        Returns dict with platform info
        """
        result = {
            'platform': 'generic',
            'platform_name': 'Generic',
            'confidence': 0,
            'indicators': []
        }
        
        try:
            # Fetch the homepage
            response = self.session.get(url, timeout=self.timeout)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            base_url = get_base_url(url)
            
            # Check for WordPress
            wp_score, wp_indicators = self._check_wordpress(soup, html_content, base_url)
            if wp_score > result['confidence']:
                result['platform'] = 'wordpress'
                result['platform_name'] = self.PLATFORMS['wordpress']
                result['confidence'] = wp_score
                result['indicators'] = wp_indicators
            
            # Check for Shopify
            shopify_score, shopify_indicators = self._check_shopify(soup, html_content, base_url)
            if shopify_score > result['confidence']:
                result['platform'] = 'shopify'
                result['platform_name'] = self.PLATFORMS['shopify']
                result['confidence'] = shopify_score
                result['indicators'] = shopify_indicators
            
            # Check for WooCommerce (must check after WordPress)
            if result['platform'] == 'wordpress':
                wc_score, wc_indicators = self._check_woocommerce(soup, html_content)
                if wc_score > 50:
                    result['platform'] = 'woocommerce'
                    result['platform_name'] = self.PLATFORMS['woocommerce']
                    result['indicators'].extend(wc_indicators)
            
            # Check other platforms
            for platform_key in ['wix', 'squarespace', 'webflow']:
                score, indicators = self._check_other_platform(soup, html_content, platform_key)
                if score > result['confidence']:
                    result['platform'] = platform_key
                    result['platform_name'] = self.PLATFORMS[platform_key]
                    result['confidence'] = score
                    result['indicators'] = indicators
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_wordpress(self, soup: BeautifulSoup, html: str, base_url: str) -> tuple:
        """
        Check for WordPress indicators
        Returns (confidence_score, indicators_list)
        """
        score = 0
        indicators = []
        
        # Check meta generator tag
        meta_gen = soup.find('meta', attrs={'name': 'generator'})
        if meta_gen and 'wordpress' in meta_gen.get('content', '').lower():
            score += 40
            indicators.append('WordPress meta generator tag')
        
        # Check for wp-content paths
        if '/wp-content/' in html:
            score += 25
            indicators.append('/wp-content/ paths found')
        
        # Check for wp-includes
        if '/wp-includes/' in html:
            score += 15
            indicators.append('/wp-includes/ paths found')
        
        # Try to access wp-json API
        try:
            wp_json_url = make_absolute_url(base_url, '/wp-json/')
            response = self.session.head(wp_json_url, timeout=5)
            if response.status_code == 200:
                score += 20
                indicators.append('wp-json API accessible')
        except:
            pass
        
        return score, indicators
    
    def _check_shopify(self, soup: BeautifulSoup, html: str, base_url: str) -> tuple:
        """
        Check for Shopify indicators
        """
        score = 0
        indicators = []
        
        # Check for Shopify CDN
        if 'cdn.shopify.com' in html:
            score += 50
            indicators.append('Shopify CDN found')
        
        # Check for Shopify theme
        if 'Shopify.theme' in html or 'Shopify.shop' in html:
            score += 30
            indicators.append('Shopify JavaScript found')
        
        # Try to access cart.js
        try:
            cart_url = make_absolute_url(base_url, '/cart.js')
            response = self.session.head(cart_url, timeout=5)
            if response.status_code == 200:
                score += 20
                indicators.append('/cart.js endpoint accessible')
        except:
            pass
        
        return score, indicators
    
    def _check_woocommerce(self, soup: BeautifulSoup, html: str) -> tuple:
        """
        Check for WooCommerce indicators (requires WordPress)
        """
        score = 0
        indicators = []
        
        # Check for WooCommerce paths
        if '/product/' in html or '/shop/' in html:
            score += 30
            indicators.append('WooCommerce paths found')
        
        # Check for woocommerce classes
        if 'woocommerce' in html.lower():
            score += 40
            indicators.append('WooCommerce classes/IDs found')
        
        # Check for product schema
        if 'schema.org/Product' in html:
            score += 20
            indicators.append('Product schema markup found')
        
        return score, indicators
    
    def _check_other_platform(self, soup: BeautifulSoup, html: str, platform: str) -> tuple:
        """
        Check for other platforms (Wix, Squarespace, Webflow)
        """
        score = 0
        indicators = []
        
        platform_signatures = {
            'wix': ['wix.com', 'wixstatic.com', 'X-Wix-'],
            'squarespace': ['squarespace.com', 'sqsp.com', 'squarespace-cdn'],
            'webflow': ['webflow.com', 'webflow.io', 'data-wf-']
        }
        
        if platform in platform_signatures:
            for signature in platform_signatures[platform]:
                if signature in html:
                    score += 30
                    indicators.append(f'{signature} found')
        
        return score, indicators
    
    def get_sitemap_locations(self, platform: str, base_url: str) -> list:
        """
        Get likely sitemap locations based on platform
        """
        sitemaps = []
        
        if platform == 'wordpress' or platform == 'woocommerce':
            sitemaps = [
                '/wp-sitemap.xml',
                '/sitemap_index.xml',
                '/sitemap.xml'
            ]
        elif platform == 'shopify':
            sitemaps = [
                '/sitemap.xml',
                '/sitemap_products_1.xml',
                '/sitemap_pages_1.xml',
                '/sitemap_collections_1.xml'
            ]
        else:
            sitemaps = [
                '/sitemap.xml',
                '/sitemap_index.xml'
            ]
        
        return [make_absolute_url(base_url, s) for s in sitemaps]
