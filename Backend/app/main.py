# Standard library imports
import os
import time
import logging
import asyncio
import json
import re
from typing import Tuple

# Third-party imports
from dotenv import load_dotenv # type: ignore
from fastapi import FastAPI, HTTPException, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, RedirectResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
import dspy # type: ignore - Used for DSPy configuration and LM settings
import uvicorn # type: ignore - Used for running the FastAPI server

# Local application imports
from app.schema import (
    GenerateWebsiteRequest, WebsitePlanResponse, WebsiteGenerationResponse, UpdateWebsiteRequest, UpdateWebsiteResponse
)
from app.utils import call_dalle, find_local_images
import app.config  # Import config to configure DSPy

from app.workflow_graph import website_workflow
from app.workflow_state import WorkflowState
from app.rate_limiter import init_rate_limiter, get_rate_limiter

# Import litellm for error handling (optional dependency)
try:
    import litellm # type: ignore
except ImportError:
    litellm = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Landing Page Generator API",
    version="1.0.0",
    debug=False
)

# Initialize rate limiter with simple config
init_rate_limiter({
    'requests_per_minute': 60,
    'requests_per_hour': 1000,
    'burst_size': 10
})

logger.info("Starting AI Landing Page Generator API v1.0.0")





# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables (OPENAI_API_KEY is used in dspy_modules.py)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
WEBTEMPLATES_DIR = os.path.join(BASE_DIR, "webtemplates")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(WEBTEMPLATES_DIR, exist_ok=True)

