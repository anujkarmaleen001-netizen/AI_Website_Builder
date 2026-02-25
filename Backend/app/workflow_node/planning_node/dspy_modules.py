# Standard library imports
import json
from typing import Dict, Optional

# Third-party imports
import dspy

from .signature import WebsitePlannerSignature
# Import LLM configurations from config module (used in various DSPy modules)
from app.config import planning_llm


class WebsitePlanner(dspy.Module):
    """Generate comprehensive website structure plan."""
    
    def __init__(self):
        super().__init__()
        # Import planning_llm from config and use it for this module - imported at top
        self.predict = dspy.Predict(WebsitePlannerSignature)
        # Configure this specific predict to use planning_llm
        self.predict.lm = planning_llm
    
    
    def forward(self, description: str, template_styling: Optional[Dict] = None):
        planning_instructions = """You are an expert website architect and UX designer.
        
Your task is to create a comprehensive, professional website structure plan based on the business description.

PLANNING STRATEGY - PRIORITIZE BUSINESS REQUIREMENTS:

**PRIMARY FOCUS: Business Requirements**
1. PAGES STRUCTURE - STRICT USER REQUIREMENTS:
   ⚠️ CRITICAL: If the business description explicitly specifies which pages are needed, YOU MUST create ONLY those pages.
   
   - Read the business description CAREFULLY for page requirements
   - If user says "I want pages: X, Y, Z" → Create ONLY pages X, Y, and Z
   - If user says "just home and blog" → Create ONLY home and blog pages
   - If user says "home, about, contact" → Create ONLY those 3 pages
   - DO NOT add extra pages unless the description explicitly requests them
   
   - Only use common pages as FALLBACK if user doesn't specify pages:
     * Common fallback: home (landing), about, features/services, contact
     * Business-specific fallback: portfolio, blog, FAQ, pricing, etc.
   
   - Each page should serve a clear business purpose
   - Define sections for each page that support business goals

2. SECTION PLANNING:
   - Hero: Main value proposition aligned with business goals, CTA
   - Features: Product/service highlights that address business needs
   - Testimonials: Social proof relevant to the business
   - CTA: Call-to-action sections that drive business objectives
   - Additional: Business-specific sections (FAQ, pricing, team, portfolio, etc.)

3. CONTENT STRUCTURE:
   - Plan content that serves business purposes
   - User journey that supports business goals
   - Business-specific features and functionality

**SECONDARY REFERENCE: Template Styling (if provided)**
4. DESIGN SYSTEM STRATEGY (Comprehensive Styling):
   - **Color Palette** (CRITICAL: Use ONLY hex codes, never generic names):
     - Choose primary brand color with dark and light variants (e.g., #3B82F6, #2563EB, #DBEAFE)
     - Choose secondary/accent color with variants (e.g., #8B5CF6, #7C3AED, #EDE9FE)
     - Define background colors: main background (#FFFFFF or dark), surface/card background (#F9FAFB)
     - Define text colors: primary text (#111827 or light), secondary/muted text (#6B7280)
     - Define border color (#E5E7EB)
     - Define status colors: success (#10B981), warning (#F59E0B), error (#EF4444)
     - **If template styling is provided**: Adapt template colors to business context
     - **If no template**: Choose colors based on business type:
       * Professional/Business: Blues, navies, grays
       * Creative/Agency: Purples, pinks, vibrant colors
       * Health/Wellness: Greens, teals, calming colors
       * Food/Restaurant: Warm colors, oranges, reds
       * Tech/SaaS: Blues, cyans, modern palettes
   
   - **Typography System**:
     - Select Google Fonts: heading font and body font (e.g., "Inter", "Poppins", "Playfair Display")
     - Define available font weights (e.g., ["400", "500", "600", "700"])
     - Create type scale with specific sizes:
       * h1: 3.5rem, h2: 2.5rem, h3: 2rem, h4: 1.5rem, h5: 1.25rem, h6: 1.125rem
       * body: 1rem, small: 0.875rem
     - Define line-heights: heading (1.2), body (1.6), relaxed (1.8)
     - **If template**: Use template fonts as reference
     - **If no template**: Choose fonts matching business tone (modern sans-serif, elegant serif, etc.)
   
   - **Spacing System**:
     - Base unit: "8px" (standard design system unit)
     - Spacing scale: ["4px", "8px", "16px", "24px", "32px", "48px", "64px", "96px"]
     - Container max width: "1200px" (adjust based on business type)
     - Section padding: vertical "80px", horizontal "24px"
     - Grid gap: "24px" for layouts
   
   - **Component Styles**:
     - Button style: "rounded" | "pill" | "sharp" (match business aesthetic)
     - Button sizes: ["sm", "md", "lg"]
     - Card style: "elevated" (shadow) | "outlined" (border) | "filled" (background)
     - Card border radius: e.g., "12px"
     - Input style: "outline" | "filled" | "underline"
     - Base border radius: e.g., "8px"
   
   - **Responsive Strategy**:
     - Breakpoints: mobile "768px", tablet "1024px", desktop "1200px"
     - Mobile-first approach: true
     - Mobile navigation: "hamburger" | "drawer" | "bottom_nav"
     - Mobile font scale: 0.9 (slightly smaller on mobile)
   
   - **Interactions & Animations**:
     - Transitions: "smooth" (300ms) | "snappy" (150ms) | "none"
     - Hover effects: true | false
     - Scroll animations: ["fade", "slide"] or []
     - Page transitions: "fade" | "slide" | "none"

5. IMAGE REQUIREMENTS:
   - Identify which sections need background/decorative images
   - Typically: hero, features, testimonials
   - Images should enhance, not distract

6. NAVIGATION:
   - Define clear navigation structure
   - Should include all main pages
   - Logical order for user journey

**BALANCE**: Generate a plan that serves business requirements FIRST, then applies comprehensive design system for professional execution.

⚠️ REMEMBER: Respect user-specified pages EXACTLY. Do not add pages they didn't ask for.
⚠️ CRITICAL: ALL colors must be valid hex codes (e.g., "#3B82F6"), NEVER use generic names like "blue" or "red".
⚠️ CRITICAL: The plan MUST include a "design_system" object (not "styling") with all components listed above.

OUTPUT FORMAT: Return ONLY valid JSON matching the structure specified in the signature.
Do not include any explanatory text, only the JSON object."""
        
        # Build description with template styling reference if available
        if template_styling:
            template_info = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMPLATE STYLING REFERENCE (Use as design guide):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{json.dumps(template_styling, indent=2)}

Use these styling patterns as a design reference while prioritizing business requirements above.
"""
            full_description = f"{planning_instructions}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nBUSINESS DESCRIPTION TO ANALYZE:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{description}\n{template_info}\nNow create an EXCEPTIONAL website plan that serves business needs while maintaining template design consistency."
        else:
            full_description = f"{planning_instructions}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nBUSINESS DESCRIPTION TO ANALYZE:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{description}\n\nNow create an EXCEPTIONAL website plan based on this business."
        
        result = self.predict(description=full_description)
        return result.plan.strip()
