"""
Planning node for website generation workflow.
Generates comprehensive website plan based on business requirements.
"""
import json
import logging
import re
from typing import Dict

from app.workflow_state import WorkflowState
from .dspy_modules import WebsitePlanner
from app.web_scraper_service import get_reference_context_for_planning

# Configure logging
logger = logging.getLogger(__name__)


def planning_node(state: WorkflowState) -> WorkflowState:
    """
    Step 1: Generate comprehensive website plan.
    PRIMARY: Analyze business requirements
    SECONDARY: Use reference site analysis for design inspiration (if available)
    BALANCE: Generate plan prioritizing business needs with reference design patterns
    """
    logger.info("Starting planning node...")
    
    try:
        # Idempotency check: Skip if plan exists and no revision requested
        if state.get("plan") and not state.get("plan_revision_requested"):
            logger.info("Plan already exists and no revision requested. Skipping planning node.")
            return state

        # PRIMARY: Use business_plan from gathering phase (with fallback to description)
        # The business_plan contains the analyzed and validated business requirements
        business_description = state.get("business_plan", state.get("description", ""))
        
        if state.get("business_plan"):
            logger.info("Using business_plan from gathering phase...")
            logger.info(f"Business plan preview: {business_description[:200]}...")
        else:
            logger.info("No business_plan found, falling back to raw description...")
            logger.info(f"Description preview: {business_description[:200]}...")
            
        # CRITICAL: Incorporate user feedback if revision requested
        plan_feedback = state.get("plan_feedback")
        if plan_feedback:
            logger.info(f"Incorporating user feedback into plan: {plan_feedback}")
            business_description += f"\n\nIMPORTANT: The user has requested changes to the previous plan. Please update the plan based on this feedback:\n[USER FEEDBACK]: {plan_feedback}"
        
        # SECONDARY: Inject reference site design patterns if available
        reference_analysis = state.get("reference_analysis")
        if reference_analysis and reference_analysis.get('status') in ('completed', 'partial'):
            reference_context = get_reference_context_for_planning(reference_analysis)
            if reference_context:
                logger.info(f"Injecting reference design context into planning ({len(reference_context)} chars)")
                business_description = f"{business_description}\n\n{reference_context}"
        else:
            logger.info("No reference analysis available - generating plan based on business requirements only")
        
        # Template styling / CSS theme
        template_styling = None
        css_theme = None
        
        # BALANCE: Generate plan prioritizing business requirements, using template styling as reference
        planner = WebsitePlanner()
        
        # Generate plan with template styling as reference (if available)
        plan_json = planner(description=business_description, template_styling=template_styling)
        
        logger.info(f"Raw plan response length: {len(plan_json)} chars")
        logger.info(f"Raw plan preview: {plan_json[:200]}...")
        
        # Parse JSON with multiple fallback strategies
        plan = None
        parse_error = None
        
        # Strategy 1: Direct JSON parse
        try:
            plan = json.loads(plan_json)
            logger.info("✓ JSON parsed directly")
        except json.JSONDecodeError as e:
            parse_error = str(e)
            logger.warning(f"Direct JSON parse failed: {e}")
            
            # Strategy 2: Extract from markdown code blocks
            try:
                if "```json" in plan_json:
                    logger.info("Attempting to extract JSON from ```json block")
                    plan_json = plan_json.split("```json")[1].split("```")[0].strip()
                elif "```" in plan_json:
                    logger.info("Attempting to extract JSON from ``` block")
                    plan_json = plan_json.split("```")[1].split("```")[0].strip()
                
                plan = json.loads(plan_json)
                logger.info("✓ JSON extracted from code block")
            except (json.JSONDecodeError, IndexError) as e2:
                logger.warning(f"Code block extraction failed: {e2}")
                
                # Strategy 3: Find JSON object using regex
                json_match = re.search(r'\{[^{}]*"pages"[^{}]*\}|\{.*"pages".*\}', plan_json, re.DOTALL)
                if json_match:
                    logger.info("Attempting regex extraction of JSON")
                    try:
                        plan = json.loads(json_match.group(0))
                        logger.info("✓ JSON extracted using regex")
                    except json.JSONDecodeError as e3:
                        logger.error(f"Regex extraction failed: {e3}")
                
                # Strategy 4: Create a fallback plan
                if plan is None:
                    logger.warning("All JSON parsing strategies failed, using fallback plan")
                    plan = {
                        "pages": [
                            {"name": "home", "purpose": "Landing page", "sections": ["hero", "features", "cta"]},
                            {"name": "about", "purpose": "About page", "sections": ["story", "team"]},
                            {"name": "contact", "purpose": "Contact page", "sections": ["form", "info"]}
                        ],
                        "styling": {
                            "theme": "modern",
                            "primary_color": "#3B82F6",
                            "secondary_color": "#64748B",
                            "font_family": "sans-serif",
                            "design_style": "clean and professional"
                        },
                        "image_sections": ["hero", "features", "testimonials"],
                        "navigation": ["home", "about", "contact"]
                    }
        
        # Validate plan structure
        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")
        
        if "pages" not in plan or not isinstance(plan["pages"], list):
            raise ValueError("Plan must contain 'pages' array")
        
        if len(plan["pages"]) == 0:
            raise ValueError("Plan must contain at least one page")
        
        logger.info(f"✓ Generated plan with {len(plan.get('pages', []))} pages")
        logger.info(f"Pages: {[p.get('name', 'unknown') for p in plan.get('pages', [])]}")
        
        # Extract design_system from plan (new comprehensive design spec)
        design_system = plan.get("design_system", None)
        if design_system:
            logger.info("✓ Design system extracted from plan")
            logger.info(f"  - Colors: {len(design_system.get('color_palette', {}))} defined")
            logger.info(f"  - Typography: {design_system.get('typography', {}).get('heading_font', 'N/A')}")
        else:
            logger.warning("⚠ No design_system in plan, using legacy styling format")
            # Fallback: create basic design_system from old styling format for backward compatibility
            design_system = plan.get("styling", {})

        # Extract CI4 context from plan (routes, PHP variables, merchant ID)
        ci4_context = plan.get("ci4_context", {})
        shop_mid = ci4_context.get("shop_mid", "1")
        if ci4_context:
            logger.info(f"✓ CI4 context extracted: mid={shop_mid}, routes={list(ci4_context.get('route_patterns', {}).keys())}")
        else:
            logger.warning("⚠ No ci4_context in plan — using defaults")
            ci4_context = {
                "shop_mid": "1",
                "php_variables": ["$categories", "$subcategorieslist", "$products", "$mid"],
                "helper_function": "getDynamicBaseUrl()",
                "route_patterns": {
                    "all_products": "fshop/index/{mid}",
                    "by_category": "fshop/index/{mid}/{catid}",
                    "by_subcategory": "fshop/index/{mid}/{catid}?sub={subcatid}",
                    "single_product": "fshop/product/{mid}/{product_id}",
                    "faq_page": "fshop/faq/{mid}"
                }
            }
        
        # Check if this is a revision (plan_feedback exists)
        is_revision = bool(state.get("plan_feedback"))
        plan_version = state.get("plan_version", 0) + 1 if is_revision else 1
        
        logger.info(f"Plan version: {plan_version}" + (" (revision)" if is_revision else " (initial)"))
        
        # Update state with plan, design system, CI4 config, and approval workflow flags
        return {
            **state,
            "plan": plan,
            "plan_json": json.dumps(plan),        # Store normalized JSON
            "design_system": design_system,        # Store extracted design system
            "ci4_config": ci4_context,             # Store CI4 routes & PHP variable context
            "shop_mid": shop_mid,                  # Store merchant ID for convenience
            "template_styling": template_styling,  # Store extracted template styling (legacy)
            "css_theme": css_theme,                # Store extracted CSS theme (legacy)
            "plan_version": plan_version,          # Track plan iterations
            "awaiting_plan_approval": True,        # Set approval gate flag
            "plan_approved": False,                # Reset approval status
            "plan_revision_requested": False,      # Reset revision flag
            "current_step": "plan_approval",      # Next step is approval
            "status": "awaiting_approval",         # Workflow pauses for user approval
            "progress": 20,
            "progress_message": f"✓ Plan generated: {len(plan.get('pages', []))} pages (home + faq), awaiting your approval"
        }
        
    except Exception as e:
        logger.error(f"Planning node error: {str(e)}")
        return {
            **state,
            "current_step": "failed",
            "status": "failed",
            "error": f"Planning failed: {str(e)}",
            "progress": 0,
            "progress_message": f"✗ Planning failed: {str(e)}"
        }
