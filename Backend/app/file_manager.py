"""
File manager for website template storage.
Handles creation of website folders and file storage in webtemplates directory.
"""
import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class WebsiteFileManager:
    """Manages website file storage in structured folders."""
    
    def __init__(self, base_templates_dir: str = None):
        """
        Initialize the file manager.
        
        Args:
            base_templates_dir: Base directory for storing website templates.
                              Defaults to Backend/webtemplates
        """
        if base_templates_dir is None:
            # Get the Backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_templates_dir = os.path.join(backend_dir, "webtemplates")
        
        self.base_dir = base_templates_dir
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"WebsiteFileManager initialized with base directory: {self.base_dir}")
    
    def create_website_folder(self, website_name: str = None) -> str:
        """
        Create a unique folder for a website.
        
        Args:
            website_name: Optional name for the website. If not provided, 
                         generates a timestamp-based name.
        
        Returns:
            Absolute path to the created website folder.
        """
        if website_name is None:
            # Generate timestamp-based folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            website_name = f"website_{timestamp}"
        else:
            # Sanitize website name (remove special characters)
            website_name = re.sub(r'[^\w\s-]', '', website_name)
            website_name = re.sub(r'[\s]+', '_', website_name)
            
            # Add timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            website_name = f"{website_name}_{timestamp}"
        
        website_folder = os.path.join(self.base_dir, website_name)
        os.makedirs(website_folder, exist_ok=True)
        
        logger.info(f"Created website folder: {website_folder}")
        return website_folder
    
    def extract_css_from_html(self, html: str) -> Tuple[str, str]:
        """
        Extract CSS from HTML <style> tags and create separate CSS file.
        
        Args:
            html: HTML content containing <style> tags
        
        Returns:
            Tuple of (html_without_style_tags, extracted_css)
        """
        # Pattern to match <style> tags with optional attributes
        style_pattern = r'<style[^>]*>(.*?)</style>'
        
        # Extract all CSS content from style tags
        css_matches = re.findall(style_pattern, html, re.DOTALL | re.IGNORECASE)
        extracted_css = '\n\n'.join(css_matches).strip()
        
        # Remove all style tags from HTML
        html_without_style = re.sub(style_pattern, '', html, flags=re.DOTALL | re.IGNORECASE)
        
        return html_without_style, extracted_css
    
    def add_css_link_to_html(self, html: str, css_filename: str = "style.css") -> str:
        """
        Add CSS link tag to HTML if not present.
        
        Args:
            html: HTML content
            css_filename: Name of the CSS file to link
        
        Returns:
            HTML with CSS link tag added
        """
        link_tag = f'<link rel="stylesheet" href="{css_filename}">'
        
        # Check if link tag already exists
        if css_filename in html:
            return html
        
        # Try to insert before </head>
        if '</head>' in html.lower():
            html = re.sub(
                r'(</head>)',
                f'    {link_tag}\n    \\1',
                html,
                flags=re.IGNORECASE,
                count=1
            )
        # Fallback: insert at beginning of <body>
        elif '<body' in html.lower():
            html = re.sub(
                r'(<body[^>]*>)',
                f'\\1\n    {link_tag}',
                html,
                flags=re.IGNORECASE,
                count=1
            )
        else:
            # Last fallback: prepend to HTML
            html = f'{link_tag}\n{html}'
        
        return html
    
    def save_website_files(
        self,
        pages: Dict[str, Dict[str, str]],
        website_folder: str,
        create_global_css: bool = True,
        global_css_theme: str = None
    ) -> Dict[str, str]:
        """
        Save all website pages and CSS files to the website folder.
        
        Args:
            pages: Dictionary mapping page_name -> {html: str, css: str}
            website_folder: Path to the website folder
            create_global_css: If True, creates a single global style.css file.
                             If False, creates separate CSS files for each page.
            global_css_theme: Optional pre-generated CSS theme for the entire website.
                            If provided, this will be used instead of extracting CSS from pages.
        
        Returns:
            Dictionary mapping page_name -> saved_file_path
        """
        saved_files = {}
        all_css_content = []
        
        # Use global CSS theme if provided, otherwise collect from pages
        if create_global_css:
            if global_css_theme:
                # Use the provided global CSS theme
                logger.info("Using pre-generated global CSS theme")
                global_css = global_css_theme
            else:
                # Fallback: collect CSS from individual pages
                logger.info("No global CSS theme provided, extracting from pages")
                for page_name, page_content in pages.items():
                    # Get CSS from the page_content
                    css = page_content.get('css', '')
                    html = page_content.get('html', '')
                    
                    # Extract additional CSS from HTML if present
                    html_clean, extracted_css = self.extract_css_from_html(html)
                    
                    # Combine CSS
                    combined_css = css
                    if extracted_css:
                        combined_css = f"{css}\n\n{extracted_css}" if css else extracted_css
                    
                    if combined_css:
                        all_css_content.append(f"/* CSS for {page_name} page */\n{combined_css}")
                
                global_css = '\n\n'.join(all_css_content)
            
            # Save global CSS file
            if global_css:
                css_path = os.path.join(website_folder, "style.css")
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(global_css)
                logger.info(f"Saved global CSS file: {css_path} ({len(global_css)} chars)")
        
        # Second pass: save HTML files
        for page_name, page_content in pages.items():
            html = page_content.get('html', '')
            css = page_content.get('css', '')
            
            # Clean HTML and extract CSS
            html_clean, extracted_css = self.extract_css_from_html(html)
            
            # Add CSS link to HTML
            if create_global_css:
                html_final = self.add_css_link_to_html(html_clean, "style.css")
            else:
                # Create separate CSS file for this page
                page_css = f"{css}\n\n{extracted_css}" if css else extracted_css
                if page_css:
                    css_filename = f"{page_name}.css"
                    css_path = os.path.join(website_folder, css_filename)
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(page_css)
                    logger.info(f"Saved CSS file: {css_path}")
                    html_final = self.add_css_link_to_html(html_clean, css_filename)
                else:
                    html_final = html_clean
            
            # Save HTML file
            html_filename = f"{page_name}.html"
            html_path = os.path.join(website_folder, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_final)
            
            saved_files[page_name] = html_path
            logger.info(f"Saved HTML file: {html_path}")
        
        return saved_files
    
    def fix_internal_links(self, website_folder: str, pages: List[str]):
        """
        Fix internal page links in all HTML files to ensure proper navigation.
        Updates links like <a href="about.html"> to work correctly.
        
        Args:
            website_folder: Path to the website folder
            pages: List of page names (without .html extension)
        """
        for page_name in pages:
            html_path = os.path.join(website_folder, f"{page_name}.html")
            
            if not os.path.exists(html_path):
                logger.warning(f"HTML file not found for link fixing: {html_path}")
                continue
            
            # Read HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Fix links to other pages
            # Pattern: href="page_name" or href="page_name.html" or href="#"
            for target_page in pages:
                # Replace href="page_name" with href="page_name.html"
                html_content = re.sub(
                    rf'href=["\']({target_page})(["\'])',
                    rf'href="\1.html\2',
                    html_content,
                    flags=re.IGNORECASE
                )
            
            # Write updated HTML back
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Fixed internal links in: {html_path}")
    
    def create_index_html(self, website_folder: str, home_page: str = "home"):
        """
        Create an index.html file that redirects to the home page.
        
        Args:
            website_folder: Path to the website folder
            home_page: Name of the home page (without .html extension)
        """
        index_path = os.path.join(website_folder, "index.html")
        redirect_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="0; url={home_page}.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>If you are not redirected automatically, <a href="{home_page}.html">click here</a>.</p>
