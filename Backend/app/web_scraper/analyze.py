"""
Analysis Pipeline
AI-powered analysis of scraped website data
"""
import sys
import json
import os
import logging
from datetime import datetime
from pathlib import Path

from .llm import LLMClient
from .analyzers import StructureAnalyzer, DesignAnalyzer, ContentAnalyzer

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Main pipeline for analyzing scraped data
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient()
        self.structure_analyzer = StructureAnalyzer(self.llm)
        self.design_analyzer = DesignAnalyzer(self.llm)
        self.content_analyzer = ContentAnalyzer(self.llm)
    
    def analyze(self, scraped_data: dict, user_info: dict = None) -> dict:
        """
        Run full analysis pipeline
        """
        print(f"\n{'='*60}")
        print(f"STARTING AI ANALYSIS")
        print(f"{'='*60}\n")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'source_url': scraped_data.get('url', 'Unknown'),
            'analysis': {}
        }
        
        # Structure analysis
        try:
            results['analysis']['structure'] = self.structure_analyzer.analyze(scraped_data)
        except Exception as e:
            print(f"[ERROR] Structure analysis failed: {str(e)}")
            results['analysis']['structure'] = {'error':str(e)}
        
        # Design analysis
        try:
            results['analysis']['design'] = self.design_analyzer.analyze(scraped_data)
        except Exception as e:
            print(f"[ERROR] Design analysis failed: {str(e)}")
            results['analysis']['design'] = {'error': str(e)}
        
        # Content generation (if user info provided)
        if user_info:
            try:
                results['analysis']['content'] = self.content_analyzer.analyze(scraped_data, user_info)
            except Exception as e:
                print(f"[ERROR] Content generation failed: {str(e)}")
                results['analysis']['content'] = {'error': str(e)}
        else:
            print("[INFO] Skipping content generation (no user info provided)")
        
        print(f"\n{'='*60}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*60}\n")
        
        return results


def load_scraped_data(file_path: str) -> dict:
    """
    Load scraped data from JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_analysis(analysis: dict, output_path: str):
    """
    Save analysis results to JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Analysis saved to: {output_path}")


def load_config(config_path: str = None) -> dict:
    """
    Load business info from config file
    """
    if config_path is None:
        # Try default locations
        default_paths = [
            'AnalyesData/analysis_config.json',
            'AnalyesData\\analysis_config.json',
            'analysis_config.json',
            'config/analysis_config.json',
            '../analysis_config.json'
        ]
        for path in default_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path and os.path.exists(config_path):
        print(f"[INFO] Loading config from: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None


def main():
    """
    CLI entry point
    """
    if len(sys.argv) < 2:
        print("Usage: python -m Scraper.analyze <scraped_json_file> [options]")
        print("\nOptions:")
        print("  --config           Path to analysis_config.json (optional)")
        print("  --business-name    Your business name")
        print("  --industry         Your industry")
        print("  --description      Business description")
        print("  --brand-voice      Brand voice (e.g., 'professional, friendly')")
        print("\nExamples:")
        print("  # Use config file (recommended):")
        print("  python -m Scraper.analyze scraped_data/file.json")
        print("\n  # Or specify manually:")
        print("  python -m Scraper.analyze scraped_data/file.json --business-name \"My Store\"")
        sys.exit(1)
    
    # Parse arguments
    input_file = sys.argv[1]
    args = sys.argv[2:]
    
    # Try to load from config file first
    config_path = None
    if '--config' in args:
        idx = args.index('--config')
        config_path = args[idx + 1] if idx + 1 < len(args) else None
    
    user_info = load_config(config_path)
    
    # Override with command line args if provided
    if '--business-name' in args:
        idx = args.index('--business-name')
        business_name = args[idx + 1] if idx + 1 < len(args) else 'Your Business'
        
        user_info = {
            'business_name': business_name,
            'industry': args[args.index('--industry') + 1] if '--industry' in args else 'General',
            'description': args[args.index('--description') + 1] if '--description' in args else '',
            'brand_voice': args[args.index('--brand-voice') + 1] if '--brand-voice' in args else 'Professional'
        }
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)
    
    # Load scraped data
    print(f"[INFO] Loading scraped data from: {input_file}")
    scraped_data = load_scraped_data(input_file)
    
    # Run analysis
    try:
        pipeline = AnalysisPipeline()
        analysis = pipeline.analyze(scraped_data, user_info)
        
        # Save results
        input_path = Path(input_file)
        output_file = input_path.parent / f"analysis_{input_path.stem}.json"
        save_analysis(analysis, str(output_file))
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        
        structure = analysis['analysis'].get('structure', {})
        if 'recommended_pages' in structure:
            print(f"\n📄 Recommended Pages: {len(structure['recommended_pages'])}")
            for page in structure['recommended_pages'][:5]:
                print(f"  - {page.get('suggested_name', 'Unknown')} ({page.get('page_type', 'custom')})")
        
        design = analysis['analysis'].get('design', {})
        if 'color_palette' in design:
            print(f"\n🎨 Color Palette:")
            for name, color in design['color_palette'].items():
                print(f"  - {name}: {color}")
        
        if 'typography' in design:
            print(f"\n✍️ Typography:")
            print(f"  - Headings: {design['typography'].get('heading_font', 'N/A')}")
            print(f"  - Body: {design['typography'].get('body_font', 'N/A')}")
        
        content = analysis['analysis'].get('content', {})
        if 'hero_section' in content:
            print(f"\n💬 Content Generated:")
            print(f"  - Headline: {content['hero_section'].get('headline', 'N/A')}")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