# Mount static directories
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/test")
async def serve_test_page():
    """Serve the test page for /api/generate-website endpoint"""
    index_path = os.path.join(BASE_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/api/serve-website/{folder_name}/{file_path:path}")
async def serve_website_file(folder_name: str, file_path: str):
    """
    Serve static files from a generated website folder.
    
    Args:
        folder_name: Name of the website folder (e.g., 'website_20260107_120500')
        file_path: Path to the file within the folder (e.g., 'index.html', 'style.css', 'home.html')
    
    Returns:
        FileResponse with the requested file
    """
    # Sanitize folder_name to prevent directory traversal
    folder_name = os.path.basename(folder_name)
    
    # Construct full path
    website_folder = os.path.join(WEBTEMPLATES_DIR, folder_name)
    full_path = os.path.join(website_folder, file_path)
    
    # Security check: ensure the resolved path is within webtemplates
    try:
        real_path = os.path.realpath(full_path)
        real_webtemplates = os.path.realpath(WEBTEMPLATES_DIR)
        
        if not real_path.startswith(real_webtemplates):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Security check failed: {str(e)}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    if not os.path.exists(full_path):
        logger.warning(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Determine MIME type
    if full_path.endswith('.html'):
        media_type = 'text/html'
    elif full_path.endswith('.css'):
        media_type = 'text/css'
    elif full_path.endswith('.js'):
        media_type = 'application/javascript'
    elif full_path.endswith('.json'):
        media_type = 'application/json'
    elif full_path.endswith('.png'):
        media_type = 'image/png'
    elif full_path.endswith('.jpg') or full_path.endswith('.jpeg'):
        media_type = 'image/jpeg'
    else:
        media_type = None
    
    logger.info(f"Serving file: {full_path}")
    return FileResponse(full_path, media_type=media_type)

@app.get("/api/serve-website/{folder_name}")
async def serve_website_index(folder_name: str, request: Request):
    """
    Redirect to the folder URL with a trailing slash.
    This ensures relative URLs in index.html work correctly.
    
    Args:
        folder_name: Name of the website folder
        request: FastAPI Request object
    
    Returns:
        RedirectResponse to the folder with trailing slash
    """
    # Redirect to the same URL with a trailing slash
    redirect_url = f"/api/serve-website/{folder_name}/index.html"
    return RedirectResponse(url=redirect_url, status_code=307)

@app.get("/api/serve-website/{folder_name}/")
async def serve_website_index_with_slash(folder_name: str):
    """
    Serve the index.html file from a generated website folder.
    The trailing slash ensures relative URLs in the HTML work correctly.
    
    Args:
        folder_name: Name of the website folder
    
    Returns:
        FileResponse with index.html
    """
    # Sanitize folder_name to prevent directory traversal
    folder_name = os.path.basename(folder_name)
    
    # Construct full path to index.html
    website_folder = os.path.join(WEBTEMPLATES_DIR, folder_name)
    index_path = os.path.join(website_folder, "index.html")
    
    # Security check: ensure the resolved path is within webtemplates
    try:
        real_path = os.path.realpath(index_path)
        real_webtemplates = os.path.realpath(WEBTEMPLATES_DIR)
        
        if not real_path.startswith(real_webtemplates):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Security check failed: {str(e)}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    if not os.path.exists(index_path):
        logger.warning(f"File not found: {index_path}")
        raise HTTPException(status_code=404, detail="index.html not found")
    
    # Check if it's actually a file
    if not os.path.isfile(index_path):
        logger.error(f"Path is not a file: {index_path}")
        raise HTTPException(status_code=500, detail="Invalid file path")
    
    logger.info(f"Serving index.html from: {index_path}")
    return FileResponse(index_path, media_type='text/html')


def extract_css_and_replace_style_tags(html: str) -> Tuple[str, str]:
    """
    Extract CSS from <style> tags and replace them with external stylesheet link.
    
    Args:
        html: HTML string containing <style> tags
        
    Returns:
        tuple: (html_with_link_tag, extracted_css)
    """
    # Pattern to match <style> tags with optional attributes
    style_pattern = r'<style[^>]*>(.*?)</style>'
    
    # Extract all CSS content from style tags
    css_matches = re.findall(style_pattern, html, re.DOTALL | re.IGNORECASE)
    extracted_css = '\n\n'.join(css_matches).strip()
    
    # Remove all style tags from HTML
    html_without_style = re.sub(style_pattern, '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Insert <link> tag before </head> if head tag exists
    link_tag = '<link rel="stylesheet" href="style.css">'
    
    # Check if </head> exists
    if '</head>' in html_without_style.lower():
        # Insert link tag before </head> (case-insensitive)
        html_with_link = re.sub(
            r'(</head>)',
            f'{link_tag}\n    \\1',
            html_without_style,
            flags=re.IGNORECASE
        )
    else:
        # If no </head> tag, try to insert before </html> or at the beginning
        if '</html>' in html_without_style.lower():
            html_with_link = re.sub(
                r'(</html>)',
                f'    {link_tag}\n\\1',
                html_without_style,
                flags=re.IGNORECASE
            )
        else:
            # Fallback: prepend link tag to HTML
            html_with_link = f'{link_tag}\n{html_without_style}'
    
    return html_with_link, extracted_css


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "AI Landing Page Generator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks if app can serve traffic."""
    try:
        # Check if DSPy is configured (dspy imported at top)
        if not hasattr(dspy.settings, 'lm') or dspy.settings.lm is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "DSPy LM not configured"
                }
            )
        
        return {
            "status": "ready",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e)
            }
        )



def _convert_messages_to_langchain(messages_dicts):
    """Convert message dictionaries from frontend to LangChain message objects."""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    if not messages_dicts:
        return []
    
    langchain_messages = []
    for msg_dict in messages_dicts:
        role = msg_dict.get("role", "human")
        content = msg_dict.get("content", "")
        
        # Map role to appropriate message class
        if role in ["human", "user"]:
            langchain_messages.append(HumanMessage(content=content))
        elif role in ["ai", "assistant"]:
            langchain_messages.append(AIMessage(content=content))
        elif role == "system":
            langchain_messages.append(SystemMessage(content=content))
        else:
            # Default to human message
            langchain_messages.append(HumanMessage(content=content))
    
    return langchain_messages


