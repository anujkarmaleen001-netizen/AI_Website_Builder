"""
DEPRECATED: This file has been refactored into modular workflow nodes.

The DSPy signatures previously in this file have been moved to their respective workflow node folders:
- WebsitePlannerSignature -> app.workflow_node.planning_node.signature
- ImageDescriptionSignature -> app.workflow_node.image_description_node.signature
- MultiPageSignature -> app.workflow_node.html_generation.signature

Please update your imports to use the new locations.

This file is kept for backward compatibility but will be removed in a future version.
"""

# For backward compatibility, re-export the signatures from their new locations
from app.workflow_node.planning_node.signature import WebsitePlannerSignature
from app.workflow_node.image_description_node.signature import ImageDescriptionSignature
from app.workflow_node.html_generation.signature import MultiPageSignature

__all__ = ['WebsitePlannerSignature', 'ImageDescriptionSignature', 'MultiPageSignature']
