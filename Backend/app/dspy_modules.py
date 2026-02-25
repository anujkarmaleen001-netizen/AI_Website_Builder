"""
DEPRECATED: This file has been refactored into modular workflow nodes.

The DSPy modules previously in this file have been moved to their respective workflow node folders:
- WebsitePlanner -> app.workflow_node.planning_node.dspy_modules
- ImageDescriptionGenerator -> app.workflow_node.image_description_node.dspy_modules
- MultiPageGenerator -> app.workflow_node.html_generation.dspy_modules

Please update your imports to use the new locations.

This file is kept for backward compatibility but will be removed in a future version.
"""

# For backward compatibility, re-export the modules from their new locations
from app.workflow_node.planning_node.dspy_modules import WebsitePlanner
from app.workflow_node.image_description_node.dspy_modules import ImageDescriptionGenerator
from app.workflow_node.html_generation.dspy_modules import MultiPageGenerator

__all__ = ['WebsitePlanner', 'ImageDescriptionGenerator', 'MultiPageGenerator']