def _convert_langchain_to_dict(messages):
    """Convert LangChain message objects to serializable dictionaries."""
    if not messages:
        return []
        
    serializable_messages = []
    for msg in messages:
        if hasattr(msg, 'content'):
            # Get content and ensure it's a string
            content = str(msg.content) if msg.content else ""
            
            # Truncate very long messages and remove problematic characters
            # Convert newlines to spaces to avoid JSON issues
            content = content.replace('\n', ' ').replace('\r', ' ')
            
            # Limit length to prevent huge payloads
            # We keep it reasonable for frontend context
            if len(content) > 1000:
                content = content[:997] + "..."
            
            # Map message class names to LangChain-compatible role names
            role_mapping = {
                'HumanMessage': 'user',
                'AIMessage': 'assistant',
                'SystemMessage': 'system',
                'FunctionMessage': 'function',
                'ToolMessage': 'tool'
            }
            
            class_name = msg.__class__.__name__
            role = role_mapping.get(class_name, 'user')  # Default to 'user' if unknown
            
            serializable_messages.append({
                "role": role,
                "content": content
            })
            
    return serializable_messages


# New LangGraph workflow endpoint
@app.post("/api/generate-website")
async def generate_website(request: GenerateWebsiteRequest):
    """
    Generate complete multi-page website using LangGraph workflow.
    
    Workflow steps:
    1. Planning: Generate website structure and strategy
    2. Image Description: Create targeted image descriptions
    3. Image Generation: Generate images with DALL-E 3
    4. HTML Generation: Create multi-page HTML/CSS
    
    Returns streaming response with progress updates.
    """
    logger.info("="  * 60)
    logger.info("LangGraph Website Generation - Request Received")
    logger.info(f"Description: {request.description[:100]}...")
    logger.info("=" * 60)
    
    if not request.description or len(request.description.strip()) < 10:
        logger.warning("Invalid request: Description too short")
        raise HTTPException(
            status_code=400,
            detail="Description must be at least 10 characters long"
        )
    
    async def event_stream():
        """Stream workflow progress as Server-Sent Events."""
        try:
            # Use provided thread_id or generate new one for conversation continuity
            thread_id_str = request.thread_id or str(int(time.time()))
            thread_id = {"configurable": {"thread_id": thread_id_str}}
            logger.info(f"Using thread_id: {thread_id_str}")
            
            # Check for existing state to handle updates vs new conversations
            # This ensures we don't overwrite existing plan/progress when user replies
            current_state = website_workflow.get_state(thread_id).values
            is_new_conversation = not current_state
            
            inputs = {}
            
            # Handle user intent (Approval vs Revision)
            latest_message_content = ""
            if request.messages and request.messages[-1].get("role") == "user":
                latest_message_content = request.messages[-1].get("content", "").lower().strip()
            
            user_intent = None
            if latest_message_content:
                # Check for approval keywords
                if latest_message_content in ["approve", "yes", "proceed", "looks good", "start building", "approve plan"]:
                    user_intent = "approve"
                elif current_state and current_state.get("awaiting_plan_approval"):
                    # If waiting for approval and not explicit approval, treat as feedback/revision
                    user_intent = "revise"
            
            if is_new_conversation:
                logger.info("Starting NEW conversation/workflow")
                # Initialize full state for new conversation
                inputs = {
                    "description": request.description,
                    "ready": False,
                    "business_plan": None,
                    "business_description": None,
                    "clarification_questions": None,
                    "reference_url": None,
                    "reference_analysis": None,
                    "plan": None,
                    "plan_json": None,
                    "template_styling": None,
                    "css_theme": None,
                    "design_system": None,
                    "awaiting_plan_approval": False,
                    "plan_approved": False,
                    "plan_revision_requested": False,
                    "plan_feedback": None,
                    "plan_version": 0,
                    "image_descriptions": None,
                    "image_urls": None,
                    "pages": None,
                    "folder_path": None,
                    "saved_files": None,
                    "current_step": "business_gathering",
                    "status": "in_progress",
                    "error": None,
                    "progress": 0,
                    "progress_message": "Starting website generation...",
                    "messages": _convert_messages_to_langchain(request.messages) if request.messages else []
                }
            else:
                logger.info("Resuming EXISTING conversation/workflow")
                # Update existing state
                inputs = {
                    "description": request.description,
                }
                
                # Append NEW messages only
                current_messages = current_state.get("messages", [])
                request_messages = request.messages or []
                
                if len(request_messages) > len(current_messages):
                    new_msgs = request_messages[len(current_messages):]
                    logger.info(f"Appending {len(new_msgs)} new messages to history")
                    inputs["messages"] = _convert_messages_to_langchain(new_msgs)
                
                # Apply intent updates
                if user_intent == "approve":
                    logger.info("ℹ️ User APPROVED the plan")
                    inputs["plan_approved"] = True
                    inputs["awaiting_plan_approval"] = False
                    inputs["plan_revision_requested"] = False
                    inputs["plan_feedback"] = None
                    inputs["status"] = "in_progress" # Resume workflow
                    
                elif user_intent == "revise":
                    logger.info("ℹ️ User requested PLAN REVISION")
                    inputs["plan_approved"] = False
                    inputs["awaiting_plan_approval"] = False 
                    inputs["plan_revision_requested"] = True
                    inputs["plan_feedback"] = latest_message_content
                    inputs["status"] = "in_progress" # Resume workflow
                
            # Use inputs as initial state (LangGraph will merge)
            initial_state = inputs
            
            # Stream workflow execution
            logger.info("Starting LangGraph workflow execution...")
            
            async for event in website_workflow.astream(initial_state, thread_id):
                # Extract state from event
                if isinstance(event, dict):
                    # Get the latest node's state
                    for node_name, node_state in event.items():
                        if isinstance(node_state, dict):
                            logger.info(f"Node '{node_name}' completed")
                            
                            # Skip sending intermediate "awaiting_input" events from business_gathering
                            # We'll send the complete event with questions after streaming finishes
                            if (node_name == "business_gathering" and 
                                node_state.get("status") == "awaiting_input" and 
                                not node_state.get("ready", True)):
                                logger.info("Skipping intermediate business gathering event (will send complete event with questions)")
                                continue
                            
                            # Send progress update
                            progress_data = {
                                "step": node_state.get("current_step", "unknown"),
                                "status": node_state.get("status", "in_progress"),
                                "progress": node_state.get("progress", 0),
                                "message": node_state.get("progress_message", ""),
                                "error": node_state.get("error")
                            }
                            
                            # Send as SSE
                            yield f"data: {json.dumps(progress_data)}\n\n"
                            
                            # Check for errors
                            if node_state.get("status") == "failed":
                                logger.error(f"Workflow failed: {node_state.get('error')}")
                                return
            
            # Get final state
            final_state = website_workflow.get_state(thread_id).values
            
            # Check if business gathering needs more information
            if not final_state.get("ready") and final_state.get("clarification_questions"):
                logger.info("Business gathering needs more information")
                
                # Convert LangChain messages to JSON-serializable format
                messages = final_state.get("messages", [])
                serializable_messages = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        # Get content and ensure it's a string
                        content = str(msg.content) if msg.content else ""
                        
                        # Truncate very long messages and remove problematic characters
                        # Convert newlines to spaces to avoid JSON issues
                        content = content.replace('\n', ' ').replace('\r', ' ')
                        
                        # Limit length to prevent huge payloads
                        if len(content) > 500:
                            content = content[:497] + "..."
                        
                        # Map message class names to LangChain-compatible role names
                        role_mapping = {
                            'HumanMessage': 'human',
                            'AIMessage': 'ai',
                            'SystemMessage': 'system',
                            'FunctionMessage': 'function',
                            'ToolMessage': 'tool'
                        }
                        
                        class_name = msg.__class__.__name__
                        role = role_mapping.get(class_name, 'human')  # Default to 'human' if unknown
                        
                        serializable_messages.append({
                            "role": role,
                            "content": content
                        })
                
                questions_result = {
                    "step": "business_gathering",  
                    "status": "awaiting_input",
                    "progress": 5,
                    "ready": False,
                    "questions": final_state.get("clarification_questions", []),
                    "thread_id": thread_id_str,  # Return thread_id for next request
                    "message": "Please provide more information",
                    "messages": serializable_messages  # Converted to JSON-serializable format
                }
                yield f"data: {json.dumps(questions_result)}\n\n"
                return
            
            # Check if workflow completed successfully
            status = final_state.get("status")
            
            if status == "completed":
                logger.info("✓ Website generation completed successfully")
                
                # Send final result
                result = {
                    "step": "complete",
                    "status": "completed",
                    "progress": 100,
                    "ready": True,
                    "thread_id": thread_id_str,
                    "message": "✓ Website generation complete",
                    "data": {
                        "pages": final_state.get("pages", {}),
                        "image_urls": final_state.get("image_urls", {}),
                        "plan": final_state.get("plan", {}),
                        "folder_path": final_state.get("folder_path"),
                        "saved_files": final_state.get("saved_files", {})
                    }
                }
                yield f"data: {json.dumps(result)}\n\n"
            
            elif status == "awaiting_approval":
                logger.info("Workflow paused for plan approval")
                
                # Extract plan details for frontend
                approval_data = {
                    "step": "plan_approval",
                    "status": "awaiting_approval",
                    "progress": final_state.get("progress", 22),
                    "thread_id": thread_id_str,
                    "message": final_state.get("progress_message", "Awaiting approval"),
                    "plan": final_state.get("plan"),
                    "design_system": final_state.get("design_system"),
                    "messages": _convert_langchain_to_dict(final_state.get("messages", [])) # Ensure messages are serialized
                }
                yield f"data: {json.dumps(approval_data)}\n\n"
                
            else:
                logger.error(f"Workflow did not complete successfully. Status: {status}")
                error_data = {
                    "step": "failed",
                    "status": "failed",
                    "progress": final_state.get("progress", 0),
                    "thread_id": thread_id_str,
                    "message": final_state.get("error", "Unknown error"),
                    "error": final_state.get("error")
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
            error_data = {
                "step": "failed",
                "status": "failed",
                "progress": 0,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    # Return streaming response
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for streaming
        }
    )

