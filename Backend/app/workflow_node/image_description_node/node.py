"""
Image description node for website generation workflow.
Generates targeted image descriptions for specific sections based on plan.
"""
import asyncio
import json
import logging
from typing import Dict

from app.workflow_state import WorkflowState
from .dspy_modules import ImageDescriptionGenerator

# Configure logging
logger = logging.getLogger(__name__)


async def image_description_node(state: WorkflowState) -> WorkflowState:
    """
    Step 2a: Generate image descriptions for sections based on plan.
    Executing in parallel for speed.
    """
    logger.info("Starting image description node...")
    
    try:
        plan = state["plan"]
        # Only generate images for these 3 specific sections
        image_sections = ["hero", "features", "testimonials", "preview"]
        
        # Initialize generator
        generator = ImageDescriptionGenerator()
        
        # Generator wrapper for async execution
        def generate_description_safe(section, page_name):
            try:
                logger.info(f"Generating image description for {section} on {page_name}")
                plan_str = json.dumps(plan)
                description = generator(
                    plan=plan_str,
                    section_name=section,
                    page_name=page_name,
                    business_description=state["description"]
                )
                return (section, description)
            except Exception as e:
                return (section, e)

        # Prepare tasks
        tasks = []
        
        for section in image_sections:
            # Determine which page has this section
            page_name = "home"  # Default to home page
            for page in plan.get("pages", []):
                if section in page.get("sections", []):
                    page_name = page["name"]
                    break
            
            # Create async task for this section
            tasks.append(
                asyncio.to_thread(
                    generate_description_safe, 
                    section, 
                    page_name
                )
            )
            
        # Execute in parallel
        logger.info(f"Starting parallel generation of {len(tasks)} image descriptions...")
        results = await asyncio.gather(*tasks)
        
        # Process results
        image_descriptions = {}
        fallback_descriptions = {
            "hero": "Professional business hero banner with modern design, clean layout, and welcoming atmosphere",
            "features": "Clean feature section with minimalist icons and professional presentation",
            "testimonials": "Professional testimonial section with friendly atmosphere and trust-building design",
            "preview": "A wide, full-page website mockup thumbnail showing the complete layout of a modern professional website, birds-eye overview screenshot style, clean design, consistent branding, light background"
        }
        
        for section, result in results:
            if isinstance(result, Exception):
                logger.error(f"Error generating description for {section}: {str(result)}")
                # Use fallback
                fallback = fallback_descriptions.get(
                    section,
                    f"Professional {section} section with modern, clean design"
                )
                image_descriptions[section] = fallback
                logger.info(f"Using fallback description for {section}")
            else:
                image_descriptions[section] = result
                logger.info(f"✓ Generated description for {section}")
        
        logger.info(f"Generated {len(image_descriptions)} image descriptions")
        
        # Update state
        return {
            **state,
            "image_descriptions": image_descriptions,
            "current_step": "image_generation",
            "progress": 40,
            "progress_message": f"✓ Image descriptions ready for {len(image_descriptions)} sections"
        }
        
    except Exception as e:
        logger.error(f"Image description node error: {str(e)}")
        
        # For catastrophic errors, fail the workflow
        return {
            **state,
            "current_step": "failed",
            "status": "failed",
            "error": f"Image description generation failed: {str(e)}",
            "progress": 25,
            "progress_message": f"✗ Image description failed: {str(e)}"
        }
