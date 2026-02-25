"""
HTML generation node for website generation workflow.
Generates static PHP partials (header, body, footer) and CSS for each page.

OPTIMIZED: Pages are generated in PARALLEL using asyncio.gather()
to dramatically reduce total generation time.
"""
import re
import json
import asyncio
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


def _generate_page(generator: MultiPageGenerator, plan: dict, page: dict,
                   image_urls_text: str, description: str,
                   template_styling, page_names: list,
                   is_single_page: bool) -> dict:
    """
    Synchronous helper that generates PHP partials for ONE page.
    Runs inside asyncio.to_thread() so multiple pages run in parallel.
    """
    page_name = page["name"]
    logger.info(f"→ Generating PHP partials for page: {page_name}")

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

    # Generate the 3 PHP partials + CSS
    header_html, body_html, footer_html, css = generator(
        plan=json.dumps(enhanced_plan),
        page_name=page_name,
        page_config=json.dumps(page),
        image_urls=image_urls_text,
        business_description=description,
        template_styling=template_styling
    )

    # Clean markdown fences from each part
    header_html = _clean_partial(header_html, "header")
    body_html   = _clean_partial(body_html,   "body")
    footer_html = _clean_partial(footer_html, "footer")

    # CSS: strip any style tags if LLM accidentally included them
    css = re.sub(r'<style[^>]*>', '', css, flags=re.IGNORECASE)
    css = re.sub(r'</style>', '',   css, flags=re.IGNORECASE)
    css = re.sub(r'```[a-z]*', '', css)
    css = css.strip()

    # Validate body content (most critical part)
    if not body_html or len(body_html) < 50:
        raise ValueError(
            f"PHP generation failed for {page_name}: body_html too short or empty "
            f"({len(body_html)} chars)"
        )

    logger.info(
        f"✓ {page_name}: header={len(header_html)}c, body={len(body_html)}c, "
        f"footer={len(footer_html)}c, css={len(css)}c"
    )

    return {
        "page_name": page_name,
        "header_html": header_html,
        "body_html":   body_html,
        "footer_html": footer_html,
        "css":         css
    }


async def html_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Step 3: Generate static PHP page partials (header, body, footer) + CSS.

    OPTIMIZED: All pages are generated in PARALLEL using asyncio.gather()
    so 4 pages take the same time as 1 page (instead of 4× longer).

    Stores results in state['pages'] as:
      { page_name: { header_html, body_html, footer_html, css } }
    Only header/footer from the FIRST page are used as shared templates.
    """
    logger.info("Starting HTML generation node (PHP static mode — PARALLEL)...")

    try:
        plan        = state["plan"]
        image_urls  = state["image_urls"]
        all_pages   = plan.get("pages", [])
        page_names  = [p["name"] for p in all_pages]
        is_single_page   = len(all_pages) == 1
        template_styling = state.get("template_styling")

        logger.info(f"Website type : {'SINGLE-PAGE' if is_single_page else 'MULTI-PAGE'}")
        logger.info(f"Pages to generate IN PARALLEL: {page_names}")

        # One generator instance — DSPy modules are stateless for forward() calls
        generator = MultiPageGenerator()

        # Format image URLs once
        image_urls_text = "\n".join(
            f"{section}: {url}" for section, url in image_urls.items()
        )

        # ── Build parallel tasks ────────────────────────────────────────────
        tasks = [
            asyncio.to_thread(
                _generate_page,
                generator,
                plan,
                page,
                image_urls_text,
                state["description"],
                template_styling,
                page_names,
                is_single_page
            )
            for page in all_pages
        ]

        logger.info(f"Launching {len(tasks)} parallel HTML generation tasks...")
        # Run ALL pages at the same time
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # ── Collect results ─────────────────────────────────────────────────
        pages_output = {}
        errors = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Page generation failed: {result}")
                errors.append(str(result))
            else:
                pages_output[result["page_name"]] = {
                    "header_html": result["header_html"],
                    "body_html":   result["body_html"],
                    "footer_html": result["footer_html"],
                    "css":         result["css"]
                }

        # If ALL pages failed — raise so workflow enters failed state
        if not pages_output:
            raise ValueError(
                f"All {len(all_pages)} page(s) failed to generate. "
                f"Errors: {'; '.join(errors)}"
            )

        # Partial success — warn but continue (file_storage handles what exists)
        if errors:
            logger.warning(
                f"⚠ {len(errors)} page(s) failed: {errors}. "
                f"Continuing with {len(pages_output)} successful page(s)."
            )

        logger.info(
            f"✅ Parallel HTML generation complete: "
            f"{len(pages_output)}/{len(all_pages)} pages generated"
        )

        return {
            **state,
            "pages":            pages_output,
            "current_step":     "file_storage",
            "status":           "in_progress",
            "progress":         90,
            "progress_message": (
                f"PHP partials generated for {len(pages_output)} pages "
                f"{'(some pages failed — check logs)' if errors else ''}"
                f", preparing to save files..."
            )
        }

    except Exception as e:
        logger.error(f"HTML generation node error: {str(e)}")
        return {
            **state,
            "current_step":     "failed",
            "status":           "failed",
            "error":            f"HTML generation failed: {str(e)}",
            "progress":         65,
            "progress_message": f"HTML generation failed: {str(e)}"
        }
