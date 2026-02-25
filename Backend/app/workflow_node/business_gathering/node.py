"""
Business gathering workflow node.

Gathers and validates business information through iterative conversation.
Detects reference URLs and integrates web scraping for design inspiration.
"""
import logging
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage

from app.workflow_state import WorkflowState
from app.web_scraper_service import (
    detect_url_in_text,
    scrape_and_analyze_reference,
    extract_design_insights
)
from .prompts import BUSINESS_GATHERING_SYSTEM_PROMPT
from .utils import extract_json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LLM for business gathering
api_key = os.getenv("OPENAI_API_KEY_PLAN")
business_gathering_llm = init_chat_model(model="openai:gpt-4o", api_key=api_key)


async def business_gathering_node(state: WorkflowState) -> WorkflowState:
    """
    Step 0: Gather and validate business information.
    Asks clarifying questions if needed, or proceeds if sufficient information is provided.
    Also detects reference URLs in user messages and runs web scraping for design inspiration.
    """
    logger.info("Starting business gathering node...")
    
    # Idempotency check: If business gathering is already done, skip
    if state.get("ready"):
        logger.info("Business gathering already complete (ready=True). Skipping to preserve state.")
        return state
    
    try:
        # Get conversation messages from state
        messages = state.get("messages", [])
        description = state.get("description", "")
        
        logger.info(f"Existing messages: {len(messages)}")
        logger.info(f"New description: {description[:100] if description else 'None'}...")
        
        # Build message history
        if not messages:
            # First time - create initial message from description
            if description:
                messages = [HumanMessage(content=description)]
                logger.info("Created initial message from description")
            else:
                # No description at all - create a message asking for information
                logger.info("No description provided, creating initial request message")
                messages = [HumanMessage(content="I want to create a website but I need help figuring out what I need.")]
        else:
            # Subsequent calls - append new user input to message history
            if description:
                # Check if this is a new message (not already in history)
                if not messages or not isinstance(messages[-1], HumanMessage) or messages[-1].content != description:
                    messages = messages + [HumanMessage(content=description)]
                    logger.info("Appended new user message to conversation history")
        
        # ========================================
        # REFERENCE URL DETECTION & SCRAPING
        # ========================================
        reference_url = state.get("reference_url")
        reference_analysis = state.get("reference_analysis")
        
        # Check if user provided a new reference URL (only scrape if not already done)
        if description and not reference_analysis:
            detected_url = detect_url_in_text(description)
            
            if detected_url:
                logger.info(f"🔍 Reference URL detected: {detected_url}")
                reference_url = detected_url
                
                try:
                    # Run scraping and analysis asynchronously
                    logger.info(f"🌐 Scraping reference site: {detected_url}")
                    reference_data = await scrape_and_analyze_reference(
                        url=detected_url,
                        max_pages=5,
                        timeout=60.0
                    )
                    
                    if reference_data.get('status') == 'completed':
                        reference_analysis = reference_data
                        design_insights = extract_design_insights(reference_data)
                        
                        logger.info(f"✓ Reference site analysis complete")
                        
                        # Inject design insights into conversation as system context
                        insight_message = (
                            f"[REFERENCE SITE ANALYSIS]\n"
                            f"I've analyzed the reference website: {detected_url}\n\n"
                            f"Design Insights Extracted:\n{design_insights}\n\n"
                            f"I'll use these patterns as design inspiration for your website."
                        )
                        messages = messages + [AIMessage(content=insight_message)]
                        
                    elif reference_data.get('status') == 'partial':
                        reference_analysis = reference_data
                        logger.warning(f"⚠ Partial reference analysis: {reference_data.get('message', 'Limited data')}")
                        
                        messages = messages + [AIMessage(content=(
                            f"I tried to analyze {detected_url} but could only extract limited data. "
                            f"I'll proceed with what I have and focus on your requirements."
                        ))]
                    else:
                        logger.warning(f"⚠ Reference scraping status: {reference_data.get('status')}")
                        messages = messages + [AIMessage(content=(
                            f"I wasn't able to fully analyze {detected_url}, but no worries! "
                            f"I'll create a great website based on your requirements."
                        ))]
                        
                except Exception as scrape_error:
                    logger.error(f"Reference scraping failed: {str(scrape_error)}")
                    # Don't fail the workflow - just continue without reference
                    messages = messages + [AIMessage(content=(
                        f"I couldn't analyze the reference site ({detected_url}), "
                        f"but I'll proceed with designing your website based on your description."
                    ))]
        
        # ========================================
        # LLM BUSINESS GATHERING
        # ========================================
        
        # Call LLM to analyze business information with full conversation context
        logger.info(f"Analyzing business information with {len(messages)} messages...")
        
        response = await business_gathering_llm.ainvoke(
            [BUSINESS_GATHERING_SYSTEM_PROMPT] + messages
        )
        
        # Debug: Log response details
        logger.info(f"LLM Response type: {type(response)}")
        logger.info(f"LLM Response content preview: {response.content[:200] if isinstance(response.content, str) else response.content}")
        
        # Extract and parse JSON from response
        data = extract_json(response.content)
        
        # Check if we're ready to proceed
        if not data.get("ready"):
            # Need more information - ask questions
            questions = data.get("questions", [])
            
            questions_text = "\n".join(f"- {q}" for q in questions)
            content = f"I need more information:\n{questions_text}"
            
            logger.info(f"Business information insufficient. Asking {len(questions)} questions.")
            
            return {
                **state,
                "ready": False,
                "clarification_questions": questions,
                "current_step": "business_gathering",
                "status": "awaiting_input",
                "progress": 5,
                "progress_message": "Waiting for additional business information",
                "messages": messages + [AIMessage(content=content)],
                "reference_url": reference_url,
                "reference_analysis": reference_analysis,
            }
        
        # We have enough information - proceed
        business_plan = data.get("business_plan", "")
        logger.info(f"✓ Business information gathered successfully")
        logger.info(f"Business plan: {business_plan[:200]}...")
        
        return {
            **state,
            "ready": True,
            "business_plan": business_plan,
            "clarification_questions": [],
            "current_step": "planning",
            "status": "in_progress",
            "progress": 10,
            "progress_message": "✓ Business information gathered, proceeding to planning",
            "messages": messages + [AIMessage(content=f"Great! I have enough information to proceed. Here's my understanding:\n\n{business_plan}")],
            "reference_url": reference_url,
            "reference_analysis": reference_analysis,
        }
        
    except Exception as e:
        logger.error(f"Business gathering node error: {str(e)}")
        return {
            **state,
            "current_step": "failed",
            "status": "failed",
            "error": f"Business gathering failed: {str(e)}",
            "progress": 0,
            "progress_message": f"✗ Business gathering failed: {str(e)}"
        }
