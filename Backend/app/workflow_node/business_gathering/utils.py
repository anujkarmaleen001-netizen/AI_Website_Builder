"""
Utility functions for business gathering node.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json(text) -> dict:
    """Extract JSON from text, handling markdown code fences and extra whitespace."""
    # Handle non-string inputs (like empty lists from Claude)
    if not isinstance(text, str):
        logger.warning(f"extract_json received non-string input: {type(text)} = {text}")
        if isinstance(text, list) and len(text) == 0:
            # Empty list - return "not ready" without questions
            # The business_gathering_node will handle asking for more info
            return {
                "ready": False,
                "questions": [],
                "business_plan": ""
            }
        # Try to convert to string
        text = str(text)
    
    text = text.strip()
    
    # Handle malformed/truncated responses
    if len(text) < 10 or not any(c in text for c in ['{', 'ready', 'questions']):
        logger.error(f"Malformed LLM response (too short or missing JSON markers): {text}")
        return {
            "ready": False,
            "questions": ["Please provide more details about your business and website requirements."],
            "business_plan": ""
        }
    
    # Try to extract JSON from markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    
    # Try to extract JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {text[:200]}")
        logger.error(f"JSON decode error: {e}")
        # Return a safe fallback instead of crashing
        return {
            "ready": False,
            "questions": ["I had trouble processing that. Please describe your business and website needs in more detail."],
            "business_plan": ""
        }
