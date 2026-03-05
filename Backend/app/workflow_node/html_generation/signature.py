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
    <div class="category-nav-shell">
      <button type="button" class="category-nav-arrow category-nav-arrow-prev" id="categoryNavPrev" aria-label="Scroll categories left">‹</button>
      <div class="category-nav-scroll" id="categoryNavScroll">
        <ul class="navbar-nav category-nav-list" id="categoryNavList">

      <?php
        $selectedCategoryId = !empty($selected_category_id) ? (int)$selected_category_id : 0;
        $selectedSubcategoryId = !empty($selected_subcategory_id)
          ? (int)$selected_subcategory_id
          : (isset($_GET['sub']) ? (int)$_GET['sub'] : 0);
        $isAllActive = ($selectedCategoryId <= 0 && $selectedSubcategoryId <= 0) ? 'active' : '';
      ?>

      <?php if((empty($search)) && empty($filters)): ?>
      <li class="nav-item category-nav-item">
        <a class="nav-link cat-link <?= $isAllActive ?>"
           href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>">All</a>
      </li>
      <?php endif; ?>

      <?php foreach ($categories as $category):
        $categoryname = $category['category_name'];
        $catid        = $category['category_id'];
        $subcategories = !empty($subcategorieslist[$catid]) ? $subcategorieslist[$catid] : [];
        $hasSubcategories = !empty($category['subcategory_count']) && !empty($subcategories);
        $isCategorySelected = ($selectedCategoryId > 0 && $selectedCategoryId === (int)$catid);

        $selectedSubBelongsToCategory = false;
        if($hasSubcategories && $selectedSubcategoryId > 0):
          foreach($subcategories as $subcategoryRef):
            if((int)$subcategoryRef['sub_category_id'] === $selectedSubcategoryId):
              $selectedSubBelongsToCategory = true;
              break;
            endif;
          endforeach;
        endif;

        if($isCategorySelected && $selectedSubcategoryId > 0 && !$selectedSubBelongsToCategory):
          $redirectUrl = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$catid);
          echo '<script>window.location.href='.json_encode($redirectUrl).';</script>';
          $selectedSubcategoryId = 0;
        endif;

        $isActive = $isCategorySelected ? 'active' : '';

        if(!$hasSubcategories):
          $catlink = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$catid);
      ?>
        <li class="nav-item category-nav-item">
          <a class="nav-link cat-link <?= $isActive ?>" href="<?= $catlink ?>"><?= $categoryname ?></a>
        </li>
      <?php else: $catlink = "#"; ?>
        <li class="nav-item dropdown category-nav-item">
          <a class="nav-link cat-link dropdown-toggle <?= $isActive ?>"
             href="#"
             data-subcategory-toggle="true"
             aria-expanded="false"><?= $categoryname ?></a>
          <ul class="dropdown-menu category-submenu" style="max-height:none; overflow:visible;">
            <?php foreach($subcategories as $subcategory):
                $subcatid   = $subcategory['sub_category_id'];
                $subcatlink = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$catid.'?sub='.$subcatid);
                $subIsActive = ($isCategorySelected && (int)$subcatid === $selectedSubcategoryId) ? 'active' : '';
            ?>
            <li>
              <a class="dropdown-item <?= $subIsActive ?>" href="<?= $subcatlink ?>"><?= $subcategory['name'] ?></a>
            </li>
            <?php endforeach; ?>
          </ul>
        </li>
      <?php endif; endforeach; ?>
        </ul>
      </div>
      <button type="button" class="category-nav-arrow category-nav-arrow-next" id="categoryNavNext" aria-label="Scroll categories right">›</button>
    </div>
  </div>
