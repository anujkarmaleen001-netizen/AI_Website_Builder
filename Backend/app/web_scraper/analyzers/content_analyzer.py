"""
Content Analyzer
Generates original content based on reference patterns
"""
import json
from typing import Dict
from .prompts import CONTENT_GENERATION_PROMPT


class ContentAnalyzer:
    """
    Generates original content based on reference website patterns
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def analyze(self, scraped_data: Dict, user_info: Dict) -> Dict:
        """
        Generate original content for user's business
        
        Args:
            scraped_data: Scraped website data
            user_info: Dictionary with business_name, industry, description, brand_voice
        """
        print("[INFO] Generating original content...")
        
        # Prepare reference structure
        reference_structure = self._extract_reference_structure(scraped_data)
        
        # Extract user info
        business_name = user_info.get('business_name', 'Your Business')
        industry = user_info.get('industry', 'General')
        description = user_info.get('description', '')
        brand_voice = user_info.get('brand_voice', 'Professional and friendly')
        
        # Create prompt
        prompt = CONTENT_GENERATION_PROMPT.format(
            reference_structure=json.dumps(reference_structure, indent=2),
            business_name=business_name,
            industry=industry,
            description=description,
            brand_voice=brand_voice
        )
        
        # Get LLM to generate content
        result = self.llm.generate_content(prompt)
        
        if 'error' in result:
            print(f"[ERROR] Content generation failed: {result['error']}")
            return self._fallback_content(business_name, industry)
        
        print(f"[OK] Generated original content")
        return result
    
    def _extract_reference_structure(self, scraped_data: Dict) -> Dict:
        """
        Extract content structure patterns from reference site
        """
        structure = {
            "page_types": [],
            "common_sections": [],
            "messaging_patterns": []
        }
        
        pages = scraped_data.get('pages', [])
        
        if pages:
            homepage = pages[0]
            
            # Extract headings as messaging patterns
            headings = homepage.get('headings', {})
            h1_list = headings.get('h1', [])
            h2_list = headings.get('h2', [])
            
            structure['messaging_patterns'] = {
                "main_headlines": h1_list[:2],
                "section_titles": h2_list[:5]
            }
            
            # Extract sections
            sections = homepage.get('sections', [])
            structure['common_sections'] = [s.get('tag', 'section') for s in sections[:5]]
        
        return structure
    
    def _fallback_content(self, business_name: str, industry: str) -> Dict:
        """
        Fallback generic content if LLM fails
        """
        return {
            "hero_section": {
                "headline": f"Welcome to {business_name}",
                "subheadline": f"We provide exceptional {industry} solutions",
                "cta_text": "Get Started"
            },
            "value_propositions": [
                f"Quality {industry} services",
                "Customer-focused approach",
                "Proven track record"
            ],
            "section_suggestions": [
                {
                    "section_type": "features",
                    "content_outline": f"Highlight key benefits of your {industry} offerings"
                },
                {
                    "section_type": "testimonials",
                    "content_outline": "Showcase customer success stories"
                }
            ]
        }
