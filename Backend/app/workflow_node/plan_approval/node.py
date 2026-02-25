"""
Plan approval workflow node.

Presents comprehensive website plan to user for review and approval.
"""
import logging
from typing import Dict
from app.workflow_state import WorkflowState
from langchain_core.messages import AIMessage
# Configure logging
logger = logging.getLogger(__name__)


def format_color_palette(colors: Dict) -> str:
    """Format color palette for display."""
    if not colors:
        return "  No color palette defined"
    
    lines = []
    for key, value in colors.items():
        # Format key nicely: primary_dark -> Primary Dark
        display_key = key.replace('_', ' ').title()
        lines.append(f"  • {display_key}: {value}")
    return "\n".join(lines)


def format_typography(typography: Dict) -> str:
    """Format typography system for display."""
    if not typography:
        return "  No typography defined"
    
    lines = []
    lines.append(f"  • Heading Font: {typography.get('heading_font', 'N/A')}")
    lines.append(f"  • Body Font: {typography.get('body_font', 'N/A')}")
    
    type_scale = typography.get('type_scale', {})
    if type_scale:
        lines.append("  • Type Scale:")
        for level, size in type_scale.items():
            lines.append(f"    - {level}: {size}")
    
    return "\n".join(lines)


def format_pages(pages: list) -> str:
    """Format pages list for display."""
    if not pages:
        return "  No pages defined"
    
    lines = []
    for page in pages:
        name = page.get('name', 'Unknown')
        purpose = page.get('purpose', 'No purpose')
        sections = page.get('sections', [])
        sections_str = ', '.join(sections) if sections else 'No sections'
        lines.append(f"  • {name.upper()}: {purpose}")
        lines.append(f"    Sections: {sections_str}")
    return "\n".join(lines)


def format_responsive(responsive: Dict) -> str:
    """Format responsive strategy for display."""
    if not responsive:
        return "  No responsive strategy defined"
    
    lines = []
    breakpoints = responsive.get('breakpoints', {})
    if breakpoints:
        lines.append("  • Breakpoints:")
        for device, size in breakpoints.items():
            lines.append(f"    - {device.capitalize()}: {size}")
    
    lines.append(f"  • Mobile Navigation: {responsive.get('mobile_nav_style', 'N/A')}")
    lines.append(f"  • Mobile First: {responsive.get('mobile_first', False)}")
    
    return "\n".join(lines)


def plan_approval_node(state: WorkflowState) -> WorkflowState:
    """
    Format and present the website plan for user approval.
    Creates a comprehensive approval message with all plan details.
    """
    logger.info("Starting plan approval node...")
    
    try:
        plan = state.get("plan", {})
        design_system = state.get("design_system", {})
        business_plan = state.get("business_plan", "")
        plan_version = state.get("plan_version", 1)
        
        # Build comprehensive approval message
        approval_message = f"""
═══════════════════════════════════════════════════════════════
📋 WEBSITE PLAN (Version {plan_version}) - REVIEW & APPROVE
═══════════════════════════════════════════════════════════════

🎯 BUSINESS SUMMARY:
{business_plan[:300]}{'...' if len(business_plan) > 300 else ''}

───────────────────────────────────────────────────────────────
📄 PAGES & STRUCTURE:
───────────────────────────────────────────────────────────────
{format_pages(plan.get('pages', []))}

───────────────────────────────────────────────────────────────
🎨 DESIGN SYSTEM:
───────────────────────────────────────────────────────────────

COLOR PALETTE:
{format_color_palette(design_system.get('color_palette', {}))}

TYPOGRAPHY:
{format_typography(design_system.get('typography', {}))}

SPACING:
  • Base Unit: {design_system.get('spacing', {}).get('base_unit', 'N/A')}
  • Container Max Width: {design_system.get('spacing', {}).get('container_max_width', 'N/A')}
  • Section Padding: {design_system.get('spacing', {}).get('section_padding_y', 'N/A')} vertical

COMPONENTS:
  • Button Style: {design_system.get('components', {}).get('button_style', 'N/A')}
  • Card Style: {design_system.get('components', {}).get('card_style', 'N/A')}
  • Border Radius: {design_system.get('components', {}).get('border_radius_base', 'N/A')}

───────────────────────────────────────────────────────────────
📱 RESPONSIVE DESIGN:
───────────────────────────────────────────────────────────────
{format_responsive(design_system.get('responsive', {}))}

───────────────────────────────────────────────────────────────
🖼️  IMAGE SECTIONS:
───────────────────────────────────────────────────────────────
  {', '.join(plan.get('image_sections', [])) if plan.get('image_sections') else 'None'}

───────────────────────────────────────────────────────────────
🧭 NAVIGATION:
───────────────────────────────────────────────────────────────
  {' → '.join([nav.capitalize() for nav in plan.get('navigation', [])])}

═══════════════════════════════════════════════════════════════

✅ To APPROVE this plan and start building, reply with: "APPROVE" or "Yes, build it"

🔧 To REQUEST CHANGES, provide specific feedback like:
   • "Change primary color to dark green"
   • "Use a more elegant serif font for headings"
   • "Add a pricing page"
   • "Make it more minimal and clean"

═══════════════════════════════════════════════════════════════
"""
        
        logger.info(f"✓ Plan approval message generated (version {plan_version})")
        
        # Store the formatted approval message in messages for the user
        
        messages = state.get("messages", [])
        messages = messages + [AIMessage(content=approval_message)]
        
        return {
            **state,
            "messages": messages,
            "current_step": "plan_approval",
            "status": "awaiting_approval",
            "progress": 22,
            "progress_message": f"📋 Plan ready for review (v{plan_version}). Please approve or request changes."
        }
        
    except Exception as e:
        logger.error(f"Plan approval node error: {str(e)}")
        return {
            **state,
            "current_step": "failed",
            "status": "failed",
            "error": f"Plan approval failed: {str(e)}",
            "progress": 0,
            "progress_message": f"✗ Plan approval failed: {str(e)}"
        }
