# AI Analysis Layer - Quick Start

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up Azure OpenAI credentials:**
```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your Azure OpenAI credentials:
AZURE_AI_ENDPOINT_URL=https://your-resource.openai.azure.com/
AZURE_AI_DEPLOYMENT_NAME=gpt-4o
AZURE_AI_APP_VERSION=2024-02-15-preview
AZURE_AI_TOKEN=your-azure-api-key-here
```


## Usage

### 1. Analyze Scraped Data (Structure + Design Only)
```bash
python -m Scraper.analyze scraped_data/scraped_20260211_154207.json
```

### 2. Analyze with Content Generation
```bash
python -m Scraper.analyze scraped_data/scraped_20260211_154207.json \
  --business-name "My Store" \
  --industry "E-commerce" \
  --description "Online retail for home goods" \
  --brand-voice "Modern, friendly, trustworthy"
```

### 3. Python API
```python
from Scraper import AnalysisPipeline
import json

# Load scraped data
with open('scraped_data/file.json') as f:
    data = json.load(f)

# Run analysis
pipeline = AnalysisPipeline()
analysis = pipeline.analyze(
    scraped_data=data,
    user_info={
        'business_name': 'My Business',
        'industry': 'Technology',
        'description': 'AI-powered solutions',
        'brand_voice': 'Innovative and professional'
    }
)

# Access results
print(analysis['analysis']['structure']['recommended_pages'])
print(analysis['analysis']['design']['color_palette'])
print(analysis['analysis']['content']['hero_section'])
```

## Output

Analysis creates a new file: `analysis_<original_name>.json`

Example output structure:
```json
{
  "timestamp": "2026-02-11T16:45:00",
  "source_url": "https://lights.com",
  "analysis": {
    "structure": {
      "recommended_pages": [...],
      "navigation_structure": {...},
      "content_patterns": [...]
    },
    "design": {
      "color_palette": {...},
      "typography": {...},
      "design_style": [...]
    },
    "content": {
      "hero_section": {...},
      "value_propositions": [...],
      "section_suggestions": [...]
    }
  }
}
```

## Cost Estimation

Using `gpt-4o-mini` (recommended):
- Small site (5 pages): ~$0.01-$0.05
- Medium site (20 pages): ~$0.05-$0.15
- Large site (50 pages): ~$0.10-$0.30

Using `gpt-4o`:
- ~10x more expensive but higher quality

## Modules

- **structure_analyzer.py** - Extracts page types and navigation
- **design_analyzer.py** - Extracts colors, fonts, design patterns
- **content_analyzer.py** - Generates original content
- **llm_client.py** - OpenAI API integration
- **prompts.py** - LLM prompt templates
