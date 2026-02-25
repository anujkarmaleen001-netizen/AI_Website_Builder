"""
Image generation node for website generation workflow.
Generates images using DALL-E 3 based on descriptions from image_description_node.
Generated images are saved to uploads/ and local file paths stored in state
so file_manager can copy them into the website theme folder.
"""
import asyncio
import logging
import os
from typing import Dict

from dotenv import load_dotenv

from app.workflow_state import WorkflowState
from app.utils import call_dalle

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Sections and their ideal DALL-E sizes
SECTION_SIZES = {
    "hero":         "1792x1024",   # wide landscape for hero banners
    "features":     "1024x1024",   # square for feature cards
    "testimonials": "1024x1024",   # square for testimonial photos
}


async def image_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Step 2b: Generate images using DALL-E 3 based on descriptions.
    Saves images to uploads/, stores both public URLs and local file paths in state.
    file_manager.py will later copy local files into <name>theme/images/.
    """
    logger.info("Starting image generation node (DALL-E 3)...")

    try:
        image_descriptions = state.get("image_descriptions", {})
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")

        image_urls       = {}   # section → public URL (for LLM to embed in HTML)
        image_local_paths = {}  # section → local file path (for file_manager to copy)

        # Static fallback images if DALL-E fails
        static_fallbacks = {
            "hero":         "hero_1766668485.png",
            "features":     "features_1766668478.png",
            "testimonials": "testimonials_1766668479.png",
        }

        # Build parallel tasks
        tasks = []
        sections = list(image_descriptions.keys())

        for section in sections:
            description = image_descriptions[section]
            size = SECTION_SIZES.get(section, "1024x1024")
            logger.info(f"Queuing DALL-E generation for '{section}' at {size}")
            tasks.append(
                call_dalle(
                    section=section,
                    prompt=description,
                    size=size,
                    quality="standard"
                )
            )

        # Execute in parallel
        if tasks:
            logger.info(f"Starting parallel DALL-E generation for {len(tasks)} images...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                section = sections[i]

                if isinstance(result, Exception):
                    logger.error(f"DALL-E failed for '{section}': {result}")
                    fallback = static_fallbacks.get(section, "placeholder.png")
                    fallback_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        "uploads", fallback
                    )
                    image_urls[section] = f"{base_url}/uploads/{fallback}"
                    if os.path.exists(fallback_path):
                        image_local_paths[section] = fallback_path
                    logger.info(f"Using fallback image for '{section}'")
                else:
                    # result is local URL e.g. "/uploads/hero_1234.png"
                    local_url = result
                    image_urls[section] = f"{base_url}{local_url}"

                    # Derive absolute file path from the URL
                    filename = os.path.basename(local_url)
                    uploads_dir = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        "uploads"
                    )
                    abs_path = os.path.join(uploads_dir, filename)
                    image_local_paths[section] = abs_path
                    logger.info(f"✓ '{section}' → {image_urls[section]}")
        else:
            logger.warning("No image descriptions found — skipping image generation")

        logger.info(f"Generated {len(image_urls)} images")

        return {
            **state,
            "image_urls":        image_urls,
            "image_local_paths": image_local_paths,   # passed to file_manager
            "current_step":      "html_generation",
            "progress":          65,
            "progress_message":  f"✓ {len(image_urls)} images generated"
        }

    except Exception as e:
        logger.error(f"Image generation node error: {str(e)}")
        return {
            **state,
            "image_urls":        {},
            "image_local_paths": {},
            "current_step":      "html_generation",   # continue anyway
            "progress":          65,
            "progress_message":  f"⚠ Image generation failed ({str(e)}), continuing without images"
        }
