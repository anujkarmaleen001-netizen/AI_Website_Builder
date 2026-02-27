import dspy  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# CI4 CATEGORY NAV TEMPLATE
# This is hardcoded (NOT LLM-generated) to guarantee correct CI4 variable usage.
# It is injected into the header_html description so the LLM copies it verbatim.
# ─────────────────────────────────────────────────────────────────────────────
CI4_CATEGORY_NAV_TEMPLATE = """
<!-- ===== CI4 DYNAMIC CATEGORY NAV — COPY THIS EXACTLY ===== -->
<nav class="category-nav-bar">
  <div class="container">
    <ul class="navbar-nav category-nav-list" id="categoryNavList">

      <?php if((empty($search)) && empty($filters)): ?>
      <li class="nav-item category-nav-item">
        <a class="nav-link cat-link <?= empty($selected_category_id) ? 'active' : '' ?>"
           href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>">All</a>
      </li>
      <?php endif; ?>

      <?php foreach ($categories as $category):
        $categoryname = $category['category_name'];
        $catid        = $category['category_id'];
        $isActive     = (!empty($selected_category_id) && $selected_category_id == $catid) ? 'active' : '';
        if($category['subcategory_count'] == 0):
          $catlink = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$catid);
      ?>
        <li class="nav-item category-nav-item">
          <a class="nav-link cat-link <?= $isActive ?>" href="<?= $catlink ?>"><?= $categoryname ?></a>
        </li>
      <?php else: $catlink = "#"; ?>
        <li class="nav-item dropdown category-nav-item">
          <a class="nav-link cat-link dropdown-toggle <?= $isActive ?>"
             href="#" data-bs-toggle="dropdown"><?= $categoryname ?></a>
          <ul class="dropdown-menu">
            <?php if(!empty($subcategorieslist[$catid])):
              foreach($subcategorieslist[$catid] as $subcategory):
                $subcatid   = $subcategory['sub_category_id'];
                $subcatlink = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$catid.'?sub='.$subcatid);
            ?>
            <li>
              <a class="dropdown-item" href="<?= $subcatlink ?>"><?= $subcategory['name'] ?></a>
            </li>
            <?php endforeach; endif; ?>
          </ul>
        </li>
      <?php endif; endforeach; ?>

    </ul>
  </div>
</nav>
<!-- ===== END CI4 CATEGORY NAV ===== -->
"""


