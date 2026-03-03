# Standard library imports
import re
import json
import logging

# Third-party imports
import dspy
from typing import Dict, Optional

from .signature import (
    MultiPageSignature,
    WebsiteUpdateAnalyzerSignature,
    HTMLEditSignature,
    CI4_CATEGORY_NAV_TEMPLATE,
)
from app.config import update_llm


class MultiPageGenerator(dspy.Module):
    """Generate static PHP page parts and CSS for individual pages."""
    
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(MultiPageSignature)
    
    def forward(
        self,
        plan: str,
        page_name: str,
        page_config: str,
        image_urls: str,
        business_description: str,
        template_styling=None,
        ci4_config: Optional[Dict] = None,
    ):
        # Build CI4 context block for the LLM prompt
        if ci4_config:
            shop_mid = ci4_config.get("shop_mid", "1")
            php_vars  = ", ".join(ci4_config.get("php_variables", []))
            routes    = json.dumps(ci4_config.get("route_patterns", {}), indent=2)
            ci4_context_block = (
                f"CI4 CRM INTEGRATION CONTEXT:\n"
                f"  Merchant ID ($merchant_id): {shop_mid}\n"
                f"  Available PHP variables from controller: {php_vars}\n"
                f"  Helper function: getDynamicBaseUrl()\n"
                f"  CI4 Route patterns:\n{routes}\n"
            )
        else:
            shop_mid = "1"
            ci4_context_block = (
                "CI4 CRM INTEGRATION CONTEXT:\n"
                "  Merchant ID ($merchant_id): 1\n"
                "  Available PHP variables: $categories, $subcategorieslist, $results, $merchant_id, $search, $filters, $selected_category_id, $selected_subcategory_id\n"
                "  Helper function: getDynamicBaseUrl()\n"
            )

        generation_rules = f"""You are an expert CI4 PHP frontend developer creating dynamic e-commerce page templates.

YOUR TASK:
- Generate THREE separate PHP/HTML partials (header, body, footer) + CSS for the '{page_name}' page
- Each partial is a FRAGMENT, NOT a full HTML document
- The website is integrated with a CI4 CRM — data comes from the database via PHP variables
- DO NOT hardcode product names, categories, or prices — always use PHP loops and variables

{ci4_context_block}

HEADER STRUCTURE (ALL PAGES):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The header contains the BRAND + HOME/FAQ NAV ONLY.
DO NOT put the category nav in the header.
Category nav goes ONLY in the home page body (see below).

HOME PAGE BODY — FIRST BLOCK MUST BE THE CATEGORY NAV:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For the 'home' page, body_html MUST start with this EXACT CI4 category nav block:
{CI4_CATEGORY_NAV_TEMPLATE}
Then follows: hero banner → product grid → CTA banner.

FAQ PAGE BODY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For the 'faq' page, body_html has NO category nav.
Content: FAQ hero → accordion FAQ list → contact CTA.

CRITICAL OUTPUT FORMAT:
1. header_html : ONLY <header>...</header>. Brand + Home/FAQ nav. Single tier. NO category nav.
2. body_html   : ONLY page body blocks (no <html>,<head>,<body>,<header>,<footer> tags)
                 HOME: starts with category nav → hero → products → CTA
                 FAQ:  NO category nav → FAQ hero → FAQ list → contact CTA
3. footer_html : ONLY <footer>...</footer> + <script> blocks (Home & FAQ links only)
4. css         : Plain CSS text only (no <style> tags, no markdown fences)

NAVIGATION — MAIN NAV: Home and FAQ ONLY — no other pages.
All URLs must use getDynamicBaseUrl() with $merchant_id in the route.
Category nav UX rules: non-sticky navbar, no horizontal overflow/scroll on category UL, desktop hover opens subcategories, and dropdown expansion must not create navbar scrolling.

OUTPUT: Production-ready CI4 PHP partials."""

        full_prompt = (
            f"{generation_rules}\n\n"
            f"{'='*60}\nGENERATION INPUTS:\n{'='*60}\n\n"
            f"BUSINESS DESCRIPTION:\n{business_description}\n\n"
            f"Now create EXCEPTIONAL CI4 PHP page partials for this e-commerce shop!"
        )

        print("\n" + "="*80)
        print(f"🛒 GENERATING CI4 PHP PARTIALS — PAGE: {page_name.upper()}")
        print(f"   Shop MID : {shop_mid}")
        print("="*80 + "\n")

        result = self.predict(
            plan=plan,
            page_name=page_name,
            page_config=page_config,
            image_urls=image_urls,
            business_description=full_prompt
        )

        return (
            result.header_html.strip(),
            result.body_html.strip(),
            result.footer_html.strip(),
            result.css.strip()
        )


