"""
Main Scraper Pipeline
Orchestrates the entire scraping process
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict
from .validators import URLValidator
from .platform_detector import PlatformDetector
from .sitemap_parser import SitemapParser
from .dom_scraper import DOMScraper
from .asset_extractor import AssetExtractor
from .utils import get_base_url


class ScraperPipeline:
    """
    Main scraping pipeline that orchestrates all components
    """
    
    def __init__(self, output_dir: str = 'scraped_data'):
        self.output_dir = output_dir
        self.validator = URLValidator()
        self.platform_detector = PlatformDetector()
        self.sitemap_parser = SitemapParser()
        self.dom_scraper = DOMScraper()
        self.asset_extractor = AssetExtractor()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def run(self, url: str, max_pages: int = 10) -> Dict:
        """
        Run the complete scraping pipeline
        """
        print(f"\n{'='*60}")
        print(f"STARTING SCRAPE FOR: {url}")
        print(f"{'='*60}\n")
        
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'validation': {},
            'platform': {},
            'sitemap': {},
            'pages': [],
            'assets': {},
            'summary': {}
        }
        
        # Step 1: Validate URL
        print("[STEP 1] Validating URL...")
        validation = self.validator.full_validation(url)
        result['validation'] = validation
        
        if not validation['is_valid']:
            print(f"[ERROR] URL validation failed: {validation['error']}")
            return result
        
        if not validation['is_allowed']:
            print("[WARNING] robots.txt disallows scraping this URL")
            print("Continuing anyway for demonstration purposes...")
        
        print("[OK] URL is valid and accessible\n")
        
        # Step 2: Detect Platform
        print("[STEP 2] Detecting platform...")
        platform = self.platform_detector.detect(url)
        result['platform'] = platform
        print(f"[OK] Platform detected: {platform['platform_name']} (confidence: {platform['confidence']}%)")
        if platform['indicators']:
            for indicator in platform['indicators']:
                print(f"  - {indicator}")
        print()
        
        # Step 3: Parse Sitemap
        print("[STEP 3] Parsing sitemap...")
        base_url = get_base_url(url)
        sitemap_locations = self.platform_detector.get_sitemap_locations(platform['platform'], base_url)
        
        sitemap_urls = self.sitemap_parser.discover_and_parse(base_url, sitemap_locations, max_pages)
        
        if sitemap_urls:
            categories = self.sitemap_parser.categorize_urls(sitemap_urls)
            result['sitemap'] = {
                'urls': sitemap_urls,
                'categories': categories,
                'total_found': len(sitemap_urls)
            }
            print(f"[OK] Found {len(sitemap_urls)} URLs from sitemap\n")
        else:
            print("[WARNING] No sitemap found, will scrape homepage only\n")
            sitemap_urls = [{'url': url, 'priority': 1.0}]
        
        # Step 4: Scrape Pages
        print(f"[STEP 4] Scraping content from {min(len(sitemap_urls), max_pages)} pages...")
        urls_to_scrape = [item['url'] for item in sitemap_urls[:max_pages]]
        scraped_pages = self.dom_scraper.scrape_multiple(urls_to_scrape, max_pages)
        result['pages'] = scraped_pages
        print(f"[OK] Scraped {len(scraped_pages)} pages\n")
        
        # Step 5: Extract Assets
        print("[STEP 5] Extracting assets (images, colors, fonts)...")
        assets = self.asset_extractor.extract(url)
        result['assets'] = assets
        
        if assets['colors']:
            print(f"[OK] Found {len(assets['colors'])} colors")
        if assets['fonts']:
            print(f"[OK] Found {len(assets['fonts'])} fonts")
        if assets['logo']:
            print(f"[OK] Logo: {assets['logo']}")
        print()
        
        # Step 6: Generate Summary
        print("[STEP 6] Generating summary...")
        result['summary'] = self._generate_summary(result)
        
        # Step 7: Save Results
        output_file = self._save_results(result)
        print(f"\n[SUCCESS] Results saved to: {output_file}")
        print(f"\n{'='*60}\n")
        
        return result
    
    def _generate_summary(self, result: Dict) -> Dict:
        """
        Generate a summary of the scraping results
        """
        summary = {
            'platform': result['platform'].get('platform_name', 'Unknown'),
            'total_pages_scraped': len(result['pages']),
            'total_urls_found': result['sitemap'].get('total_found', 0),
            'colors_found': len(result['assets'].get('colors', [])),
            'fonts_found': len(result['assets'].get('fonts', [])),
            'has_logo': bool(result['assets'].get('logo')),
            'has_favicon': bool(result['assets'].get('favicon'))
        }
        
        # Get homepage title
        if result['pages']:
            homepage = result['pages'][0]
            summary['site_title'] = homepage.get('title', 'Unknown')
            summary['meta_description'] = homepage.get('meta_description', 'None')
        
        return summary
    
    def _save_results(self, result: Dict) -> str:
        """
        Save results to JSON file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"scraped_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return filepath


def main():
    """
    CLI entry point
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m Scraper.main <url> [max_pages]")
        print("Example: python -m Scraper.main https://example.com 10")
        sys.exit(1)
    
    url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    pipeline = ScraperPipeline()
    pipeline.run(url, max_pages)


if __name__ == '__main__':
    main()
