import dspy  # type: ignore


class ImageDescriptionSignature(dspy.Signature):
    """Generate targeted image description for a specific section."""
    plan: str = dspy.InputField(
        desc="Complete website plan JSON"
    )
    section_name: str = dspy.InputField(
        desc="Section name (hero, features, testimonials, etc.)"
    )
    page_name: str = dspy.InputField(
        desc="Page name where section appears"
    )
    business_description: str = dspy.InputField(
        desc="Original business description"
    )
    image_description: str = dspy.OutputField(
        desc="""Professional DALL-E 3 image prompt optimized for web backgrounds.
        
        CRITICAL REQUIREMENTS:
        - NO text, letters, numbers, words, quotes, headings, UI elements
        - NO testimonial cards, review boxes, star ratings, speech bubbles
        - NO dashboards, website mockups, or UI screenshots
        - Images must be background/decorative only
        - Professional, modern, clean aesthetic
        - Suitable for overlaying web content
        - Soft lighting, minimal contrast, breathable composition
        - Aligned with website theme and section purpose
        """
    )
