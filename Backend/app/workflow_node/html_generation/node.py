"""
HTML generation node for website generation workflow.
Generates static PHP partials (header, body, footer) and CSS for each page.
"""
import re
import json
import logging
from typing import Dict

from app.workflow_state import WorkflowState
from .dspy_modules import MultiPageGenerator

# Configure logging
logger = logging.getLogger(__name__)


def _clean_partial(html: str, part_name: str) -> str:
    """Remove markdown code fences from an HTML partial."""
    html = html.strip()
    for fence in ("```html", "```php", "```"):
        if html.startswith(fence):
            html = html[len(fence):]
            break
    if html.endswith("```"):
        html = html[:-3]
    return html.strip()


def html_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Step 3: Generate static PHP page partials (header, body, footer) + CSS.
    Stores results in state['pages'] as:
      { page_name: { header_html, body_html, footer_html, css } }
    Only header/footer from the FIRST page are used as shared templates.
    """
    logger.info("Starting HTML generation node (PHP static mode)...")

    try:
        plan = state["plan"]
        image_urls = state["image_urls"]
        pages_output = {}

        # Initialize generator
        generator = MultiPageGenerator()

        # Format image URLs for DSPy
        image_urls_text = "\n".join([f"{section}: {url}" for section, url in image_urls.items()])

        # Extract all page names for navigation context
        all_pages = plan.get("pages", [])
        page_names = [page["name"] for page in all_pages]
        is_single_page = len(all_pages) == 1

        logger.info(f"Website type: {'SINGLE-PAGE' if is_single_page else 'MULTI-PAGE'}")
        logger.info(f"Generating PHP partials for {len(all_pages)} pages: {page_names}")

        total_pages = len(all_pages)
        for idx, page in enumerate(all_pages):
            page_name = page["name"]
            logger.info(f"Generating PHP partials for page: {page_name} ({idx + 1}/{total_pages})")

            # Build navigation info for the LLM
            if is_single_page:
                sections = page.get("sections", [])
                navigation_info = {
                    "navigation_type": "single-page",
                    "navigation_method": "anchor-links",
                    "sections": sections,
                    "instruction": (
                        "CRITICAL: This is a SINGLE-PAGE website. "
                        "Create navigation using ANCHOR LINKS (href='#section-name'). "
                        "All page links use .php extension."
                    )
                }
            else:
                navigation_info = {
                    "navigation_type": "multi-page",
                    "navigation_method": "page-links",
                    "pages": page_names,
                    "instruction": (
                        "MULTI-PAGE website. Navigation links use href='[page_name].php' format."
                    )
                }

            enhanced_plan = {
                **plan,
                "current_page": page_name,
                "all_pages": page_names,
                "is_single_page": is_single_page,
                "navigation": navigation_info
            }

            template_styling = state.get("template_styling")

            # Generate the 3 PHP partials + CSS
            header_html, body_html, footer_html, css = generator(
                plan=json.dumps(enhanced_plan),
                page_name=page_name,
                page_config=json.dumps(page),
                image_urls=image_urls_text,
                business_description=state["description"],
                template_styling=template_styling
            )

            # Clean markdown fences from each part
            header_html = _clean_partial(header_html, "header")
            body_html = _clean_partial(body_html, "body")
            footer_html = _clean_partial(footer_html, "footer")
            # CSS: strip any style tags if LLM accidentally included them
            css = re.sub(r'<style[^>]*>', '', css, flags=re.IGNORECASE)
            css = re.sub(r'</style>', '', css, flags=re.IGNORECASE)
            css = re.sub(r'```[a-z]*', '', css)
            css = css.strip()

            # Validate body content (most critical part)
            if not body_html or len(body_html) < 50:
                logger.error(f"Empty or too short body_html for {page_name} ({len(body_html)} chars)")
                raise ValueError(f"PHP generation failed for {page_name}: body_html too short or empty")

            pages_output[page_name] = {
                "header_html": header_html,
                "body_html": body_html,
                "footer_html": footer_html,
                "css": css
            }

            logger.info(
                f"Generated PHP partials for {page_name}: "
                f"header={len(header_html)}c, body={len(body_html)}c, "
                f"footer={len(footer_html)}c, css={len(css)}c"
            )

        logger.info(f"Generated PHP partials for {len(pages_output)} pages")

        return {
            **state,
            "pages": pages_output,
            "current_step": "file_storage",
            "status": "in_progress",
            "progress": 90,
            "progress_message": (
                f"PHP partials generated for {len(pages_output)} pages, preparing to save files..."
            )
        }

    except Exception as e:
        logger.error(f"HTML generation node error: {str(e)}")
        return {
            **state,
            "current_step": "failed",
            "status": "failed",
            "error": f"HTML generation failed: {str(e)}",
            "progress": 65,
            "progress_message": f"HTML generation failed: {str(e)}"
        }
