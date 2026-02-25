import dspy  # type: ignore


class MultiPageSignature(dspy.Signature):
    """Generate static PHP page parts (header, body, footer) and CSS for a specific page."""
    plan: str = dspy.InputField(
        desc="Complete website plan JSON containing all pages and navigation structure"
    )
    page_name: str = dspy.InputField(
        desc="Name of the page to generate"
    )
    page_config: str = dspy.InputField(
        desc="Specific page configuration from plan"
    )
    image_urls: str = dspy.InputField(
        desc="Available image URLs formatted as: section_name: url"
    )
    business_description: str = dspy.InputField(
        desc="Original business description for content generation"
    )
    header_html: str = dspy.OutputField(
        desc="""The <header> partial HTML only. No <!DOCTYPE>, no <html>, no <head>, no <body> tags.
        Output ONLY the <header>...</header> element containing the navbar/logo/navigation.

        TOKEN LIMIT: Keep this under 1000 tokens.

        REQUIRED STRUCTURE:
        <header>
            <div class="navbar container">
                <a href="home.php" class="logo">Brand Name</a>
                <button class="hamburger-menu" onclick="toggleMenu()" aria-label="Toggle menu">
                    <span></span><span></span><span></span>
                </button>
                <nav>
                    <ul class="nav-menu">
                        <li><a href="home.php" class="nav-link active">Home</a></li>
                        <li><a href="about.php" class="nav-link">About</a></li>
                    </ul>
                </nav>
            </div>
        </header>

        RULES:
        - Use href="[page_name].php" for ALL navigation links (NOT .html)
        - Logo on the left, nav on the right
        - Include hamburger button with 3 spans for mobile
        - Mark current page link with class="nav-link active"
        - NO <!DOCTYPE>, NO <html>, NO <head>, NO <style>, NO <body> tags
        """
    )
    body_html: str = dspy.OutputField(
        desc="""The page body content ONLY -- all section blocks for this page.
        No <!DOCTYPE>, no <html>, no <head>, no <body>, no <header>, no <footer> tags.
        Output ONLY the inner content sections that go between header and footer.

        TOKEN LIMIT: Keep total output under 6000 tokens.

        CONTENT LENGTH LIMITS (STRICT):
        - Hero section: 1 heading (6-10 words) + 1 description (15-25 words) + 1 CTA button
        - Features: Max 3 features, each with title (3-5 words) + text (15-20 words max)
        - Testimonials: Max 2-3 items, each quote under 20 words
        - About/Other sections: 2-3 sentences maximum (30-50 words total)

        REQUIRED STRUCTURE for every section:
        <section id="section_name" class="section-padding">
            <div class="container">
                <h2 class="section-title">Title</h2>
                <div class="grid grid-cols-1 grid-cols-md-3 gap-lg">
                    <div class="card">Content</div>
                </div>
            </div>
        </section>

        RULES:
        - Use provided image URLs in img tags with alt text
        - Use realistic, professional content aligned with business description
        - All internal links use href="[page_name].php" format
        - Use CSS classes: .container, .grid, .grid-cols-1, .grid-cols-md-3, .card, .btn, .btn-primary, .section-padding
        - DO NOT create custom classes
        - NO <html>, <head>, <body>, <header>, <footer>, <style> tags
        """
    )
    footer_html: str = dspy.OutputField(
        desc="""The <footer> partial HTML + JavaScript. No <!DOCTYPE>, no <html>, no <head>, no <body> tags.
        Output the <footer>...</footer> element AND the <script>...</script> for mobile menu toggle.

        TOKEN LIMIT: Keep this under 1500 tokens.

        REQUIRED STRUCTURE:
        <footer id="footer">
            <div class="container">
                <div class="footer-grid">
                    <div class="footer-col">
                        <h4>Brand Name</h4>
                        <p>Short tagline.</p>
                    </div>
                    <div class="footer-col">
                        <h4>Quick Links</h4>
                        <a href="home.php">Home</a>
                        <a href="about.php">About</a>
                    </div>
                    <div class="footer-col">
                        <h4>Contact</h4>
                        <p>email@example.com</p>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>2024 Brand. All rights reserved.</p>
                </div>
            </div>
        </footer>
        <script>
        function toggleMenu() {
            var navMenu = document.querySelector('.nav-menu');
            if (navMenu) { navMenu.classList.toggle('active'); }
        }
        document.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                var navMenu = document.querySelector('.nav-menu');
                if (navMenu) { navMenu.classList.remove('active'); }
            });
        });
        </script>

        RULES:
        - All links use href="[page_name].php" format
        - Include the JavaScript toggleMenu function
        - Minimal footer content, max 3 columns
        - NO <html>, <head>, <body>, <header>, <style> tags
        """
    )
    css: str = dspy.OutputField(
        desc="""All CSS styles for this website as plain CSS text (no style tags, no markdown).
        This will be saved as assets/css/style.css and linked from the main template.

        TOKEN LIMIT: Keep under 3000 tokens. Only essential styles.

        MUST INCLUDE:
        - CSS reset/base styles
        - .container, .grid, .grid-cols-1, .grid-cols-md-3, .gap-lg layout classes
        - header, .navbar, .logo, .nav-menu, .nav-link styles
        - .hamburger-menu styles (hidden by default on desktop)
        - Hero section styles
        - .card, .btn, .btn-primary component styles
        - .section-padding, .section-title styles
        - footer, .footer-grid, .footer-col, .footer-bottom styles
        - Media query (max-width: 768px) responsive rules including:
            .hamburger-menu display flex
            .nav-menu slide-in behavior

        OUTPUT: Plain CSS text only. No style tags. No markdown code fences.
        """
    )


