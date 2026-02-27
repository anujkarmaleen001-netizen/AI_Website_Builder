"""
LangGraph workflow state definition for website generation.
"""
from typing import TypedDict, Dict, List, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class WorkflowState(TypedDict):
    """State schema for the website generation workflow."""
    
    # User input
    description: str
    
    business_description: Optional[str]
    
    # Reference website scraping
    reference_url: Optional[str]  # URL provided by user as reference
    reference_analysis: Optional[Dict]  # Scraped analysis data from reference site
    
    # Step 0: Business information gathering
    ready: bool  # Whether enough business information has been gathered
    business_plan: Optional[str]  # Initial business understanding/summary before detailed planning
    clarification_questions: Optional[List[str]]  # Questions to ask user if information is insufficient
    
    # Step 1: Planning output
    plan: Optional[Dict]  # Website structure plan
    plan_json: Optional[str]  # Raw JSON string from LLM
    template_styling: Optional[Dict]  # Extracted styling patterns (fonts, colors, CSS structure)
    css_theme: Optional[str]  # Global CSS theme extracted/derived from template
    
    # Design system (comprehensive styling specifications)
    design_system: Optional[Dict]  # Complete design specification including:
        # - color_palette: Full color scheme with variants (primary, secondary, accent, background, text)
        # - typography: Font families, sizes, weights, line-heights, type scale
        # - spacing: Base unit, spacing scale, container widths, section padding
        # - components: Button styles, card styles, input styles, border radius
        # - responsive: Breakpoints, mobile-first strategy, navigation approach
        # - interactions: Animation preferences, hover effects, transitions
    
    # Plan approval workflow
    awaiting_plan_approval: bool  # Flag indicating workflow is waiting for user approval
    plan_approved: bool  # User's approval decision
    plan_revision_requested: bool  # Whether user requested changes to the plan
    plan_feedback: Optional[str]  # User's feedback or change requests
    plan_version: int  # Track plan iterations (starts at 1)
    
    # Step 2: Image generation
    image_descriptions: Optional[Dict]  # Section name -> image description
    image_urls: Optional[Dict]  # Section name -> image URL
    
    # Step 3: Multi-page HTML generation
    pages: Optional[Dict]  # Page name -> {html: str, css: str}
    
    shop_mid: Optional[str]      # Merchant ID used in CI4 routes (e.g. "1")
    ci4_config: Optional[Dict]   # CI4 route patterns and available PHP variables
 

    # Step 4: File storage
    folder_path: Optional[str]  # Path to saved website folder
    saved_files: Optional[Dict]  # Page name -> file path
    
    # Workflow state tracking
    current_step: str  # "planning", "image_description", "image_generation", "html_generation", "file_storage", "complete"
    status: str  # "in_progress", "completed", "failed"
    error: Optional[str]  # Error message if failed
    
    # Progress tracking for streaming
    progress: int  # 0-100
    progress_message: str  # Human-readable progress message
    
    # Messages for LangChain compatibility (optional)
    messages: Annotated[List[BaseMessage], add_messages]


class PlanStructure(TypedDict):
    """Structure of the website plan."""
    pages: List[Dict[str, any]]  # List of page configurations
    styling: Dict[str, str]  # Styling strategy (colors, fonts, theme)
    image_sections: List[str]  # Sections requiring images (hero, features, testimonials)
    navigation: List[str]  # Navigation structure
