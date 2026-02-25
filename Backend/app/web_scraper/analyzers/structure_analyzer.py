"""
Structure Analyzer
Extracts and normalizes website structure from scraped data
"""
import json
from typing import Dict
from .prompts import STRUCTURE_ANALYSIS_PROMPT


class StructureAnalyzer:
    """
    Analyzes scraped website data to extract normalized structure
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def analyze(self, scraped_data: Dict) -> Dict:
        """
        Analyze website structure and return recommendations
        """
        print("[INFO] Analyzing website structure...")
        
        # Prepare input data for LLM
        input_summary = self._prepare_input(scraped_data)
        
        # Create prompt
        prompt = STRUCTURE_ANALYSIS_PROMPT.format(input_data=input_summary)
        
        # Get LLM analysis
        result = self.llm.analyze_structure(prompt)
        
        if 'error' in result:
            print(f"[ERROR] Structure analysis failed: {result['error']}")
            return self._fallback_analysis(scraped_data)
        
        print(f"[OK] Identified {len(result.get('recommended_pages', []))} page types")
        return result
    
    def _prepare_input(self, scraped_data: Dict) -> str:
        """
        Prepare scraped data summary for LLM analysis
        """
        summary = {
            "platform": scraped_data.get('platform', {}).get('platform_name', 'Unknown'),
            "total_pages": len(scraped_data.get('pages', [])),
            "sitemap_categories": scraped_data.get('sitemap', {}).get('categories', {}),
            "pages_overview": []
        }
        
        # Add overview of each page
        for page in scraped_data.get('pages', [])[:10]:  # Limit to first 10 pages
            page_info = {
                "url": page.get('url', ''),
                "title": page.get('title', ''),
                "headings": {
                    "h1": page.get('headings', {}).get('h1', [])[:3],
                    "h2": page.get('headings', {}).get('h2', [])[:5]
                },
                "sections": len(page.get('sections', [])),
                "has_navigation": bool(page.get('navigation', {}).get('header'))
            }
            summary['pages_overview'].append(page_info)
        
        # Add navigation structure
        if scraped_data.get('pages') and len(scraped_data['pages']) > 0:
            homepage = scraped_data['pages'][0]
            nav = homepage.get('navigation', {})
            summary['navigation'] = {
                "header_links": nav.get('header', [])[:20],
                "footer_links": nav.get('footer', [])[:15]
            }
        
        return json.dumps(summary, indent=2)
    
    def _fallback_analysis(self, scraped_data: Dict) -> Dict:
        """
        Fallback basic analysis if LLM fails
        """
        pages = scraped_data.get('pages', [])
        sitemap_categories = scraped_data.get('sitemap', {}).get('categories', {})
        
        recommended_pages = []
        
        # Homepage
        if pages:
            recommended_pages.append({
                "page_type": "homepage",
                "suggested_name": "Home",
                "sections_detected": ["hero", "features"],
                "content_summary": "Main landing page",
                "priority": 10
            })
        
        # Products page if products detected
        if sitemap_categories.get('products'):
            recommended_pages.append({
                "page_type": "products",
                "suggested_name": "Products",
                "sections_detected": ["product_grid"],
                "content_summary": "Product catalog",
                "priority": 9
            })
        
        # Blog page if posts detected
        if sitemap_categories.get('posts'):
            recommended_pages.append({
                "page_type": "blog",
                "suggested_name": "Blog",
                "sections_detected": ["post_list"],
                "content_summary": "Blog posts",
                "priority": 7
            })
        
        return {
            "recommended_pages": recommended_pages,
            "navigation_structure": {
                "header": [],
                "footer": []
            },
            "content_patterns": ["Basic structure extracted"]
        }