</nav>
<script>
/* Hover + click behavior for category submenus */
(function() {
  function isDesktop() {
    return window.matchMedia('(min-width: 992px)').matches;
  }

  function closeAllCategoryDropdowns(exceptItem) {
    document.querySelectorAll('#categoryNavList .category-nav-item.dropdown').forEach(function(item) {
      if (exceptItem && item === exceptItem) { return; }
      item.classList.remove('open');
      var toggle = item.querySelector('[data-subcategory-toggle="true"]');
      if (toggle) { toggle.setAttribute('aria-expanded', 'false'); }
    });
  }

  var navScroll = document.getElementById('categoryNavScroll');
  var prevBtn = document.getElementById('categoryNavPrev');
  var nextBtn = document.getElementById('categoryNavNext');

  function updateArrowState() {
    if (!navScroll || !prevBtn || !nextBtn) { return; }
    var maxScroll = Math.max(0, navScroll.scrollWidth - navScroll.clientWidth);
    var left = Math.max(0, navScroll.scrollLeft);
    prevBtn.disabled = left <= 2;
    nextBtn.disabled = left >= (maxScroll - 2);
  }

  function scrollCategories(direction) {
    if (!navScroll) { return; }
    var distance = Math.max(220, Math.floor(navScroll.clientWidth * 0.45));
    navScroll.scrollBy({
      left: direction * distance,
      behavior: 'smooth'
    });
    window.setTimeout(updateArrowState, 220);
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', function() { scrollCategories(-1); });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function() { scrollCategories(1); });
  }
  if (navScroll) {
    navScroll.addEventListener('scroll', updateArrowState, { passive: true });
    window.addEventListener('resize', updateArrowState);
    window.setTimeout(updateArrowState, 0);
  }

  function bindHoverBehavior() {
    document.querySelectorAll('#categoryNavList .category-nav-item.dropdown').forEach(function(item) {
      item.addEventListener('mouseenter', function() {
        if (!isDesktop()) { return; }
        closeAllCategoryDropdowns(item);
        item.classList.add('open');
        var toggle = item.querySelector('[data-subcategory-toggle="true"]');
        if (toggle) { toggle.setAttribute('aria-expanded', 'true'); }
      });

      item.addEventListener('mouseleave', function() {
        if (!isDesktop()) { return; }
        item.classList.remove('open');
        var toggle = item.querySelector('[data-subcategory-toggle="true"]');
        if (toggle) { toggle.setAttribute('aria-expanded', 'false'); }
      });
    });
  }

  bindHoverBehavior();

  document.addEventListener('click', function(event) {
    var toggle = event.target.closest('#categoryNavList [data-subcategory-toggle="true"]');
    if (toggle) {
      event.preventDefault();
      var parentItem = toggle.closest('.category-nav-item.dropdown');
      if (!parentItem) { return; }

      if (isDesktop()) {
        return;
      }

      var shouldOpen = !parentItem.classList.contains('open');
      closeAllCategoryDropdowns(parentItem);
      if (shouldOpen) {
        parentItem.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
      } else {
        toggle.setAttribute('aria-expanded', 'false');
      }
      return;
    }

    if (!event.target.closest('#categoryNavList .category-nav-item.dropdown')) {
      closeAllCategoryDropdowns();
    }
  });
})();
</script>
<!-- ===== END CI4 CATEGORY NAV ===== -->
"""


class MultiPageSignature(dspy.Signature):
    """Generate CI4-compatible PHP page parts (header, body, footer) and CSS for a specific page of an e-commerce shop."""
    plan: str = dspy.InputField(
        desc="Complete website plan JSON. Always contains pages=[home, product_detail, faq], design_system, and ci4_context with PHP variables and route patterns."
    )
    page_name: str = dspy.InputField(
        desc="Name of the page to generate. One of: 'home', 'product_detail', or 'faq'."
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

2. FEATURED PRODUCTS (dynamic CI4 inventory loop — use this exact field logic):
<section id="featured-products" class="section-padding products-section">
  <div class="container">
    <h2 class="section-title">Featured Products</h2>
    <?php $productCount = (!empty($results) && is_array($results)) ? count($results) : 0; ?>
    <div class="products-row <?= ($productCount === 1) ? 'single-product' : '' ?>">
      <?php if(!empty($results)){ ?>
        <?php foreach($results as $inventory){
          $pdetailurl = $inventory["merchant_id"].'/'.$inventory["inventory_id"];
          if($inventory['file_type'] == 2){
            $object_key = str_replace(' ', '', $inventory["object_key"]);
            $imageURL = !empty($inventory['object_key']) ? BUCKET360.$object_key : base_url('assets/img/Default-Image.jpg');
          }else{
            $imageURL = base_url('assets/img/Default-Image.jpg');
          }
          $pid = $inventory["inventory_id"];
          $ptype = $inventory["price_type"];
        ?>
        <input type="hidden" value="<?php echo $inventory['stock_qty'] ?>" id="<?php echo 'stock_'.$inventory['inventory_id'] ?>" >
        <input type="hidden" value="1" id="<?php echo 'invqty_'.$pid; ?>" min="1">
        <div class="product-col">
          <div class="product-item">
            <div class="product-img">
              <a href="<?php echo getDynamicBaseUrl('fshopdetail/index/'.$pdetailurl); ?>">
                <img src="<?php echo $imageURL; ?>" class="img-fluid" alt="product" />
              </a>
            </div>
            <div class="product-detail">
              <h4 class="product-title"><?php echo $inventory['name']; ?></h4>
              <p class="price">$<?php
                $special_price = $inventory['special_price'];
                if($special_price != '' && $special_price != null){
                  echo $special_price.'&nbsp; <s> '.$inventory['price']."</s>";
                }else{
                  echo $inventory['price'];
                }
              ?></p>
              <div class="addCart-area">
                <a href="javascript:void(0);" id="cart_<?php echo $pid; ?>" data-id=""
                   data-has-required-modifiers="<?php echo isset($inventory['has_required_modifiers']) && $inventory['has_required_modifiers'] ? '1' : '0'; ?>"
                   onclick="addToCart('<?php echo $pid; ?>','<?php echo $ptype; ?>','list','')">
                  Add to Cart
                </a>
              </div>
            </div>
          </div>
        </div>
        <?php } ?>
      <?php } else { ?>
        <p class="no-products-msg">Product(s) not found...</p>
      <?php } ?>
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
IF page_name == "product_detail":
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED SECTIONS (in order):

1. PRODUCT BREADCRUMB + MAIN AREA (dynamic):
<section id="product-detail-main" class="section-padding product-detail-section">
  <div class="container">
    <?php
      $productName = !empty($product['name']) ? $product['name'] : 'Product';
      $productPrice = isset($product['price']) ? (float)$product['price'] : 0;
      $productSpecialPrice = (isset($product['special_price']) && $product['special_price'] !== '' && $product['special_price'] !== null) ? (float)$product['special_price'] : null;
      $productStock = isset($product['stock_qty']) ? (int)$product['stock_qty'] : 0;
      $productCurrency = !empty($product['currency_symbol']) ? $product['currency_symbol'] : '$';
      $productShortDescription = !empty($product['short_description']) ? $product['short_description'] : '';
      $productDescription = !empty($product['description']) ? $product['description'] : 'No description available.';
      $productCategory = !empty($product['category_name']) ? $product['category_name'] : 'Category';
      $productSubcategory = !empty($product['subcategory_name']) ? $product['subcategory_name'] : '';
      $pid = !empty($product['inventory_id']) ? $product['inventory_id'] : '';
      $ptype = !empty($product['price_type']) ? $product['price_type'] : 'fixed';
      $hasRequiredModifiers = !empty($product['has_required_modifiers']) ? '1' : '0';
      $backToListUrl = getDynamicBaseUrl('fshop/index/'.$merchant_id);
      if(!empty($selected_category_id)) {
        $backToListUrl = getDynamicBaseUrl('fshop/index/'.$merchant_id.'/'.$selected_category_id);
        if(!empty($selected_subcategory_id)) {
          $backToListUrl .= '?sub='.(int)$selected_subcategory_id;
        }
      }
    ?>
    <div class="product-detail-layout">
      <div class="product-gallery-col">
        <?php $invimgCount = (isset($invimgs) && is_array($invimgs)) ? count($invimgs) : 0; ?>
        <div class="product-slider <?= ($invimgCount <= 1) ? 'single-image' : '' ?>">
          <div class="thumbnail-slider">
            <div class="l-thumbnail">
              <?php if(count($invimgs) > 0) {
                foreach ($invimgs as $idx => $invimg) {
                  $object_key = str_replace(' ', '', $invimg["object_key"]);
                  $invimgurl = BUCKETBASEURL.$object_key;
              ?>
                <button type="button" class="thumb-item <?= $idx === 0 ? 'active' : '' ?>" data-slide-index="<?= $idx ?>">
                  <img src="<?php echo $invimgurl; ?>" alt="Thumbnail">
                </button>
              <?php } ?>
              <?php } else { ?>
                <button type="button" class="thumb-item active" data-slide-index="0">
                  <img src="<?php echo ASSETSURL.'img/Default-Image.jpg' ?>" alt="Thumbnail">
                </button>
              <?php } ?>
            </div>
          </div>

          <div class="big-image-slider swiper-container swiper">
            <div class="swiper-wrapper l-big-img">
              <?php if(count($invimgs) > 0) {
                foreach ($invimgs as $invimg) {
                  $object_key = str_replace(' ', '', $invimg["object_key"]);
                  $invimgurl = BUCKETBASEURL.$object_key;
              ?>
                <div class="swiper-slide"><img src="<?php echo $invimgurl; ?>" alt="Thumbnail"></div>
              <?php } ?>
              <?php } else { ?>
                <div class="swiper-slide"><img src="<?php echo ASSETSURL.'img/Default-Image.jpg' ?>" alt="Thumbnail"></div>
              <?php } ?>
            </div>
            <?php if($invimgCount > 1): ?>
            <div class="swiper-button-next"></div>
            <div class="swiper-button-prev"></div>
            <?php endif; ?>
          </div>
        </div>
      </div>

      <div class="product-info-col">
        <a class="product-back-link" href="<?= $backToListUrl ?>">Back to Products</a>
        <nav class="product-breadcrumb-right" aria-label="breadcrumb">
          <a href="<?= getDynamicBaseUrl('fshop/index/'.$merchant_id) ?>">Home</a>
          <span>/</span>
          <span><?= htmlspecialchars($productCategory) ?></span>
          <?php if(!empty($productSubcategory)): ?>
          <span>/</span>
          <span><?= htmlspecialchars($productSubcategory) ?></span>
          <?php endif; ?>
          <span>/</span>
          <span><?= htmlspecialchars($productName) ?></span>
        </nav>
        <h1 class="product-detail-title"><?= htmlspecialchars($productName) ?></h1>
        <?php if(!empty($productShortDescription)): ?>
        <p class="product-detail-subtitle"><?= htmlspecialchars($productShortDescription) ?></p>
        <?php endif; ?>

        <div class="product-detail-price">
          <?php if($productSpecialPrice !== null): ?>
            <span class="price-current"><?= $productCurrency ?><?= number_format($productSpecialPrice, 2) ?></span>
            <span class="price-old"><?= $productCurrency ?><?= number_format($productPrice, 2) ?></span>
          <?php else: ?>
            <span class="price-current"><?= $productCurrency ?><?= number_format($productPrice, 2) ?></span>
          <?php endif; ?>
        </div>

        <p class="product-stock <?= $productStock > 0 ? 'in-stock' : 'out-stock' ?>">
          <?= $productStock > 0 ? ('In stock: '.$productStock) : 'Out of stock' ?>
        </p>

        <div class="product-qty-wrap">
          <button type="button" class="qty-btn" data-qty-action="decrease">-</button>
          <input type="number" id="invqty_<?= $pid ?>" value="1" min="1" max="<?= max(1, $productStock) ?>">
          <button type="button" class="qty-btn" data-qty-action="increase">+</button>
        </div>
        <input type="hidden" value="<?= $productStock ?>" id="stock_<?= $pid ?>">

        <div class="product-cta-row">
          <a href="javascript:void(0);" id="cart_<?= $pid ?>" class="btn btn-primary"
             data-has-required-modifiers="<?= $hasRequiredModifiers ?>"
             onclick="addToCart('<?= $pid ?>','<?= $ptype ?>','detail','')">Add to Cart</a>
          <a href="javascript:void(0);" class="btn btn-sm btn-outline">Buy Now</a>
        </div>
      </div>
    </div>
  </div>
</section>

2. PRODUCT INFORMATION TABS (dynamic):
<section id="product-detail-tabs" class="product-tabs-section">
  <div class="container">
    <div class="product-tabs-nav">
      <button class="product-tab-btn active" data-tab-target="tab-description">Product Description</button>
      <button class="product-tab-btn" data-tab-target="tab-reviews">Reviews</button>
      <button class="product-tab-btn" data-tab-target="tab-details">Other Details</button>
    </div>
    <div class="product-tab-content active" id="tab-description">
      <p><?= nl2br(htmlspecialchars($productDescription)) ?></p>
    </div>
    <div class="product-tab-content" id="tab-reviews">
      <?php if(!empty($product_reviews) && is_array($product_reviews)): ?>
        <?php foreach($product_reviews as $review): ?>
          <div class="product-review-item">
            <strong><?= htmlspecialchars($review['author'] ?? 'Customer') ?></strong>
            <p><?= htmlspecialchars($review['content'] ?? '') ?></p>
          </div>
        <?php endforeach; ?>
      <?php else: ?>
        <p>No reviews available yet.</p>
      <?php endif; ?>
    </div>
    <div class="product-tab-content" id="tab-details">
      <?php if(!empty($product_attributes) && is_array($product_attributes)): ?>
        <ul class="product-attributes-list">
          <?php foreach($product_attributes as $attr): ?>
          <li><strong><?= htmlspecialchars($attr['label'] ?? 'Attribute') ?>:</strong> <?= htmlspecialchars($attr['value'] ?? '-') ?></li>
          <?php endforeach; ?>
        </ul>
      <?php else: ?>
        <p>Additional product details are not available.</p>
      <?php endif; ?>
    </div>
  </div>
</section>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOBAL RULES:
- Use getDynamicBaseUrl() for all CI4 links
- Use htmlspecialchars() for dynamic string output
- Use number_format() for prices
- Use $merchant_id in all route URLs
- NO hardcoded product data — always use $results inventory loop for product sections
- Product block must use CI4 inventory fields: merchant_id, inventory_id, name, price, special_price, stock_qty, file_type, object_key, price_type, has_required_modifiers
- Product detail page must use dynamic fields from $product/$invimgs/$product_reviews/$product_attributes
- Product detail must include breadcrumb context and "Back to Products" navigation using selected category/subcategory when available
- Product image slider must initialize Swiper ONLY on .big-image-slider (not on thumbnail slider)
- Keep thumbnail container non-swiper: .thumbnail-slider > .l-thumbnail > .thumb-item
- Keep product image wrapper as .swiper-wrapper.l-big-img inside .big-image-slider
- CSS classes to use: .container, .section-padding, .section-title, .products-row, .product-col, .product-item, .product-img, .product-detail, .product-title, .price, .addCart-area, .no-products-msg
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
/* Product detail interactions (safe no-op if elements are absent) */
(function() {
  function initProductSwiper() {
    var sliderRoot = document.querySelector('.product-slider');
    if (!sliderRoot || !window.Swiper) { return; }
    if (sliderRoot.dataset.swiperInit === '1') { return; }

    var bigEl = sliderRoot.querySelector('.big-image-slider');
    var nextEl = sliderRoot.querySelector('.swiper-button-next');
    var prevEl = sliderRoot.querySelector('.swiper-button-prev');
    if (!bigEl) { return; }
    var totalSlides = bigEl.querySelectorAll('.swiper-wrapper .swiper-slide').length;
    var hasMultipleSlides = totalSlides > 1;

    var bigSwiper = new Swiper(bigEl, {
      spaceBetween: 10,
      observer: true,
      observeParents: true,
      autoHeight: true,
      slidesPerView: 1,
      navigation: hasMultipleSlides ? { nextEl: nextEl, prevEl: prevEl } : false,
      allowTouchMove: hasMultipleSlides
    });

    var thumbItems = sliderRoot.querySelectorAll('.thumbnail-slider .thumb-item');
    thumbItems.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var targetIndex = parseInt(btn.getAttribute('data-slide-index') || '0', 10);
        if (!isNaN(targetIndex)) {
          bigSwiper.slideTo(targetIndex);
        }
      });
    });

    function setActiveThumb(index) {
      thumbItems.forEach(function(btn) { btn.classList.remove('active'); });
      var active = sliderRoot.querySelector('.thumbnail-slider .thumb-item[data-slide-index="' + index + '"]');
      if (active) { active.classList.add('active'); }
    }

    if (hasMultipleSlides) {
      bigSwiper.on('slideChange', function() {
        setActiveThumb(bigSwiper.activeIndex);
      });
    } else {
      setActiveThumb(0);
    }

    sliderRoot.dataset.swiperInit = '1';
  }

  function ensureSwiperAssetsAndInit() {
    if (window.Swiper) {
      initProductSwiper();
      return;
    }

    if (!document.querySelector('link[data-swiper-css]')) {
      var css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css';
      css.setAttribute('data-swiper-css', '1');
      document.head.appendChild(css);
    }

    var existingScript = document.querySelector('script[data-swiper-js]');
    if (existingScript) {
      existingScript.addEventListener('load', initProductSwiper, { once: true });
      return;
    }

    var js = document.createElement('script');
    js.src = 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js';
    js.async = true;
    js.setAttribute('data-swiper-js', '1');
    js.addEventListener('load', initProductSwiper, { once: true });
    document.body.appendChild(js);
  }

  ensureSwiperAssetsAndInit();

  document.querySelectorAll('[data-qty-action]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var input = document.querySelector('.product-qty-wrap input[type="number"]');
      if (!input) { return; }
      var min = parseInt(input.getAttribute('min') || '1', 10);
      var max = parseInt(input.getAttribute('max') || '999999', 10);
      var value = parseInt(input.value || '1', 10);
      if (btn.getAttribute('data-qty-action') === 'increase') {
        value = Math.min(max, value + 1);
      } else {
        value = Math.max(min, value - 1);
      }
      input.value = String(value);
    });
  });

  document.querySelectorAll('.product-tab-btn[data-tab-target]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var targetId = btn.getAttribute('data-tab-target');
      document.querySelectorAll('.product-tab-btn').forEach(function(b) { b.classList.remove('active'); });
      document.querySelectorAll('.product-tab-content').forEach(function(c) { c.classList.remove('active'); });
      btn.classList.add('active');
      var target = document.getElementById(targetId);
      if (target) { target.classList.add('active'); }
    });
  });
})();
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
   - NON-sticky / static position (do not use fixed or sticky)
   - Logo left, nav right
   - .nav-link.active uses var(--primary)

6. TIER 2 Category nav (.category-nav-bar, .category-nav-list, .cat-link)
   - Must be premium and easy to read for SME/MSME users
   - Use horizontal scrolling category rail with generous spacing between chips
   - Add left/right arrow controls (.category-nav-arrow-prev / .category-nav-arrow-next) to scroll categories
   - Keep .category-nav-scroll as overflow-x auto with smooth scrolling and subtle/hidden scrollbar styling
   - Keep dropdown menus positioned absolutely so opening subcategories does not create page/navbar vertical scrolling
   - Keep .cat-link default state neutral; DO NOT apply primary bg/text to all .cat-link or .dropdown-toggle by default
   - .cat-link.active uses var(--primary) styling, and ONLY one category should appear active at a time
   - .category-nav-item.open should only control dropdown visibility; it must not force active/highlight styles on non-active links
   - .dropdown-menu styles (Bootstrap-compatible)
    - Subcategory dropdown MUST NOT be scrollable internally: do not set max-height or overflow-y:auto on .dropdown-menu
    - Enforce this explicitly in CSS: .category-submenu { max-height: none !important; overflow: visible !important; overflow-y: visible !important; }
    - Ensure users can see all subcategories at once (use natural height and, when long, a wider or multi-column dropdown)
   - Must include fallback rule: .category-nav-item.open > .dropdown-menu { display: block; }
   - Must include hover behavior rule on desktop: .category-nav-item.dropdown:hover > .dropdown-menu { display: block; }

7. Hamburger button (.hamburger-btn — hidden desktop, visible mobile)
   Mobile menu: #mainNavMenu.open shows as column

8. Hero section (.hero-section, .hero-inner, .hero-content, .hero-headline, .hero-subheadline, .hero-cta, .hero-image)
   - Flexbox two-column layout (text left, image right)
   - Stacks on mobile

9. Products section (.products-section, .products-row, .product-col, .product-item, .product-img, .product-detail, .product-title, .price, .addCart-area, .no-products-msg)
   - Use isolated, box-style card layout that does NOT depend on external Bootstrap column classes
   - .products-row should be CSS Grid with fixed card width behavior: repeat(auto-fill, minmax(240px, 280px)) and centered tracks
   - .products-row.single-product must keep a single card box width (do not stretch full row)
   - .product-col should be width: 100% with max-width around 280-320px
   - .product-item card hover: translateY(-4px) + box-shadow
   - .product-img img uses fixed visual height + object-fit: cover for consistent card thumbnails

10. CTA section (.cta-section, .cta-inner — centered, background var(--primary-light))

11. Product detail page styles (.product-detail-section, .product-back-link, .product-breadcrumb-right, .product-detail-layout, .product-slider, .thumbnail-slider, .thumb-item, .big-image-slider, .l-thumbnail, .l-big-img, .swiper-slide, .swiper-button-next, .swiper-button-prev, .product-info-col, .product-detail-title, .product-detail-price, .price-current, .price-old, .product-stock, .product-qty-wrap, .qty-btn, .product-cta-row, .product-tabs-nav, .product-tab-btn, .product-tab-content, .product-tab-content.active, .product-attributes-list)
    - Desktop: two-column layout (gallery left, info right), stack on mobile
    - Do NOT render any breadcrumb above the image/gallery block on the left side
    - Keep only right-side breadcrumb/meta line at the top of .product-info-col
    - .product-breadcrumb-right should appear directly above title with smaller muted text and enough bottom spacing
    - .product-back-link should be visible and easy to use for returning to listing context
    - Swiper calls should be applied to .big-image-slider only (thumbnail is click-to-select, non-swiper)
    - Define explicit big slider size: .big-image-slider { width: 100%; max-width: 520px; min-height: 420px; }
    - .product-slider.single-image should hide thumbnail rail and keep centered big image with the same visual box ratio
    - On tablet: .big-image-slider max-width 100% with min-height around 340px; on mobile min-height around 260px
    - Ensure thumbnail column has fixed usable width and big image area has stable minimum height
    - Tab buttons have clear active state and only active tab content is visible
    - Include .btn-outline style for secondary CTA button on detail page

12. FAQ styles (.faq-accordion, .faq-item, .faq-question, .faq-answer, .faq-icon)
    - .faq-answer: max-height: 0; overflow: hidden; transition for accordion

13. Contact CTA section (.contact-cta-section, .contact-cta-inner — centered)

14. Footer (.site-footer, .footer-grid, .footer-col, .footer-brand, .footer-links, .footer-contact, .footer-bottom)
    - .footer-grid: 3-column grid, collapses to 1 on mobile

15. Buttons (.btn, .btn-primary, .btn-sm, .btn-outline)
    - .btn-primary uses var(--primary), hover uses var(--primary-dark)
    - .btn-outline uses border + text in primary color, filled on hover

16. Media queries (max-width: 768px):
    - Category nav remains horizontally scrollable with touch swipe
    - Arrow controls may be reduced in size or hidden on very small screens
    - Product grid: 2 columns → 1 column at 480px
    - Product detail page stacks into one column and keeps controls tappable
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