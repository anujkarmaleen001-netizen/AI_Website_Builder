# Standard library imports
import re
import json
import logging

# Third-party imports
import dspy
from typing import Dict, Optional

from .signature import MultiPageSignature, WebsiteUpdateAnalyzerSignature, HTMLEditSignature
from app.config import update_llm


class MultiPageGenerator(dspy.Module):
    """Generate static PHP page parts and CSS for individual pages."""
    
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(MultiPageSignature)
    
    def forward(self, plan: str, page_name: str, page_config: str, image_urls: str, business_description: str, template_styling: Optional[Dict] = None):
        generation_rules = """You are an expert frontend developer creating static PHP website templates.

GENERATION STRATEGY - PRIORITIZE BUSINESS REQUIREMENTS:

YOUR TASK:
- Generate THREE separate HTML partials (header, body, footer) + CSS for this page
- Each partial is a FRAGMENT, NOT a full HTML document
- Follow the page configuration and include all specified sections in body_html
- Use the provided image URLs for appropriate sections (hero, features, etc.)
- Create realistic, professional content aligned with the business description

CRITICAL OUTPUT FORMAT:
1. header_html: ONLY the <header>...</header> element (nav bar). No <html>, <head>, <body> tags.
2. body_html: ONLY the page body sections (<section> blocks). No <html>, <head>, <body>, <header>, <footer> tags.
3. footer_html: ONLY the <footer>...</footer> element + <script> for mobile menu. No <html>, <head>, <body> tags.
4. css: Plain CSS text only (no <style> tags, no markdown). Will be saved as assets/css/style.css.

NAVIGATION LINKS: Use href="[page_name].php" format (NOT .html)

RESPONSIVE DESIGN:
- Mobile: < 768px with hamburger menu
- Tablet: 768px - 1024px
- Desktop: > 1024px

CSS CLASSES TO USE:
- Layout: .container, .grid, .grid-cols-1, .grid-cols-md-3, .gap-lg, .section-padding
- Components: .navbar, .nav-menu, .nav-link, .hero, .card, .btn, .btn-primary
- Typography: .section-title, .text-center

OUTPUT: Separate partials as described above, production-ready."""
        
        full_prompt = f"{generation_rules}\n\n{'='*60}\nGENERATION INPUTS:\n{'='*60}\n\nBUSINESS DESCRIPTION:\n{business_description}\n\nNow create EXCEPTIONAL PHP page partials for this business!"
        
        # Print summary to terminal
        print("\n" + "="*80)
        print(f"🎯 GENERATING PHP PARTIALS FOR PAGE: {page_name}")
        print("="*80)
        print(f"Business Context: {len(business_description)} chars")
        print("="*80 + "\n")
        
        result = self.predict(
            plan=plan,
            page_name=page_name,
            page_config=page_config,
            image_urls=image_urls,
            business_description=full_prompt
        )
        
        # Return all 4 parts as a tuple
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
