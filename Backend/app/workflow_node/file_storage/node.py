"""
File storage node for website generation workflow.
Saves generated website files as static PHP partials in a structured folder.
"""
import logging
import os

from app.workflow_state import WorkflowState
from app.file_manager import WebsiteFileManager

# Configure logging
logger = logging.getLogger(__name__)


def file_storage_node(state: WorkflowState) -> WorkflowState:
    """
    Step 4: Save generated static PHP files to structured folders.

    Output structure:
        <website_folder>/
            template/
                main.php       <- HTML shell with PHP view() includes
                header.php     <- shared <header> partial
                footer.php     <- shared <footer> + JS partial
            home.php           <- body content for home page
            about.php          <- body content for about page (multi-page)
            assets/
                css/
                    style.css  <- merged CSS for all pages
            metadata.json
    """
    logger.info("Starting file storage node (PHP static mode)...")

    try:
        pages = state["pages"]
        plan = state.get("plan")
        description = state.get("description")
        image_urls = state.get("image_urls")
        css_theme = state.get("css_theme")

        # Extract website name from description or plan
        website_name = None
        if plan and "name" in plan:
            website_name = plan["name"]
        elif description:
            words = description.split()[:3]
            website_name = "_".join(words)

        # Initialize file manager
        file_manager = WebsiteFileManager()

        # Save complete website as PHP static structure
        logger.info(f"Saving PHP website with {len(pages)} pages...")
        result = file_manager.save_complete_website_php(
            pages=pages,
            plan=plan,
            description=description,
            website_name=website_name,
            image_urls=image_urls,
            css_theme=css_theme
        )

        folder_path = result['folder_path']
        saved_files = result['saved_files']

        logger.info(f"PHP website saved to: {folder_path}")
        logger.info(f"Saved {len(saved_files)} PHP content files")

        return {
            **state,
            "folder_path": folder_path,
            "saved_files": saved_files,
            "current_step": "complete",
            "status": "completed",
            "progress": 100,
            "progress_message": (
                f"Website generation complete: {len(saved_files)} PHP pages saved to "
                f"{os.path.basename(folder_path)}"
            )
        }

    except Exception as e:
        logger.error(f"File storage node error: {str(e)}")
        return {
            **state,
            "current_step": "complete",
            "status": "completed",
            "progress": 100,
            "progress_message": f"HTML generated but file storage failed: {str(e)}",
            "error": f"File storage warning: {str(e)}"
        }
