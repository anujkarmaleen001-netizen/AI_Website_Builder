"""
Web Scraper Service
Wrapper service to integrate web scraper into the workflow pipeline.
Handles URL detection, scraping, analysis, and formatting design insights.
"""
import re
import logging
import asyncio
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor

from app.web_scraper.main import ScraperPipeline
from app.web_scraper.analyze import AnalysisPipeline

logger = logging.getLogger(__name__)

# Thread pool for running synchronous scraper in async context
_executor = ThreadPoolExecutor(max_workers=2)

# URL regex pattern - matches http/https URLs in text
URL_PATTERN = re.compile(
    r'https?://(?:www\.)?'
    r'[-a-zA-Z0-9@:%._\+~#=]{1,256}'
    r'\.[a-zA-Z0-9()]{1,6}'
    r'(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
    re.IGNORECASE
)


def detect_url_in_text(text: str) -> Optional[str]:
    """
    Extract the first valid URL from user message text.
    
    Args:
        text: User message text that may contain a URL
        
    Returns:
        First valid URL found, or None if no URL detected
    """
    if not text:
        return None
    
    match = URL_PATTERN.search(text)
    if match:
        url = match.group(0)
        # Clean trailing punctuation that might be part of sentence
        url = url.rstrip('.,;:!?)\'\"')
        logger.info(f"Detected URL in text: {url}")
        return url
    
    return None


def _run_scraper_sync(url: str, max_pages: int = 5) -> Dict:
    """
    Run the scraping pipeline synchronously (called from thread pool).
    
    Args:
        url: Website URL to scrape
        max_pages: Maximum number of pages to scrape
        
    Returns:
        Scraped data dictionary
    """
    pipeline = ScraperPipeline(output_dir='scraped_data')
    result = pipeline.run(url, max_pages=max_pages)
    return result


def _run_analysis_sync(scraped_data: Dict) -> Dict:
    """
    Run the analysis pipeline synchronously (called from thread pool).
    Only runs structure and design analysis (no content generation - that
    happens later in the workflow with user's business info).
    
    Args:
        scraped_data: Output from scraper pipeline
        
    Returns:
        Analysis results dictionary
    """
    pipeline = AnalysisPipeline()
    # No user_info - we only want structure and design analysis
    result = pipeline.analyze(scraped_data, user_info=None)
    return result


async def scrape_and_analyze_reference(url: str, max_pages: int = 5, timeout: float = 60.0) -> Dict:
    """
    Run full scraping + AI analysis pipeline asynchronously.
    
    This runs the synchronous scraper in a thread pool to avoid
    blocking the async event loop.
    
    Args:
        url: Reference website URL to scrape and analyze
        max_pages: Maximum pages to scrape (default 5 for references)
        timeout: Maximum time in seconds for the entire operation
        
    Returns:
        Dict with 'scraped_data' and 'analysis' keys, or 'error' key on failure
    """
    logger.info(f"Starting reference site scraping: {url}")
    
    loop = asyncio.get_event_loop()
    
    try:
        # Step 1: Scrape the website
        logger.info("[SCRAPER] Running scraping pipeline...")
        scraped_data = await asyncio.wait_for(
            loop.run_in_executor(_executor, _run_scraper_sync, url, max_pages),
            timeout=timeout * 0.6  # 60% of timeout for scraping
        )
        
        # Validate scraping result
        if not scraped_data or not scraped_data.get('pages'):
            logger.warning("Scraping returned no pages, returning partial data")
            return {
                'scraped_data': scraped_data or {},
                'analysis': {},
                'status': 'partial',
                'message': 'Scraping completed but no pages were found'
            }
        
        logger.info(f"[SCRAPER] Scraped {len(scraped_data.get('pages', []))} pages")
        
        # Step 2: Analyze scraped data  
        logger.info("[ANALYZER] Running AI analysis pipeline...")
        try:
            analysis = await asyncio.wait_for(
                loop.run_in_executor(_executor, _run_analysis_sync, scraped_data),
                timeout=timeout * 0.4  # 40% of timeout for analysis
            )
        except asyncio.TimeoutError:
            logger.warning("Analysis timed out, returning scraped data without analysis")
            analysis = {}
        except Exception as analysis_error:
            logger.warning(f"Analysis failed: {analysis_error}, returning scraped data only")
            analysis = {'error': str(analysis_error)}
        
        logger.info("[SCRAPER] Reference site scraping and analysis complete")
        
        return {
            'scraped_data': scraped_data,
            'analysis': analysis,
            'status': 'completed',
            'url': url
        }
        
    except asyncio.TimeoutError:
        logger.error(f"Scraping timed out after {timeout}s for: {url}")
        return {
            'error': f'Scraping timed out after {timeout}s',
            'status': 'timeout',
            'url': url
        }
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        return {
            'error': str(e),
            'status': 'failed', 
            'url': url
        }


