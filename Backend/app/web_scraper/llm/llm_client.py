"""
LLM Client for AI Analysis
Supports Azure OpenAI
"""
import os
import json
from typing import Dict, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    Client for interacting with Azure OpenAI
    """
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, 
                 deployment: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize Azure OpenAI client
        
        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_AI_TOKEN env var)
            endpoint: Azure OpenAI endpoint URL (defaults to AZURE_AI_ENDPOINT_URL env var)
            deployment: Azure deployment name (defaults to AZURE_AI_DEPLOYMENT_NAME env var)
            api_version: API version (defaults to AZURE_AI_APP_VERSION env var)
        """
        self.api_key = api_key or os.getenv('AZURE_AI_TOKEN')
        self.endpoint = endpoint or os.getenv('AZURE_AI_ENDPOINT_URL')
        self.deployment = deployment or os.getenv('AZURE_AI_DEPLOYMENT_NAME')
        self.api_version = api_version or os.getenv('AZURE_AI_APP_VERSION', '2024-02-15-preview')
        
        if not self.api_key:
            raise ValueError(
                "Azure AI API key not found. Set AZURE_AI_TOKEN environment variable or pass api_key parameter."
            )
        
        if not self.endpoint:
            raise ValueError(
                "Azure AI endpoint not found. Set AZURE_AI_ENDPOINT_URL environment variable or pass endpoint parameter."
            )
        
        if not self.deployment:
            raise ValueError(
                "Azure AI deployment not found. Set AZURE_AI_DEPLOYMENT_NAME environment variable or pass deployment parameter."
            )
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        
        print(f"[INFO] Azure OpenAI initialized - Deployment: {self.deployment}")
    
    def analyze(self, prompt: str, system_message: str = "You are a helpful AI assistant.") -> Dict:
        """
        Send a prompt to the LLM and get structured JSON response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,  # Azure uses deployment name
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                print(f"[WARNING] Failed to parse JSON response. Raw output:")
                print(result)
                return {"error": "Failed to parse JSON", "raw_response": result}
        
        except Exception as e:
            print(f"[ERROR] LLM API call failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_structure(self, prompt: str) -> Dict:
        """
        Analyze website structure
        """
        return self.analyze(
            prompt=prompt,
            system_message="You are an expert website structure analyst. Always respond with valid JSON."
        )
    
    def analyze_design(self, prompt: str) -> Dict:
        """
        Analyze design patterns
        """
        return self.analyze(
            prompt=prompt,
            system_message="You are an expert design system analyst. Always respond with valid JSON."
        )
    
    def generate_content(self, prompt: str) -> Dict:
        """
        Generate original content
        """
        return self.analyze(
            prompt=prompt,
            system_message="You are an expert content strategist. Generate original, compelling content. Always respond with valid JSON."
        )

