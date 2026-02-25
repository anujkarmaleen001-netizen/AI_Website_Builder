import dspy  # type: ignore


class WebsitePlannerSignature(dspy.Signature):
    """Generate a comprehensive website structure plan with detailed design system."""
    description: str = dspy.InputField(
        desc="User's business/product description"
    )
    plan: str = dspy.OutputField(
        desc="""JSON-formatted website plan including:
        - pages: Array of page objects with name, purpose, and sections
        - design_system: Comprehensive design specification object with:
          * color_palette: Full color scheme with hex codes (primary, primary_dark, primary_light, secondary, background, surface, text_primary, text_secondary, border, success, warning, error)
          * typography: Complete type system (heading_font, body_font, font_weights, type_scale, line_heights)
          * spacing: Layout spacing system (base_unit, scale, container_max_width, section_padding_y, section_padding_x, grid_gap)
          * components: Component styling (button_style, card_style, input_style, border_radius_base, etc.)
          * responsive: Mobile/tablet strategy (breakpoints, mobile_first, mobile_nav_style, mobile_font_scale)
          * interactions: Animation preferences (transitions, hover_effects, scroll_animations, page_transitions)
        - image_sections: Array of section names requiring images (hero, features, testimonials)
        - navigation: Array of navigation items
        
        Example structure:
        {
            "pages": [
                {"name": "home", "purpose": "Landing page", "sections": ["hero", "features", "testimonials", "cta"]},
                {"name": "about", "purpose": "About page", "sections": ["story", "team", "values"]},
                {"name": "contact", "purpose": "Contact page", "sections": ["form", "info"]}
            ],
            "design_system": {
                "color_palette": {
                    "primary": "#3B82F6",
                    "primary_dark": "#2563EB",
                    "primary_light": "#DBEAFE",
                    "secondary": "#8B5CF6",
                    "secondary_dark": "#7C3AED",
                    "secondary_light": "#EDE9FE",
                    "background": "#FFFFFF",
                    "surface": "#F9FAFB",
                    "text_primary": "#111827",
                    "text_secondary": "#6B7280",
                    "border": "#E5E7EB",
                    "success": "#10B981",
                    "warning": "#F59E0B",
                    "error": "#EF4444"
                },
                "typography": {
                    "heading_font": "Inter",
                    "body_font": "Inter",
                    "font_weights": ["400", "500", "600", "700"],
                    "type_scale": {
                        "h1": "3.5rem",
                        "h2": "2.5rem",
                        "h3": "2rem",
                        "h4": "1.5rem",
                        "h5": "1.25rem",
                        "h6": "1.125rem",
                        "body": "1rem",
                        "small": "0.875rem"
                    },
                    "line_heights": {
                        "heading": "1.2",
                        "body": "1.6",
                        "relaxed": "1.8"
                    }
                },
                "spacing": {
                    "base_unit": "8px",
                    "scale": ["4px", "8px", "16px", "24px", "32px", "48px", "64px", "96px"],
                    "container_max_width": "1200px",
                    "section_padding_y": "80px",
                    "section_padding_x": "24px",
                    "grid_gap": "24px"
                },
                "components": {
                    "button_style": "rounded",
                    "button_size_variants": ["sm", "md", "lg"],
                    "card_style": "elevated",
                    "card_border_radius": "12px",
                    "input_style": "outline",
                    "border_radius_base": "8px"
                },
                "responsive": {
                    "breakpoints": {
                        "mobile": "768px",
                        "tablet": "1024px",
                        "desktop": "1200px"
                    },
                    "mobile_first": true,
                    "mobile_nav_style": "hamburger",
                    "mobile_font_scale": 0.9
                },
                "interactions": {
                    "transitions": "smooth",
                    "hover_effects": true,
                    "scroll_animations": ["fade", "slide"],
                    "page_transitions": "fade"
                }
            },
            "image_sections": ["hero", "features", "testimonials"],
            "navigation": ["home", "about", "features", "contact"]
        }
        
        CRITICAL: Always use valid hex color codes (e.g., "#3B82F6"), never generic names like "blue" or "red".
        CRITICAL: Ensure all Google Fonts are real and commonly available (Inter, Poppins, Roboto, Playfair Display, etc.)
        CRITICAL: Return ONLY valid JSON, no markdown code fences, no extra text.
        """
    )
