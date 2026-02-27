import dspy  # type: ignore


class WebsitePlannerSignature(dspy.Signature):
    """Generate a CI4-compatible e-commerce website structure plan with design system."""
    description: str = dspy.InputField(
        desc="Business/brand description including shop name, merchant ID, colors, hero text, FAQ items"
    )
    plan: str = dspy.OutputField(
        desc="""JSON-formatted website plan. MUST follow this exact structure:

CRITICAL RULES:
- ALWAYS generate EXACTLY 2 pages: "home" and "faq" — no more, no less
- navigation MUST always be: ["home", "faq"]
- DO NOT add "about", "contact", "shop" or any other pages
- The ci4_context block MUST always be included with the available PHP variables

Required JSON structure:
{
    "pages": [
        {
            "name": "home",
            "purpose": "Main shop landing page with hero banner, dynamic category navigation, and product grid",
            "sections": ["hero_banner", "featured_products", "cta_banner"]
        },
        {
            "name": "faq",
            "purpose": "Frequently asked questions and customer support info",
            "sections": ["faq_hero", "faq_list", "contact_cta"]
        }
    ],
    "ci4_context": {
        "shop_mid": "1",
        "php_variables": [
            "$categories",
            "$subcategorieslist",
            "$products",
            "$merchant_id",
            "$search",
            "$filters",
            "$selected_category_id"
        ],
        "helper_function": "getDynamicBaseUrl()",
        "route_patterns": {
            "all_products":    "fshop/index/{mid}",
            "by_category":     "fshop/index/{mid}/{catid}",
            "by_subcategory":  "fshop/index/{mid}/{catid}?sub={subcatid}",
            "single_product":  "fshop/product/{mid}/{product_id}",
            "faq_page":        "fshop/faq/{mid}"
        }
    },
    "design_system": {
        "color_palette": {
            "primary":          "#3B82F6",
            "primary_dark":     "#2563EB",
            "primary_light":    "#DBEAFE",
            "secondary":        "#8B5CF6",
            "secondary_dark":   "#7C3AED",
            "secondary_light":  "#EDE9FE",
            "background":       "#FFFFFF",
            "surface":          "#F9FAFB",
            "text_primary":     "#111827",
            "text_secondary":   "#6B7280",
            "border":           "#E5E7EB",
            "success":          "#10B981",
            "warning":          "#F59E0B",
            "error":            "#EF4444"
        },
        "typography": {
            "heading_font": "Inter",
            "body_font":    "Inter",
            "font_weights": ["400", "500", "600", "700"],
            "type_scale": {
                "h1": "3rem",
                "h2": "2.25rem",
                "h3": "1.75rem",
                "h4": "1.5rem",
                "h5": "1.25rem",
                "h6": "1.125rem",
                "body": "1rem",
                "small": "0.875rem"
            },
            "line_heights": {
                "heading": "1.2",
                "body":    "1.6",
                "relaxed": "1.8"
            }
        },
        "spacing": {
            "base_unit":          "8px",
            "scale":              ["4px","8px","16px","24px","32px","48px","64px","96px"],
            "container_max_width":"1200px",
            "section_padding_y":  "80px",
            "section_padding_x":  "24px",
            "grid_gap":           "24px"
        },
        "components": {
            "button_style":       "rounded",
            "button_size_variants": ["sm","md","lg"],
            "card_style":         "elevated",
            "card_border_radius": "12px",
            "input_style":        "outline",
            "border_radius_base": "8px"
        },
        "responsive": {
            "breakpoints": {
                "mobile":  "768px",
                "tablet":  "1024px",
                "desktop": "1200px"
            },
            "mobile_first":      true,
            "mobile_nav_style":  "hamburger",
            "mobile_font_scale": 0.9
        },
        "interactions": {
            "transitions":       "smooth",
            "hover_effects":     true,
            "scroll_animations": ["fade","slide"],
            "page_transitions":  "fade"
        }
    },
    "image_sections":  ["hero_banner"],
    "navigation":      ["home", "faq"]
}

DESIGN GUIDANCE:
- Extract brand colors from the business description (primary_color mentioned by user)
- Use a color palette that matches the shop's brand identity
- Choose Google Fonts appropriate for an e-commerce shop (Inter, Poppins, Roboto, etc.)
- extract `shop_mid` from business description for ci4_context.shop_mid

CRITICAL:
- ALWAYS use valid hex color codes (e.g., "#3B82F6"), never color names like "blue" or "red"
- ALWAYS use real Google Fonts (Inter, Poppins, Roboto, Playfair Display, etc.)
- Return ONLY valid JSON, no markdown code fences, no extra text
- pages array MUST have EXACTLY 2 items: "home" then "faq"
- navigation MUST be exactly: ["home", "faq"]
        """
    )
