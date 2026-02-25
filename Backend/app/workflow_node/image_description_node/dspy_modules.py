# Third-party imports
import dspy

from .signature import ImageDescriptionSignature
# Import LLM configurations from config module
from app.config import planning_llm


class ImageDescriptionGenerator(dspy.Module):
    """Generate targeted image descriptions for specific sections."""
    
    def __init__(self):
        super().__init__()
        # Import planning_llm from config - image descriptions are short - imported at top
        self.predict = dspy.Predict(ImageDescriptionSignature)
        # Configure this specific predict to use planning_llm (descriptions are short prompts)
        self.predict.lm = planning_llm
    
    
    def forward(self, plan: str, section_name: str, page_name: str, business_description: str):
        system_rules = """You are a professional visual designer creating DALL-E 3 prompts for website background images.

CRITICAL: These images are BACKGROUND/DECORATIVE ONLY. All text, UI elements, and interactive components will be added via HTML/CSS.

YOUR TASK:
- Analyze the website plan, section purpose, and business description
- Create a DALL-E 3 prompt for a background image that enhances the section
- The image should align with the website's theme and styling strategy
- Focus on composition, mood, color harmony, and professional aesthetics

STRICT RULES (MUST FOLLOW):
- NO text, letters, numbers, words, quotes, headings, labels
- NO UI elements, cards, buttons, icons with text
- NO testimonial cards, review boxes, star ratings
- NO dashboards, mockups, screenshots, or website previews
- NO speech bubbles, quotes, or text overlays

VISUAL REQUIREMENTS:
- Professional, modern aesthetic suitable for business websites
- Clean composition with breathing room for overlay content
- Soft, flattering lighting (avoid harsh shadows)
- Minimal to moderate contrast (avoid extreme darks/lights)
- Color palette should complement the website's styling strategy
- Subtle depth and dimension (gradients, layering)
- Images should feel premium and polished

OUTPUT: A detailed DALL-E 3 prompt (2-4 sentences) describing the visual composition, mood, colors, and style."""
        
        result = self.predict(
            plan=plan,
            section_name=section_name,
            page_name=page_name,
            business_description=f"{system_rules}\n\nBusiness: {business_description}"
        )
        return result.image_description.strip()