</body>
</html>
"""
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(redirect_html)
        
        logger.info(f"Created index.html redirect file: {index_path}")
    
    def save_metadata(self, website_folder: str, metadata: Dict):
        """
        Save website metadata (plan, description, etc.) to a JSON file.
        
        Args:
            website_folder: Path to the website folder
            metadata: Dictionary containing website metadata
        """
        metadata_path = os.path.join(website_folder, "metadata.json")
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata file: {metadata_path}")
    
    def save_complete_website(
        self,
        pages: Dict[str, Dict[str, str]],
        plan: Dict = None,
        description: str = None,
        website_name: str = None,
        image_urls: Dict[str, str] = None,
        css_theme: str = None
    ) -> Dict[str, any]:
        """
        Complete workflow to save a website with all files and proper structure.
        
        Args:
            pages: Dictionary mapping page_name -> {html: str, css: str}
            plan: Website plan dictionary
            description: Business/website description
            website_name: Optional custom name for the website
            image_urls: Dictionary of image URLs used in the website
            css_theme: Optional pre-generated global CSS theme
        
        Returns:
            Dictionary containing:
                - folder_path: Path to the website folder
                - saved_files: Dictionary of saved file paths
                - metadata_path: Path to metadata file
        """
        # Create website folder
        website_folder = self.create_website_folder(website_name)
        
        # Save all pages and CSS (using global CSS theme if provided)
        saved_files = self.save_website_files(
            pages, 
            website_folder, 
            create_global_css=True,
            global_css_theme=css_theme
        )
        
        # Fix internal links
        page_names = list(pages.keys())
        self.fix_internal_links(website_folder, page_names)
        
        # Create index.html redirect (assumes 'home' is the main page, fallback to first page)
        home_page = 'home' if 'home' in pages else page_names[0]
        self.create_index_html(website_folder, home_page)
        
        # Save metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'description': description,
            'plan': plan,
            'pages': page_names,
            
            'image_urls': image_urls or {},
            'has_global_css_theme': bool(css_theme)
        }
        self.save_metadata(website_folder, metadata)
        
        logger.info(f"✓ Website saved successfully to: {website_folder}")
        
        return {
            'folder_path': website_folder,
            'saved_files': saved_files,
            'metadata_path': os.path.join(website_folder, "metadata.json"),
            'pages': page_names
        }

    # -------------------------------------------------------------------------
    # PHP Static Output
    # -------------------------------------------------------------------------

    def save_complete_website_php(
        self,
        pages: Dict[str, Dict[str, str]],
        plan: Dict = None,
        description: str = None,
        website_name: str = None,
        image_urls: Dict[str, str] = None,
        css_theme: str = None
    ) -> Dict[str, any]:
        """
        Save a website as static PHP files following the split-template pattern:

            <website_folder>/
                template/
                    main.php       <- HTML shell (includes header/body/footer via PHP view())
                    header.php     <- shared <header> partial (from first page)
                    footer.php     <- shared <footer> + JS partial (from first page)
                home.php           <- body sections for home page
                about.php          <- body sections for about page
                ...
                assets/
                    css/
                        style.css  <- merged CSS for all pages
                metadata.json

        Args:
            pages: Dict mapping page_name -> {header_html, body_html, footer_html, css}
            plan: Website plan dictionary
            description: Business/website description
            website_name: Optional custom name
            image_urls: Image URLs used in the website
            css_theme: Optional pre-generated global CSS theme (overrides extracted CSS)

        Returns:
            Dict with folder_path, saved_files, metadata_path, pages
        """
        # ── 1. Folder naming ──────────────────────────────────────────────
        # Content folder :  webtemplates/<name>/
        # Theme folder   :  webtemplates/<name>theme/
        content_folder = self.create_website_folder(website_name)
        theme_folder   = content_folder + "theme"
        os.makedirs(theme_folder, exist_ok=True)
        logger.info(f"Content folder : {content_folder}")
        logger.info(f"Theme folder   : {theme_folder}")

        # Sub-directories
        template_dir  = os.path.join(content_folder, "template")
        theme_css_dir = os.path.join(theme_folder, "css")
        theme_img_dir = os.path.join(theme_folder, "images")
        os.makedirs(template_dir,  exist_ok=True)
        os.makedirs(theme_css_dir, exist_ok=True)
        os.makedirs(theme_img_dir, exist_ok=True)

        page_names  = list(pages.keys())
        saved_files = {}

        # ── 2. Site title ─────────────────────────────────────────────────
        site_title = "Website"
        if plan and "name" in plan:
            site_title = plan["name"]
        elif description:
            site_title = " ".join(description.split()[:4])

        # ── 3. CSS → <name>theme/css/style.css ───────────────────────────
        if css_theme:
            global_css = css_theme
        else:
            css_parts = []
            for pg_name, pg_content in pages.items():
                pg_css = pg_content.get("css", "")
                if pg_css:
                    css_parts.append(f"/* === {pg_name} === */\n{pg_css}")
            global_css = "\n\n".join(css_parts)

        if global_css:
            css_path = os.path.join(theme_css_dir, "style.css")
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(global_css)
            logger.info(f"Saved CSS: {css_path} ({len(global_css)} chars)")

        # ── 4. Images → <name>theme/images/ ──────────────────────────────
        # Priority 1: Copy DALL-E generated images from uploads/ (passed via image_urls dict)
        # Priority 2: Fall back to copying from IMAGES_PATH folder
        import shutil
        copied_images = []

        # Try to copy from DALL-E generated local paths (passed as image_local_paths in kwargs)
        generated_paths = image_urls or {}   # image_urls maps section → http URL
        # Derive local file paths from URLs (e.g. http://localhost/uploads/hero_123.png → uploads/hero_123.png)
        uploads_base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
        )
        for section, url in generated_paths.items():
            if "/uploads/" in url:
                filename = url.split("/uploads/")[-1].split("?")[0]
                src = os.path.join(uploads_base, filename)
                if os.path.isfile(src):
                    dst = os.path.join(theme_img_dir, filename)
                    shutil.copy2(src, dst)
                    copied_images.append(filename)
                    logger.info(f"Copied DALL-E image '{filename}' → theme/images/")

        # Fall back to IMAGES_PATH if no DALL-E images were copied
        if not copied_images:
            images_src = os.getenv("IMAGES_PATH", "")
            if images_src and os.path.isdir(images_src):
                image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
                for fname in sorted(os.listdir(images_src)):
                    if os.path.splitext(fname)[1].lower() in image_exts:
                        src = os.path.join(images_src, fname)
                        dst = os.path.join(theme_img_dir, fname)
                        shutil.copy2(src, dst)
                        copied_images.append(fname)
                        logger.info(f"Copied fallback image '{fname}' → theme/images/")
            else:
                logger.warning("No DALL-E images and IMAGES_PATH not set — theme/images/ will be empty")

        logger.info(f"Total images in theme/images/: {len(copied_images)}")


        # ── 5. template/header.php & footer.php ───────────────────────────
        first_page = pages[page_names[0]] if page_names else {}
        header_html = first_page.get("header_html", "")
        footer_html = first_page.get("footer_html", "")

        for fname, content in [("header.php", header_html), ("footer.php", footer_html)]:
            fpath = os.path.join(template_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Saved: {fpath}")

        # ── 6. template/main.php ──────────────────────────────────────────
        # $themefolder and $main_content set by the framework controller at runtime.
        # CSS path: ASSETSURL/<themefolder>/css/style.css
        main_php = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{site_title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="robots" content="index,follow">
    <meta name="generator" content="GrapesJS Studio">
    <link rel="stylesheet" href="<?=ASSETSURL. '/' . $themefolder;?>/css/style.css">
  </head>
  <body>

<?php echo view('fshop/'.$themefolder.'/template/header'); ?>

<?php echo view($main_content); ?>

<?php echo view('fshop/'.$themefolder.'/template/footer'); ?>

</body>
</html>
"""
        main_path = os.path.join(template_dir, "main.php")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_php)
        logger.info(f"Saved: {main_path}")

        # ── 7. Per-page body .php files → <name>/<page>.php ───────────────
        for pg_name, pg_content in pages.items():
            body_html    = pg_content.get("body_html", "")
            php_filename = f"{pg_name}.php"
            php_path     = os.path.join(content_folder, php_filename)
            with open(php_path, "w", encoding="utf-8") as f:
                f.write(body_html)
            saved_files[pg_name] = php_path
            logger.info(f"Saved page body: {php_path} ({len(body_html)} chars)")

        # ── 8. Metadata in content folder ─────────────────────────────────
        metadata = {
            "created_at":           datetime.now().isoformat(),
            "description":          description,
            "plan":                 plan,
            "pages":                page_names,
            "image_urls":           image_urls or {},
            "copied_images":        copied_images,
            "output_format":        "php_static_split",
            "has_global_css_theme": bool(css_theme),
            "content_folder":       content_folder,
            "theme_folder":         theme_folder,
        }
        self.save_metadata(content_folder, metadata)

        logger.info(f"PHP website saved — content: {content_folder} | theme: {theme_folder}")
        return {
            "folder_path":   content_folder,   # primary content folder
            "theme_folder":  theme_folder,      # theme assets folder
            "saved_files":   saved_files,
            "metadata_path": os.path.join(content_folder, "metadata.json"),
            "pages":         page_names,
            "copied_images": copied_images,
        }