@app.post("/api/update-website", response_model=UpdateWebsiteResponse)
async def update_website(request: UpdateWebsiteRequest):
    """
    Smart Website Update: Update multi-page websites based on natural language instructions.
    
    This endpoint intelligently determines what to update based on the user's request:
    - Global styling (colors, fonts, spacing in style.css)
    - Individual page content (HTML)
    - Multiple pages at once
    - Combination of styling + content
    
    The API analyzes the request and applies updates accordingly, returning only the
    modified files.
    
    Optionally, if folder_path is provided, saves the updates directly to the website folder.
    """
    logger.info("=" * 60)
    logger.info("SMART WEBSITE UPDATE - Request Received")
    logger.info(f"Edit request: {request.edit_request[:100]}...")
    logger.info(f"Number of pages provided: {len(request.pages)}")
    logger.info(f"Pages: {list(request.pages.keys())}")
    logger.info(f"Global CSS provided: {bool(request.global_css)}")
    logger.info(f"Folder path provided: {bool(request.folder_path)}")
    logger.info(f"🔍 FOLDER PATH VALUE: {repr(request.folder_path)}")
    logger.info("=" * 60)
    
    # Validation
    if not request.edit_request or len(request.edit_request.strip()) < 5:
        logger.warning("Invalid request: Edit request too short")
        raise HTTPException(
            status_code=400,
            detail="Edit request must be at least 5 characters long"
        )
    
    if not request.pages or len(request.pages) == 0:
        logger.warning("Invalid request: No pages provided")
        raise HTTPException(
            status_code=400,
            detail="At least one page must be provided"
        )
    
    try:
        # Import WebsiteUpdater module
        from app.workflow_node.html_generation.dspy_modules import WebsiteUpdater
        
        logger.info("Initializing WebsiteUpdater module...")
        updater = WebsiteUpdater()
        
        # Apply smart updates
        logger.info("Analyzing and applying updates...")
        result = updater(
            pages=request.pages,
            global_css=request.global_css or "",
            edit_request=request.edit_request
        )
          
        updated_pages = result.get("updated_pages", {})
        updated_global_css = result.get("updated_global_css")
        changes_summary = result.get("changes_summary", "Updates applied")
        
        logger.info(f"Updates complete: {changes_summary}")
        logger.info(f"Updated pages: {list(updated_pages.keys())}")
        logger.info(f"Global CSS updated: {bool(updated_global_css)}")
        
        # Optional: Save to folder if path provided
        saved_folder_path = None
        
        logger.info("🔍 FILE SAVE CHECK:")
        logger.info(f"  folder_path exists: {bool(request.folder_path)}")
        logger.info(f"  folder_path value: {repr(request.folder_path)}")
        logger.info(f"  updated_pages exists: {bool(updated_pages)}")
        logger.info(f"  updated_global_css exists: {bool(updated_global_css)}")
        logger.info(f"  Will save: {bool(request.folder_path and (updated_pages or updated_global_css))}")
        
        if request.folder_path and (updated_pages or updated_global_css):
            try:
                logger.info(f"Saving updates to folder: {request.folder_path}")
                from app.file_manager import WebsiteFileManager
                
                file_manager = WebsiteFileManager()
                
                # Verify folder exists
                if not os.path.exists(request.folder_path):
                    logger.warning(f"Folder does not exist: {request.folder_path}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Folder path does not exist: {request.folder_path}"
                    )
                
                # Save updated pages
                if updated_pages:
                    for page_name, page_content in updated_pages.items():
                        html = page_content.get('html', '')
                        css  = page_content.get('css', '')

                        # Start with what the LLM returned — may already have <style> or <link>
                        html_final = html

                        # ── Re-link style.css if it already exists on disk ──────────────────
                        # The initial generation always creates style.css.
                        # The LLM may have removed the <link> tag during editing, so we
                        # always re-insert it when the file is present.
                        style_css_path = os.path.join(request.folder_path, "style.css")
                        if os.path.exists(style_css_path) and 'style.css' not in (html_final or ''):
                            if '</head>' in html_final:
                                html_final = html_final.replace(
                                    '</head>',
                                    '    <link rel="stylesheet" href="style.css">\n</head>'
                                )
                            logger.info(f"  Re-linked style.css in {page_name}.html")

                        # ── Embed page-specific CSS if it was stripped and not yet present ──
                        if css and css.strip() and '<style' not in (html_final or ''):
                            if '</head>' in html_final:
                                html_final = html_final.replace(
                                    '</head>',
                                    f'    <style>\n{css}\n    </style>\n</head>'
                                )
                            logger.info(f"  Embedded page CSS in {page_name}.html")

                        # ── If updated_global_css is being written, add link if missing ──────
                        if updated_global_css and 'style.css' not in (html_final or ''):
                            if '</head>' in html_final:
                                html_final = html_final.replace(
                                    '</head>',
                                    '    <link rel="stylesheet" href="style.css">\n</head>'
                                )

                        # Save HTML file
                        html_path = os.path.join(request.folder_path, f"{page_name}.html")
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_final)
                        logger.info(f"✓ Saved updated HTML: {html_path}")
                
                # Save updated global CSS
                if updated_global_css:
                    css_path = os.path.join(request.folder_path, "style.css")
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(updated_global_css)
                    logger.info(f"✓ Saved updated global CSS: {css_path}")
                
                saved_folder_path = request.folder_path
                logger.info(f"✓ All updates saved to: {saved_folder_path}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error saving to folder: {str(e)}", exc_info=True)
                # Don't fail the request, just log the error
                logger.warning("File saving failed, but updates are still returned in response")
        
        logger.info("✓ SMART WEBSITE UPDATE Complete")
        logger.info("=" * 60)
        
        return UpdateWebsiteResponse(
            updated_pages=updated_pages,
            updated_global_css=updated_global_css,
            changes_summary=changes_summary,
            folder_path=saved_folder_path,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart website update: {str(e)}", exc_info=True)
        
        # Check for rate limit or quota errors
        is_rate_limit_error = (
            (litellm and isinstance(e, litellm.RateLimitError)) or
            "RateLimitError" in str(type(e).__name__) or
            "rate limit" in str(e).lower() or
            "quota" in str(e).lower() or
            "exceeded" in str(e).lower()
        )
        
        if is_rate_limit_error:
            logger.warning("Rate limit/quota error in website update")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error updating website: {str(e)}"
        )