def extract_design_insights(reference_data: Dict) -> str:
    """
    Convert scraped analysis data into a human-readable text summary
    that can be injected into the LLM conversation for design guidance.
    
    Args:
        reference_data: Output from scrape_and_analyze_reference()
        
    Returns:
        Formatted string with design insights for LLM context
    """
    if not reference_data or reference_data.get('status') == 'failed':
        return ""
    
    insights_parts = []
    
    scraped_data = reference_data.get('scraped_data', {})
    analysis = reference_data.get('analysis', {})
    analysis_data = analysis.get('analysis', {})
    
    # --- Platform Info ---
    platform = scraped_data.get('platform', {})
    if platform.get('platform_name'):
        insights_parts.append(f"• Platform: {platform['platform_name']} (confidence: {platform.get('confidence', 0)}%)")
    
    # --- Design Analysis ---
    design = analysis_data.get('design', {})
    if design and 'error' not in design:
        # Color palette
        color_palette = design.get('color_palette', {})
        if color_palette:
            colors_str = ", ".join([f"{name}: {value}" for name, value in color_palette.items()])
            insights_parts.append(f"• Color Palette: {colors_str}")
        
        # Typography
        typography = design.get('typography', {})
        if typography:
            insights_parts.append(f"• Heading Font: {typography.get('heading_font', 'N/A')}")
            insights_parts.append(f"• Body Font: {typography.get('body_font', 'N/A')}")
        
        # Design style
        design_style = design.get('design_style', [])
        if design_style:
            insights_parts.append(f"• Design Style: {', '.join(design_style)}")
        
        # Component patterns
        components = design.get('component_patterns', {})
        if components:
            insights_parts.append(f"• Buttons: {components.get('buttons', 'N/A')}")
            insights_parts.append(f"• Layout Spacing: {components.get('spacing', 'N/A')}")
    
    # --- Structure Analysis ---
    structure = analysis_data.get('structure', {})
    if structure and 'error' not in structure:
        # Recommended pages
        pages = structure.get('recommended_pages', [])
        if pages:
            page_names = [p.get('suggested_name', 'Unknown') for p in pages[:6]]
            insights_parts.append(f"• Page Structure: {', '.join(page_names)}")
        
        # Navigation
        nav = structure.get('navigation_structure', {})
        if nav:
            header_links = nav.get('header', [])
            if header_links:
                link_labels = [l.get('label', '') for l in header_links[:8] if isinstance(l, dict)]
                if link_labels:
                    insights_parts.append(f"• Navigation: {', '.join(link_labels)}")
    
    # --- Raw Assets (fallback if no AI analysis) ---
    if not analysis_data.get('design') or 'error' in analysis_data.get('design', {}):
        assets = scraped_data.get('assets', {})
        if assets:
            colors = assets.get('colors', [])
            if colors:
                insights_parts.append(f"• Raw Colors: {', '.join(colors[:8])}")
            
            fonts = assets.get('fonts', [])
            if fonts:
                insights_parts.append(f"• Raw Fonts: {', '.join(fonts[:5])}")
            
            if assets.get('logo'):
                insights_parts.append(f"• Logo Found: Yes")
    
    # --- Summary ---
    summary = scraped_data.get('summary', {})
    if summary:
        insights_parts.append(f"• Total Pages Found: {summary.get('total_urls_found', 0)}")
        if summary.get('site_title'):
            insights_parts.append(f"• Site Title: {summary['site_title']}")
    
    if not insights_parts:
        return "Limited design data could be extracted from the reference site."
    
    return "\n".join(insights_parts)


def get_reference_context_for_planning(reference_data: Dict) -> str:
    """
    Generate a concise reference context block for the planning node prompt.
    This provides structured design guidance without overwhelming the planner.
    
    Args:
        reference_data: Output from scrape_and_analyze_reference()
        
    Returns:
        Formatted context string for planning prompt injection
    """
    if not reference_data or reference_data.get('status') in ('failed', 'timeout'):
        return ""
    
    analysis = reference_data.get('analysis', {}).get('analysis', {})
    scraped = reference_data.get('scraped_data', {})
    url = reference_data.get('url', 'reference site')
    
    context_parts = [f"REFERENCE DESIGN PATTERNS (inspiration from {url}):"]
    
    # Design tokens
    design = analysis.get('design', {})
    if design and 'error' not in design:
        color_palette = design.get('color_palette', {})
        if color_palette:
            context_parts.append(f"Color Palette: {', '.join([f'{k}: {v}' for k, v in color_palette.items()])}")
        
        typography = design.get('typography', {})
        if typography:
            context_parts.append(f"Typography: headings={typography.get('heading_font', 'sans-serif')}, body={typography.get('body_font', 'sans-serif')}")
        
        style = design.get('design_style', [])
        if style:
            context_parts.append(f"Design Style: {', '.join(style)}")
        
        components = design.get('component_patterns', {})
        if components:
            context_parts.append(f"Components: buttons={components.get('buttons', 'standard')}, spacing={components.get('spacing', 'comfortable')}")
    
    # Structure hints
    structure = analysis.get('structure', {})
    if structure and 'error' not in structure:
        pages = structure.get('recommended_pages', [])
        if pages:
            page_summary = [f"{p.get('suggested_name', '?')} ({p.get('page_type', 'custom')})" for p in pages[:6]]
            context_parts.append(f"Reference Pages: {', '.join(page_summary)}")
    
    context_parts.append("NOTE: Use these as INSPIRATION only. Prioritize the user's specific business requirements.")
    
    if len(context_parts) <= 2:  # Only header + NOTE
        return ""
    
    return "\n".join(context_parts)