class HTMLEditor(dspy.Module):
    """Edit existing HTML/CSS content."""
    
    def __init__(self):
        super().__init__()
        # Use update_llm for HTML editing (4K tokens sufficient) - imported at top
        self.predict = dspy.Predict(HTMLEditSignature)
        self.predict.lm = update_llm
    
    def forward(self, html: str, css: str, edit_request: str):
        # Build a detailed prompt for the edit request
        full_prompt = (
            f"Apply the following edit to the HTML page:\n\n"
            f"EDIT REQUEST: {edit_request}\n\n"
            f"RULES:\n"
            f"- Return the COMPLETE updated HTML document.\n"
            f"- Only change what the edit request specifies.\n"
            f"- Preserve all navigation, classes, IDs, and unrelated content.\n"
            f"- Include any modified CSS inside <style> tags in <head>.\n"
        )

        result = self.predict(
            html_input=html,
            css_input=css,
            edit_request=full_prompt
        )
        return result.html_output


class WebsiteUpdater(dspy.Module):
    """Intelligently update website pages and global CSS based on natural language requests."""
    
    def __init__(self):
        super().__init__()
        # Use planning_llm for analysis (short task, 2K tokens) - imported at top
        self.analyzer = dspy.Predict(WebsiteUpdateAnalyzerSignature)
        self.analyzer.lm = update_llm
        
        # Use HTMLEditor for actual modifications (which now uses update_llm with 4K tokens)
        self.html_editor = HTMLEditor()
    
    def forward(self, pages: dict, global_css: str, edit_request: str):
        """
        Analyze edit request and apply updates intelligently.

        Args:
            pages: Dict of page_name -> {html: str, css: str}
            global_css: Current global CSS content
            edit_request: User's natural language edit instructions

        Returns:
            Dict with:
                - updated_pages: Dict of modified pages only
                - updated_global_css: Modified global CSS if changed
                - changes_summary: Description of what was changed
        """
        # json, logging imported at top of file
        logger = logging.getLogger(__name__)

        # Step 1: Analyze the edit request
        available_pages_list = list(pages.keys())
        available_pages_text = ", ".join(available_pages_list)

        logger.info(f"Analyzing edit request: {edit_request[:100]}...")
        logger.info(f"Available pages: {available_pages_text}")

        try:
            analysis_result = self.analyzer(
                edit_request=edit_request,
                available_pages=available_pages_text,
                current_global_css=global_css[:500] if global_css else ""  # Just a sample for context
            )

            # Parse analysis
            try:
                analysis = json.loads(analysis_result.analysis)
                logger.info(f"Analysis result: {analysis}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse analysis JSON: {e}, using fallback")
                # Fallback: try to determine from keywords
                edit_lower = edit_request.lower()

                # Check for global styling keywords
                global_keywords = ['color', 'font', 'theme', 'all pages', 'everywhere', 'global', 'button', 'spacing']
                is_global = any(keyword in edit_lower for keyword in global_keywords)

                # Check for page-specific keywords
                page_specific = any(page_name in edit_lower for page_name in available_pages_list)

                if is_global and not page_specific:
                    analysis = {
                        "update_type": "global_css",
                        "target_pages": [],
                        "requires_css_update": True,
                        "interpretation": "Applying global styling changes"
                    }
                elif page_specific and not is_global:
                    # Try to identify which pages
                    target_pages = [page for page in available_pages_list if page in edit_lower]
                    analysis = {
                        "update_type": "specific_pages",
                        "target_pages": target_pages if target_pages else [available_pages_list[0]],
                        "requires_css_update": False,
                        "interpretation": f"Updating content on specific pages: {', '.join(target_pages)}"
                    }
                else:
                    # Both or ambiguous
                    target_pages = [page for page in available_pages_list if page in edit_lower]
                    if not target_pages:
                        target_pages = [available_pages_list[0]]  # Default to first page
                    analysis = {
                        "update_type": "both",
                        "target_pages": target_pages,
                        "requires_css_update": True,
                        "interpretation": "Updating both styling and page content"
                    }
        except Exception as e:
            logger.error(f"Analysis failed: {e}, using fallback analysis")
            # Ultra-fallback: update first page only
            analysis = {
                "update_type": "specific_pages",
                "target_pages": [available_pages_list[0]] if available_pages_list else [],
                "requires_css_update": False,
                "interpretation": "Updating page content"
            }

        # Step 2: Apply updates based on analysis
        updated_pages = {}
        updated_global_css = None
        changes_made = []

        # Update global CSS if needed
        if analysis.get("requires_css_update") and global_css:
            logger.info("Updating global CSS...")
            try:
                # Create a minimal HTML wrapper for CSS editing
                css_wrapper_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
    {global_css}
    </style>
