"""
LangGraph workflow definition for website generation.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.workflow_state import WorkflowState

# Import all workflow nodes from their modular structure
from app.workflow_node.business_gathering import business_gathering_node
from app.workflow_node.planning_node.node import planning_node
from app.workflow_node.plan_approval import plan_approval_node
from app.workflow_node.image_description_node.node import image_description_node
from app.workflow_node.image_generation_node.node import image_generation_node
from app.workflow_node.html_generation.node import html_generation_node
from app.workflow_node.file_storage.node import file_storage_node

# Note: html_validation_node is not currently used in the workflow
# It exists in workflow_nodes.py but is not part of the active workflow graph


def should_continue_to_planning(state: WorkflowState) -> str:
    """
    Route based on whether we have enough business information.
    Returns 'planning' if ready, otherwise END to wait for user input.
    """
    if state.get("ready"):
        return "planning"
    return END


def should_proceed_after_planning(state: WorkflowState) -> str:
    """
    Route after planning based on whether approval is required.
    Returns 'plan_approval' if awaiting approval, otherwise 'image_description' for direct execution.
    """
    if state.get("awaiting_plan_approval"):
        return "plan_approval"
    # Backward compatibility: if no approval flag, proceed directly
    return "image_description"


def handle_plan_approval(state: WorkflowState) -> str:
    """
    Route based on user's approval decision.
    Returns:
    - 'image_description' if plan is approved (proceed to generation)
    - 'planning' if revision is requested (regenerate plan with feedback)
    - END if still waiting for user input
    """
    if state.get("plan_approved"):
        return "image_description"
    
    if state.get("plan_revision_requested"):
        return "planning"
    
    # Still waiting for user input
    return END


def create_website_workflow():
    """
    Create and compile the LangGraph workflow for website generation.
    
    Workflow:
    START -> business_gathering -> [if ready] -> planning -> plan_approval -> [if approved] -> image_generation -> html_generation -> file_storage -> END
    
    Approval workflow:
    - After planning: route to plan_approval (if awaiting_plan_approval=True)
    - After plan_approval:
      * If approved -> image_generation (local images from IMAGES_PATH)
      * If revision requested -> back to planning with feedback
      * Otherwise -> END (wait for user)
    """
    # Create workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("business_gathering", business_gathering_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("plan_approval", plan_approval_node)
    workflow.add_node("image_description", image_description_node)
    workflow.add_node("image_generation", image_generation_node)
    workflow.add_node("html_generation", html_generation_node)
    workflow.add_node("file_storage", file_storage_node)
    
    # Define edges
    # Start with business gathering
    workflow.add_edge(START, "business_gathering")
    
    # Conditional routing: proceed to planning only if ready
    workflow.add_conditional_edges(
        "business_gathering",
        should_continue_to_planning,
        {
            "planning": "planning",
            END: END
        }
    )
    
    # Conditional routing after planning: approval gate or direct execution
    workflow.add_conditional_edges(
        "planning",
        should_proceed_after_planning,
        {
            "plan_approval": "plan_approval",
            "image_description": "image_description"
        }
    )

    # Conditional routing after approval: approved, revision, or wait
    workflow.add_conditional_edges(
        "plan_approval",
        handle_plan_approval,
        {
            "image_description": "image_description",
            "planning": "planning",
            END: END
        }
    )

    # Linear pipeline after image_description
    workflow.add_edge("image_description", "image_generation")
    workflow.add_edge("image_generation", "html_generation")
    workflow.add_edge("html_generation", "file_storage")
    workflow.add_edge("file_storage", END)
    
    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    compiled_workflow = workflow.compile(checkpointer=checkpointer)
    
    return compiled_workflow


# Create global workflow instance
website_workflow = create_website_workflow()

