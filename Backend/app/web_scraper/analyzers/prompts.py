"""
LLM Prompts for Website Analysis
"""

STRUCTURE_ANALYSIS_PROMPT = """You are a website structure analyst. Given scraped content from a reference website, analyze and extract a normalized structure that can be replicated.

INPUT DATA:
{input_data}

TASK: Create a normalized site structure that identifies page types, sections, and navigation patterns.

OUTPUT: Return ONLY valid JSON in this exact format:
{{
  "recommended_pages": [
    {{
      "page_type": "homepage|about|products|services|contact|blog|custom",
      "suggested_name": "Page name",
      "sections_detected": ["hero", "features", "testimonials"],
      "content_summary": "Brief description of page purpose",
      "priority": 1-10
    }}
  ],
  "navigation_structure": {{
    "header": [{{"label": "Link text", "type": "page|dropdown|external"}}],
    "footer": [{{"label": "Link text", "category": "company|legal|social"}}]
  }},
  "content_patterns": ["pattern description 1", "pattern description 2"]
}}

Be concise and focus on actionable structure insights."""

DESIGN_ANALYSIS_PROMPT = """You are a design system analyst. Extract design tokens and patterns from scraped website data.

INPUT DATA:
Colors found: {colors}
Fonts detected: {fonts}
Platform: {platform}

TASK: Analyze the design system and extract reusable tokens.

OUTPUT: Return ONLY valid JSON in this exact format:
{{
  "color_palette": {{
    "primary": "#hex (most frequent brand color)",
    "secondary": "#hex (supporting color)",
    "accent": "#hex (call-to-action color)",
    "background": "#hex (main background)",
    "text": "#hex (main text color)"
  }},
  "typography": {{
    "heading_font": "Font Family or 'sans-serif'",
    "body_font": "Font Family or 'sans-serif'",
    "font_scale": "modern|traditional"
  }},
  "design_style": ["modern", "minimal", "bold", "elegant", "playful"],
  "component_patterns": {{
    "buttons": "style description (rounded, flat, shadows, etc.)",
    "cards": "style description (borders, shadows, spacing)",
    "spacing": "tight|comfortable|spacious"
  }}
}}

Base your analysis on the actual data provided."""

CONTENT_GENERATION_PROMPT = """You are a content strategist. Generate NEW, ORIGINAL content for a user's business based on structural patterns from a reference site.

REFERENCE STRUCTURE:
{reference_structure}

USER BUSINESS:
Business Name: {business_name}
Industry: {industry}
Description: {description}
Brand Voice: {brand_voice}

CRITICAL RULES:
1. NEVER copy content directly from the reference
2. Use the reference ONLY to understand structure and flow
3. Generate completely original content for the user's business
4. Match the brand voice and industry

OUTPUT: Return ONLY valid JSON in this exact format:
{{
  "hero_section": {{
    "headline": "Compelling headline for {business_name}",
    "subheadline": "Supporting text that explains value",
    "cta_text": "Primary call-to-action"
  }},
  "value_propositions": [
    "Benefit 1 specific to {industry}",
    "Benefit 2 specific to {industry}",
    "Benefit 3 specific to {industry}"
  ],
  "section_suggestions": [
    {{
      "section_type": "features|testimonials|pricing|faq",
      "content_outline": "Brief description of what this section should contain"
    }}
  ]
}}

Create authentic, compelling content that resonates with the target audience."""
