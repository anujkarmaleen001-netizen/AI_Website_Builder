from pydantic import BaseModel
from typing import Dict, Optional


class GenerateWebsiteRequest(BaseModel):
    description: str
    thread_id: Optional[str] = None  # For conversation continuity across multiple requests
    messages: Optional[list] = None  # Previous conversation messages

class WebsitePlanResponse(BaseModel):
    plan: Dict
    status: str
    progress: int
    progress_message: str

class WebsiteGenerationResponse(BaseModel):
    pages: Dict[str, Dict[str, str]]
    image_urls: Dict[str, str]
    plan: Dict
    status: str
    progress: int
    progress_message: str

class UpdateWebsiteRequest(BaseModel):
    pages: Dict[str, Dict[str, str]]
    global_css: Optional[str] = None
    edit_request: str
    folder_path: Optional[str] = None

class UpdateWebsiteResponse(BaseModel):
    updated_pages: Dict[str, Dict[str, str]]
    updated_global_css: Optional[str] = None
    changes_summary: str
    folder_path: Optional[str] = None