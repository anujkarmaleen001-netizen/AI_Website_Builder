# Advanced Web Scraper - Quick Start Guide

## Installation

```bash
cd d:\Ai_project_landing_page\latest_Ai_webuilder
pip install -r requirements.txt
```

## Usage

### Option 1: Command Line
```bash
python -m Scraper.main https://example.com 10
```

### Option 2: Python Script
```python
from Scraper import ScraperPipeline

pipeline = ScraperPipeline(output_dir='scraped_data')
result = pipeline.run('https://example.com', max_pages=10)

print(f"Platform: {result['platform']['platform_name']}")
print(f"Colors found: {len(result['assets']['colors'])}")
```

## What It Does

1. **Validates URL** - Checks if accessible and robots.txt compliant
2. **Detects Platform** - WordPress, Shopify, WooCommerce, etc.
3. **Parses Sitemap** - Finds and extracts URLs from sitemap
4. **Scrapes Content** - Headings, navigation, meta tags, sections
5. **Extracts Assets** - Logo, favicon, colors, fonts, images
6. **Saves Results** - JSON file in `scraped_data/` folder

## Output Example

```json
{
  "platform": {
    "platform_name": "Shopify",
    "confidence": 100,
    "indicators": ["Shopify CDN found", "Shopify JavaScript found"]
  },
  "assets": {
    "logo": "https://example.com/logo.png",
    "colors": ["#C86800", "#fff", "#505050"],
    "fonts": ["Muli", "Chronicle Display"]
  },
  "summary": {
    "total_pages_scraped": 10,
    "colors_found": 59,
    "fonts_found": 4,
    "has_logo": true
  }
}
```

## Test It Now!

Try with a real website:
```bash
python -m Scraper.main https://lights.com 5
```
