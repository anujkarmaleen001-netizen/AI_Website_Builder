"""
Design Analyzer  
Extracts design patterns, colors, and typography from scraped data
"""
import json
from typing import Dict, List
from collections import Counter
from .prompts import DESIGN_ANALYSIS_PROMPT


class DesignAnalyzer:
    """
    Analyzes scraped website data to extract design system
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def analyze(self, scraped_data: Dict) -> Dict:
        """
        Analyze design patterns and return design tokens
        """
        print("[INFO] Analyzing design patterns...")
        
        # Extract design data
        colors = scraped_data.get('assets', {}).get('colors', [])
        fonts = scraped_data.get('assets', {}).get('fonts', [])
        platform = scraped_data.get('platform', {}).get('platform_name', 'Unknown')
        
        # Create prompt
        prompt = DESIGN_ANALYSIS_PROMPT.format(
            colors=json.dumps(colors[:20]),  # Top 20 colors
            fonts=json.dumps(fonts),
            platform=platform
        )
        
        # Get LLM analysis
        result = self.llm.analyze_design(prompt)
        
        if 'error' in result:
            print(f"[ERROR] Design analysis failed: {result['error']}")
            return self._fallback_analysis(colors, fonts, platform)
        
        print(f"[OK] Extracted design system")
        return result
    
    def _fallback_analysis(self, colors: List[str], fonts: List[str], platform: str) -> Dict:
        """
        Fallback basic design analysis if LLM fails
        """
        # Simple color categorization
        color_palette = {
            "primary": colors[0] if colors else "#000000",
            "secondary": colors[1] if len(colors) > 1 else "#666666",
            "accent": colors[2] if len(colors) > 2 else "#0066cc",
            "background": "#ffffff",
            "text": "#000000"
        }
        
        # Simple typography
        typography = {
            "heading_font": fonts[0] if fonts else "sans-serif",
            "body_font": fonts[1] if len(fonts) > 1 else fonts[0] if fonts else "sans-serif",
            "font_scale": "modern"
        }
        
        # Platform-based style inference
        design_style = ["modern", "clean"]
        if platform.lower() == "shopify":
            design_style.append("e-commerce")
        elif platform.lower() == "wordpress":
            design_style.append("content-focused")
        
        return {
            "color_palette": color_palette,
            "typography": typography,
            "design_style": design_style,
            "component_patterns": {
                "buttons": "rounded, solid colors",
                "cards": "subtle shadows, clean borders",
                "spacing": "comfortable"
            }
        }