# ─────────────────────────────────────────────────────────────────────────────
# Export API  —  POST /api/export/{folder_name}
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/export/config")
async def get_export_config():
    """
    Returns the current export configuration (OUTPUT_PATH + OUTPUT_PATH_STYLE from .env).
    Useful for the frontend to show the user where exports will go.
    """
    output_path       = os.getenv("OUTPUT_PATH",       "").strip()
    output_path_style = os.getenv("OUTPUT_PATH_STYLE", "").strip()
    return {
        "output_path":       output_path       if output_path       else None,
        "output_path_style": output_path_style if output_path_style else None,
        "configured": bool(output_path),
        "message": (
            f"Export paths configured — site: {output_path or '(not set)'}, "
            f"theme: {output_path_style or '(not set)'}"
        )
    }


@app.post("/api/export/{folder_name}")
async def export_website(folder_name: str):
    """
    Export a generated website to the custom paths defined in .env.

    Copies TWO folders:
      • Content folder  → OUTPUT_PATH/<folder_name>
      • Theme folder    → OUTPUT_PATH_STYLE/<folder_name>theme
        (the theme folder lives in webtemplates/ as <folder_name>theme)

    This endpoint does NOT run automatically — it must be explicitly called by
    the user/frontend after website generation is complete.

    Args:
        folder_name: Name of the generated website content folder
                     (e.g. 'mysite_20260225_123456')

    Returns:
        JSON with success status, source/destination paths, and exported file lists
    """
    import shutil

    logger.info("=" * 60)
    logger.info(f"EXPORT WEBSITE - Request received for folder: {folder_name}")
    logger.info("=" * 60)

    # ── 1. Read paths from .env ────────────────────────────────────────────────
    output_path       = os.getenv("OUTPUT_PATH",       "").strip()
    output_path_style = os.getenv("OUTPUT_PATH_STYLE", "").strip()

    if not output_path:
        logger.warning("Export failed: OUTPUT_PATH is not configured in .env")
        raise HTTPException(
            status_code=400,
            detail=(
                "OUTPUT_PATH is not configured in your .env file. "
                "Please set OUTPUT_PATH to the folder where you want to export websites. "
                "Example: OUTPUT_PATH=\"C:\\Users\\YourName\\Desktop\\MyWebsites\""
            )
        )

    # ── 2. Sanitize folder_name (prevent directory traversal) ─────────────────
    folder_name = os.path.basename(folder_name.strip())
    if not folder_name:
        raise HTTPException(status_code=400, detail="Invalid folder name.")

    theme_folder_name = folder_name + "theme"

    # ── 3. Validate source folders exist in webtemplates/ ────────────────────
    source_content = os.path.join(WEBTEMPLATES_DIR, folder_name)
    source_theme   = os.path.join(WEBTEMPLATES_DIR, theme_folder_name)

    if not os.path.exists(source_content):
        logger.warning(f"Export failed: Source content folder not found: {source_content}")
        raise HTTPException(
            status_code=404,
            detail=f"Website folder '{folder_name}' not found. "
                   f"Please make sure the website was generated successfully first."
        )

    if not os.path.isdir(source_content):
        raise HTTPException(
            status_code=400,
            detail=f"'{folder_name}' is not a valid website folder."
        )

    # ── 4. Ensure destination base directories exist ───────────────────────────
    for path_label, path_val in [("OUTPUT_PATH", output_path),
                                  ("OUTPUT_PATH_STYLE", output_path_style)]:
        if not path_val:
            continue
        try:
            os.makedirs(path_val, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create {path_label} '{path_val}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Cannot create or access '{path_val}'. "
                       f"Check the path is valid and you have write permission. Error: {str(e)}"
            )

    # ── 5. Define destination paths ────────────────────────────────────────────
    dest_content = os.path.join(output_path, folder_name)

    # Theme destination: use OUTPUT_PATH_STYLE if set, otherwise fall back to OUTPUT_PATH
    theme_base   = output_path_style if output_path_style else output_path
    dest_theme   = os.path.join(theme_base, theme_folder_name)

    for dest, label in [(dest_content, "content"), (dest_theme, "theme")]:
        if os.path.exists(dest):
            logger.warning(f"Export path already exists ({label}): {dest}")
            raise HTTPException(
                status_code=409,
                detail=f"A folder already exists at '{dest}'. "
                       f"Please rename or remove the existing folder first."
            )

    # ── 6. Copy content folder → OUTPUT_PATH ──────────────────────────────────
    try:
        logger.info(f"Copying content: {source_content} → {dest_content}")
        shutil.copytree(source_content, dest_content)
        logger.info(f"✓ Content export successful: {dest_content}")
    except Exception as e:
        logger.error(f"Content export copy failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Export failed while copying content folder: {str(e)}"
        )

    # ── 7. Copy theme folder → OUTPUT_PATH_STYLE (if it exists) ───────────────
    theme_exported_files = []
    dest_theme_final = None

    if os.path.exists(source_theme) and os.path.isdir(source_theme):
        try:
            logger.info(f"Copying theme: {source_theme} → {dest_theme}")
            shutil.copytree(source_theme, dest_theme)
            logger.info(f"✓ Theme export successful: {dest_theme}")
            dest_theme_final = dest_theme

            for root, dirs, files in os.walk(dest_theme):
                for file in files:
                    file_full = os.path.join(root, file)
                    theme_exported_files.append(
                        os.path.relpath(file_full, dest_theme)
                    )
            theme_exported_files.sort()
        except Exception as e:
            logger.error(f"Theme export copy failed: {e}", exc_info=True)
            # Non-fatal — content already exported; report warning in response
            logger.warning("Theme folder copy failed, but content was exported successfully.")
    else:
        logger.warning(
            f"Theme folder '{theme_folder_name}' not found in webtemplates/ — skipping theme export."
        )

    # ── 8. Collect list of exported content files ─────────────────────────────
    exported_files = []
    for root, dirs, files in os.walk(dest_content):
        for file in files:
            file_full = os.path.join(root, file)
            exported_files.append(os.path.relpath(file_full, dest_content))
    exported_files.sort()

    logger.info(f"Exported {len(exported_files)} content files → {dest_content}")
    logger.info(f"Exported {len(theme_exported_files)} theme files  → {dest_theme_final}")
    logger.info("=" * 60)

    return {
        "success": True,
        "message": "✓ Website exported successfully to your system!",
        "folder_name": folder_name,
        # Content folder
        "source_path":       source_content,
        "destination_path":  dest_content,
        "total_files":       len(exported_files),
        "exported_files":    exported_files,
        # Theme folder
        "theme_folder_name":        theme_folder_name,
        "theme_source_path":        source_theme if os.path.exists(source_theme) else None,
        "theme_destination_path":   dest_theme_final,
        "theme_total_files":        len(theme_exported_files),
        "theme_exported_files":     theme_exported_files,
    }


@app.get("/api/export/list")
async def list_exportable_websites():
    """
    Lists all generated websites available in webtemplates/ that can be exported.
    Also shows whether OUTPUT_PATH is configured.
    """
    output_path = os.getenv("OUTPUT_PATH", "").strip()

    # List all folders in webtemplates/
    websites = []
    if os.path.exists(WEBTEMPLATES_DIR):
        for name in sorted(os.listdir(WEBTEMPLATES_DIR)):
            folder = os.path.join(WEBTEMPLATES_DIR, name)
            if os.path.isdir(folder):
                # Get metadata if available
                metadata_path = os.path.join(folder, "metadata.json")
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                    except Exception:
                        pass

                # Count files
                file_count = sum(len(files) for _, _, files in os.walk(folder))

                websites.append({
                    "folder_name": name,
                    "created_at": metadata.get("created_at"),
                    "description": metadata.get("description"),
                    "pages": metadata.get("pages", []),
                    "file_count": file_count,
                    "output_format": metadata.get("output_format", "html"),
                })

    return {
        "export_configured": bool(output_path),
        "output_path": output_path if output_path else None,
        "total_websites": len(websites),
        "websites": websites,
    }


# Run the application (uvicorn imported at top)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)