</head>
<body>
    <p>CSS Template</p>
</body>
</html>"""

                # Use HTMLEditor to modify the CSS
                modified_html = self.html_editor(
                    html=css_wrapper_html,
                    css=global_css,
                    edit_request=f"Update the CSS styling based on this request: {edit_request}. Only modify the CSS, preserve the HTML structure."
                )

                # Extract the modified CSS from the result
                import re
                style_pattern = r'<style[^>]*>(.*?)</style>'
                css_matches = re.findall(style_pattern, modified_html, re.DOTALL | re.IGNORECASE)
                if css_matches:
                    updated_global_css = '\n\n'.join(css_matches).strip()
                    changes_made.append("Updated global CSS styling")
                    logger.info(f"✓ Global CSS updated ({len(updated_global_css)} chars)")
                else:
                    logger.warning("Could not extract CSS from modified HTML, keeping original")
                    updated_global_css = global_css
            except Exception as e:
                logger.error(f"Error updating global CSS: {e}")
                updated_global_css = global_css

        # Update specific pages if needed
        target_pages = analysis.get("target_pages", [])
        # Fallback: if analyzer returned no target pages (e.g. update_type='global_css'),
        # update ALL pages so we never silently return nothing.
        if not target_pages:
            target_pages = available_pages_list
            logger.info(f"No target pages from analysis, defaulting to all pages: {target_pages}")
        if target_pages:
            for page_name in target_pages:
                if page_name not in pages:
                    logger.warning(f"Page '{page_name}' not found in provided pages")
                    continue

                logger.info(f"Updating page: {page_name}...")
                try:
                    page_data = pages[page_name]
                    # Support both PHP partial format (body_html) and legacy html format
                    current_html = page_data.get('body_html', page_data.get('html', ''))
                    current_css = page_data.get('css', global_css if global_css else '')

                    # Use HTMLEditor to modify the page body content
                    modified_html = self.html_editor(
                        html=current_html,
                        css=current_css,
                        edit_request=edit_request
                    )

                    # Extract CSS if any (re imported at top)
                    html_clean, extracted_css = self._extract_css(modified_html)

                    updated_pages[page_name] = {
                        **page_data,  # preserve header_html, footer_html fields
                        'body_html': html_clean,
                        'html': html_clean,  # backward compat
                        'css': extracted_css if extracted_css else current_css
                    }
                    changes_made.append(f"Updated {page_name} page")
                    logger.info(f"✓ Page '{page_name}' updated")
                except Exception as e:
                    logger.error(f"Error updating page '{page_name}': {e}")

        # Generate summary
        if not changes_made:
            changes_summary = "No changes were made. Please check your request."
        else:
            changes_summary = f"Successfully applied changes: {', '.join(changes_made)}"

        logger.info(f"Update complete: {changes_summary}")

        return {
            "updated_pages": updated_pages,
            "updated_global_css": updated_global_css,
            "changes_summary": changes_summary,

            
            "analysis": analysis
        }
    def _extract_css(self, html: str):
        """Helper method to extract CSS from HTML. (re imported at top)"""
        style_pattern = r'<style[^>]*>(.*?)</style>'
        css_matches = re.findall(style_pattern, html, re.DOTALL | re.IGNORECASE)
        extracted_css = '\n\n'.join(css_matches).strip()
        html_without_style = re.sub(style_pattern, '', html, flags=re.DOTALL | re.IGNORECASE)
        return html_without_style, extracted_css