class WebsiteUpdateAnalyzerSignature(dspy.Signature):
    """Analyze edit request and determine what needs to be updated."""
    edit_request: str = dspy.InputField(
        desc="User's natural language edit request (e.g., 'change colors to blue', 'update hero text on home page')"
    )
    available_pages: str = dspy.InputField(
        desc="List of available page names in the website"
    )
    current_global_css: str = dspy.InputField(
        desc="Current global CSS content (optional, can be empty)"
    )
    analysis: str = dspy.OutputField(
        desc="""JSON-formatted analysis of what needs to be updated:
        {
            "update_type": "global_css" | "specific_pages" | "both",
            "target_pages": ["home", "about"] or [],
            "requires_css_update": true/false,
            "interpretation": "Brief explanation of what will be changed"
        }

        Examples:
        - "Change all colors to blue" -> {"update_type": "global_css", "target_pages": [], "requires_css_update": true}
        - "Update hero text on home page" -> {"update_type": "specific_pages", "target_pages": ["home"], "requires_css_update": false}
        - "Make buttons larger and update about page content" -> {"update_type": "both", "target_pages": ["about"], "requires_css_update": true}
        """
    )

class HTMLEditSignature(dspy.Signature):
    """Edit an existing HTML page based on a natural language edit request."""
    html_input: str = dspy.InputField(
        desc="Current HTML content of the page to be edited"
    )
    css_input: str = dspy.InputField(
        desc="Current CSS content associated with the page (can be empty)"
    )
    edit_request: str = dspy.InputField(
        desc="Natural language description of the changes to make to the HTML/CSS"
    )
    html_output: str = dspy.OutputField(
        desc="""Complete, updated HTML document after applying the requested changes.

        REQUIREMENTS:
        - Return the full HTML document (not just the changed parts)
        - Maintain the original structure and all existing content not affected by the edit
        - Apply ONLY the changes described in edit_request
        - Preserve all navigation links, classes, and IDs
        - Keep all responsive design and CSS intact
        - Return valid HTML5 with proper DOCTYPE
        - Include any updated or new CSS inside style tags in head
        """
    )