class MultiPageSignature(dspy.Signature):
    """Generate CI4-compatible PHP page parts (header, body, footer) and CSS for a specific page of an e-commerce shop."""
    plan: str = dspy.InputField(
        desc="Complete website plan JSON. Always contains pages=[home, faq], design_system, and ci4_context with PHP variables and route patterns."
    )
    page_name: str = dspy.InputField(
        desc="Name of the page to generate. Either 'home' or 'faq'."
    )
    page_config: str = dspy.InputField(
        desc="Specific page configuration from the plan (name, purpose, sections)."
    )
    image_urls: str = dspy.InputField(
        desc="Available image URLs formatted as: section_name: url"
    )
    business_description: str = dspy.InputField(
        desc="Business/brand description including shop name, mid, hero text, colors, FAQ items."
    )
    header_html: str = dspy.OutputField(
        desc="""The <header> partial PHP/HTML for the page. CI4 compatible. No <!DOCTYPE>, no <html>, no <head>, no <body> tags.

OUTPUT STRUCTURE — Single-tier header (brand + main nav ONLY):

REQUIRED PHP/HTML:

<header class="site-header">

  <!-- Brand + Main Nav -->
  <div class="top-nav-bar">
    <div class="container top-nav-inner">
      <a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>" class="site-logo">
        [BRAND NAME FROM BUSINESS DESCRIPTION]
      </a>
      <button class="hamburger-btn" onclick="toggleMobileMenu()" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
      <nav class="main-nav">
        <ul class="main-nav-list" id="mainNavMenu">
          <li class="nav-item">
            <a class="nav-link <?= ($page_name ?? '') === 'home' ? 'active' : '' ?>"
               href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>">Home</a>
          </li>
          <li class="nav-item">
            <a class="nav-link <?= ($page_name ?? '') === 'faq' ? 'active' : '' ?>"
               href="<?= getDynamicBaseUrl('fshop/faq/'.$merchant_id) ?>">FAQ</a>
          </li>
        </ul>
      </nav>
    </div>
  </div>

</header>

RULES:
- Replace [BRAND NAME FROM BUSINESS DESCRIPTION] with the actual shop name
- ONLY Home and FAQ in the main nav — NO other links, NO category nav here
- NO <!DOCTYPE>, NO <html>, NO <head>, NO <style>, NO <body> tags
- Apply design_system colors via inline CSS custom properties on <header>: style="--primary: #hex; --secondary: #hex;"
- The category nav is NOT part of the header — it lives in the home page body only
        """
    )
    body_html: str = dspy.OutputField(
        desc="""The page body content — all section blocks for this specific page.
No <!DOCTYPE>, no <html>, no <head>, no <body>, no <header>, no <footer> tags.
CI4 compatible PHP/HTML. Output ONLY the sections between header and footer.

TOKEN LIMIT: Keep under 5000 tokens.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF page_name == "home":
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED SECTIONS (in order):

0. CI4 DYNAMIC CATEGORY NAV (home page only — COPY THIS EXACTLY VERBATIM):
[INSERT CI4_CATEGORY_NAV_TEMPLATE HERE — placed BEFORE the hero banner]

1. HERO BANNER (static, branded):
<section id="hero-banner" class="hero-section">
  <div class="container hero-inner">
    <div class="hero-content">
      <h1 class="hero-headline">[HERO HEADLINE FROM BUSINESS DESCRIPTION]</h1>
      <p class="hero-subheadline">[HERO SUBHEADLINE FROM BUSINESS DESCRIPTION]</p>
      <a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>" class="btn btn-primary hero-cta">
        [CTA TEXT e.g. Shop Now]
      </a>
    </div>
    <div class="hero-image">
      <img src="[USE IMAGE URL FROM image_urls IF AVAILABLE]" alt="Shop Banner" loading="lazy">
    </div>
  </div>
</section>

2. FEATURED PRODUCTS (dynamic CI4 PHP loop):
<section id="featured-products" class="section-padding products-section">
  <div class="container">
    <h2 class="section-title">Featured Products</h2>
    <div class="product-grid">
      <?php if(!empty($products)): ?>
        <?php foreach($products as $product): ?>
        <div class="product-card">
          <div class="product-card-img-wrap">
            <img src="<?= !empty($product['image']) ? $product['image'] : '' ?>"
                 alt="<?= htmlspecialchars($product['product_name']) ?>" loading="lazy"
                 onerror="this.style.display='none'">
          </div>
          <div class="product-card-body">
            <h3 class="product-name"><?= htmlspecialchars($product['product_name']) ?></h3>
            <?php if(!empty($product['price'])): ?>
            <p class="product-price">&#8377;<?= number_format((float)$product['price'], 2) ?></p>
            <?php endif; ?>
            <a href="<?= getDynamicBaseUrl('fshop/product/'.$merchant_id.'/'.$product['product_id']) ?>"
               class="btn btn-primary btn-sm product-cta">View Details</a>
          </div>
        </div>
        <?php endforeach; ?>
      <?php else: ?>
        <p class="no-products-msg">No products available at the moment.</p>
      <?php endif; ?>
    </div>
  </div>
</section>

3. CTA BANNER (static, branded):
<section id="cta-banner" class="cta-section section-padding">
  <div class="container cta-inner">
    <h2>[Short compelling call-to-action headline]</h2>
    <p>[One-line supporting text]</p>
    <a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>" class="btn btn-primary">Browse All Products</a>
  </div>
</section>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF page_name == "faq":
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED SECTIONS (in order):

1. FAQ HERO (static):
<section id="faq-hero" class="faq-hero-section section-padding">
  <div class="container">
    <h1 class="section-title">Frequently Asked Questions</h1>
    <p class="faq-subtitle">Everything you need to know about shopping with us.</p>
  </div>
</section>

2. FAQ LIST (use faq_items from business_description — generate 4-6 Q&A if not specified):
<section id="faq-list" class="section-padding">
  <div class="container">
    <div class="faq-accordion">
      <div class="faq-item">
        <button class="faq-question" onclick="toggleFaq(this)">
          [Question text]
          <span class="faq-icon">+</span>
        </button>
        <div class="faq-answer">
          <p>[Answer text]</p>
        </div>
      </div>
      [Repeat for each FAQ item — minimum 4 items]
    </div>
  </div>
</section>

3. CONTACT CTA (static):
<section id="contact-cta" class="contact-cta-section section-padding">
  <div class="container contact-cta-inner">
    <h2>Still have questions?</h2>
    <p>[Contact email/phone from business description]</p>
    <a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>" class="btn btn-primary">Back to Shop</a>
  </div>
</section>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOBAL RULES:
- Use getDynamicBaseUrl() for all CI4 links
- Use htmlspecialchars() for dynamic string output
- Use number_format() for prices
- Use $merchant_id in all route URLs
- NO hardcoded product data — always use $products PHP loop for product sections
- CSS classes to use: .container, .section-padding, .section-title, .btn, .btn-primary, .btn-sm, .product-grid, .product-card
        """
    )
    footer_html: str = dspy.OutputField(
        desc="""The <footer> partial PHP/HTML + JavaScript. No <!DOCTYPE>, no <html>, no <head>, no <body> tags.
CI4 compatible. Output the <footer>...</footer> element AND inline <script> blocks.

TOKEN LIMIT: Keep under 1500 tokens.

REQUIRED STRUCTURE:
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">

      <div class="footer-col footer-brand">
        <h4 class="footer-logo">[BRAND NAME]</h4>
        <p class="footer-tagline">[FOOTER TAGLINE FROM BUSINESS DESCRIPTION]</p>
      </div>

      <div class="footer-col footer-links">
        <h4>Quick Links</h4>
        <ul>
          <li><a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>">Home</a></li>
          <li><a href="<?= getDynamicBaseUrl('fshop/faq/'.$merchant_id) ?>">FAQ</a></li>
        </ul>
      </div>

      <div class="footer-col footer-contact">
        <h4>Contact Us</h4>
        <p>[Email from business description]</p>
        <p>[Phone from business description if available]</p>
      </div>

    </div>
    <div class="footer-bottom">
      <p>&copy; <?= date('Y') ?> [BRAND NAME]. All rights reserved.</p>
    </div>
  </div>
</footer>

<script>
/* Mobile menu toggle */
function toggleMobileMenu() {
  var menu = document.getElementById('mainNavMenu');
  if (menu) { menu.classList.toggle('open'); }
}
/* Close mobile menu on link click */
document.querySelectorAll('.main-nav-list .nav-link').forEach(function(link) {
  link.addEventListener('click', function() {
    var menu = document.getElementById('mainNavMenu');
    if (menu) { menu.classList.remove('open'); }
  });
});
/* FAQ accordion toggle */
function toggleFaq(btn) {
  var answer = btn.nextElementSibling;
  var icon   = btn.querySelector('.faq-icon');
  var isOpen = answer.style.maxHeight && answer.style.maxHeight !== '0px';
  document.querySelectorAll('.faq-answer').forEach(function(a) { a.style.maxHeight = '0px'; });
  document.querySelectorAll('.faq-icon').forEach(function(i) { i.textContent = '+'; });
  if (!isOpen) {
    answer.style.maxHeight = answer.scrollHeight + 'px';
    if (icon) { icon.textContent = '−'; }
  }
}
</script>

RULES:
- Quick Links: Home and FAQ ONLY — no other pages
- All links use getDynamicBaseUrl()
- Use <?= date('Y') ?> for copyright year
- NO <html>, <head>, <body>, <header>, <style> tags
        """
    )
    css: str = dspy.OutputField(
        desc="""All CSS for this e-commerce website as plain CSS text (no style tags, no markdown fences).
Saved as assets/css/style.css and linked from the CI4 main template.

TOKEN LIMIT: Keep under 3500 tokens.

MUST INCLUDE THESE SECTIONS IN ORDER:

1. CSS Custom Properties (design tokens from design_system):
:root {
  --primary: [primary hex from design_system];
  --primary-dark: [primary_dark hex];
  --primary-light: [primary_light hex];
  --secondary: [secondary hex];
  --background: [background hex];
  --surface: [surface hex];
  --text-primary: [text_primary hex];
  --text-secondary: [text_secondary hex];
  --border: [border hex];
  --border-radius: 8px;
  --transition: 0.25s ease;
}

2. Google Fonts import (use fonts from design_system.typography)

3. Base reset + body styles

4. Layout utilities:
   .container (max-width from design_system.spacing.container_max_width, centered, padded)
   .section-padding (padding-y from design_system.spacing.section_padding_y)
   .section-title (styled heading)

5. TIER 1 Top nav (.top-nav-bar, .top-nav-inner, .site-logo, .main-nav, .main-nav-list, .nav-link)
   - Fixed or sticky position
   - Logo left, nav right
   - .nav-link.active uses var(--primary)

6. TIER 2 Category nav (.category-nav-bar, .category-nav-list, .cat-link)
   - Horizontal scrollable on mobile
   - .cat-link.active uses var(--primary) with underline/border-bottom
   - .dropdown-menu styles (Bootstrap-compatible)

7. Hamburger button (.hamburger-btn — hidden desktop, visible mobile)
   Mobile menu: #mainNavMenu.open shows as column

8. Hero section (.hero-section, .hero-inner, .hero-content, .hero-headline, .hero-subheadline, .hero-cta, .hero-image)
   - Flexbox two-column layout (text left, image right)
   - Stacks on mobile

9. Products section (.products-section, .product-grid, .product-card, .product-card-img-wrap, .product-card-body, .product-name, .product-price, .product-cta, .no-products-msg)
   - CSS Grid: repeat(auto-fill, minmax(220px, 1fr))
   - Card hover: translateY(-4px) + box-shadow
   - .product-card-img-wrap: fixed aspect-ratio (4/3), overflow hidden

10. CTA section (.cta-section, .cta-inner — centered, background var(--primary-light))

11. FAQ styles (.faq-accordion, .faq-item, .faq-question, .faq-answer, .faq-icon)
    - .faq-answer: max-height: 0; overflow: hidden; transition for accordion

12. Contact CTA section (.contact-cta-section, .contact-cta-inner — centered)

13. Footer (.site-footer, .footer-grid, .footer-col, .footer-brand, .footer-links, .footer-contact, .footer-bottom)
    - .footer-grid: 3-column grid, collapses to 1 on mobile

14. Buttons (.btn, .btn-primary, .btn-sm)
    - .btn-primary uses var(--primary), hover uses var(--primary-dark)

15. Media queries (max-width: 768px):
    - Category nav: horizontal scroll
    - Product grid: 2 columns → 1 column at 480px
    - Hero: stack vertically
    - Footer: 1 column

OUTPUT: Plain CSS only. No style tags. No markdown fences. No comments that add significant length.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# These signatures are used for the GrapesJS editor update flow (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

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
            "target_pages": ["home", "faq"] or [],
            "requires_css_update": true/false,
            "interpretation": "Brief explanation of what will be changed"
        }
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