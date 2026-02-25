"""
DEPRECATED: This file has been refactored into modular workflow nodes.

All workflow node functions previously in this file have been moved to their respective workflow node folders:

NODE FUNCTIONS (moved to workflow_node/*/node.py):
- planning_node -> app.workflow_node.planning_node.node
- image_description_node -> app.workflow_node.image_description_node.node  
- image_generation_node -> app.workflow_node.image_generation_node.node
- html_generation_node -> app.workflow_node.html_generation.node
- file_storage_node -> app.workflow_node.file_storage.node

DSPy MODULES (moved to workflow_node/*/dspy_modules.py):
- WebsitePlanner -> app.workflow_node.planning_node.dspy_modules
- ImageDescriptionGenerator -> app.workflow_node.image_description_node.dspy_modules
- MultiPageGenerator -> app.workflow_node.html_generation.dspy_modules

Please update your imports to use the new locations.

This file is kept for backward compatibility but will be removed in a future version.
"""

# For backward compatibility, re-export the node functions from their new locations
from app.workflow_node.planning_node.node import planning_node
from app.workflow_node.image_description_node.node import image_description_node
from app.workflow_node.image_generation_node.node import image_generation_node
from app.workflow_node.html_generation.node import html_generation_node
from app.workflow_node.file_storage.node import file_storage_node

__all__ = [
    'planning_node',
    'image_description_node',
    'image_generation_node',
    'html_generation_node',
    'file_storage_node'
]

# Note: html_validation_node was defined in the original file but is not currently used
# in the active workflow. It has not been migrated to the modular structure.
