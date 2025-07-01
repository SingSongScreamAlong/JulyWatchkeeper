"""
AI Processor for WATCHKEEPER

This module implements AI processing of intelligence items using Ollama.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

from src.processors.base_processor import BaseProcessor
from src.utils.logger import get_logger
from src.utils.config import get_config

class AIProcessor(BaseProcessor):
    """
    AI processor for intelligence items
    
    This processor uses Ollama to analyze intelligence items, including:
    - Summarization
    - Key theme extraction
    - Threat classification
    - Geographic entity extraction
    - Missionary impact assessment
    """
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        """
        Initialize the AI processor
        
        Args:
            model_name: Name of the Ollama model to use
        """
        super().__init__("ai_processor")
        self.model_name = model_name
        self.config = get_config().get("processors", {}).get("ai", {})
        
        # Ollama API endpoint
        self.api_base = self.config.get("ollama_api", "http://localhost:11434")
        
        # Maximum concurrent requests to Ollama
        self.max_concurrent = self.config.get("max_concurrent", 1)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # System prompts for different processing tasks
        self.prompts = {
            "summarize": self._get_summarize_prompt(),
            "extract_themes": self._get_extract_themes_prompt(),
            "classify_threat": self._get_classify_threat_prompt(),
            "extract_locations": self._get_extract_locations_prompt(),
            "assess_impact": self._get_assess_impact_prompt()
        }
    
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with AI analysis
        """
        if not item.get("content"):
            self.logger.warning("Item has no content to process")
            return item
        
        # Create a copy of the item to avoid modifying the original
        processed_item = item.copy()
        
        # Add AI analysis section if it doesn't exist
        if "ai_analysis" not in processed_item:
            processed_item["ai_analysis"] = {}
        
        try:
            # Process in parallel for efficiency
            summary, themes, threat, locations, impact = await asyncio.gather(
                self._summarize(item),
                self._extract_themes(item),
                self._classify_threat(item),
                self._extract_locations(item),
                self._assess_impact(item)
            )
            
            # Add results to AI analysis
            processed_item["ai_analysis"]["summary"] = summary
            processed_item["ai_analysis"]["themes"] = themes
            processed_item["ai_analysis"]["threat"] = threat
            processed_item["ai_analysis"]["locations"] = locations
            processed_item["ai_analysis"]["missionary_impact"] = impact
            
            self.logger.debug(f"Successfully processed item with AI")
            
        except Exception as e:
            self.logger.error(f"Error in AI processing: {e}", exc_info=True)
        
        return processed_item
    
    async def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """
        Call Ollama API with a prompt
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            str: Model response
        """
        # Use semaphore to limit concurrent requests
        async with self.semaphore:
            try:
                url = f"{self.api_base}/api/generate"
                
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            self.logger.error(f"Ollama API error: {response.status}, {error_text}")
                            return ""
                        
                        result = await response.json()
                        return result.get("response", "")
            
            except Exception as e:
                self.logger.error(f"Error calling Ollama API: {e}", exc_info=True)
                return ""
    
    async def _summarize(self, item: Dict[str, Any]) -> str:
        """
        Generate a concise summary of the intelligence item
        
        Args:
            item: Intelligence item to summarize
            
        Returns:
            str: Summary of the item
        """
        content = item.get("content", "")
        title = item.get("title", "")
        
        prompt = f"Title: {title}\n\nContent: {content}\n\nProvide a concise summary of this intelligence item in 2-3 sentences."
        
        return await self._call_ollama(prompt, self.prompts["summarize"])
    
    async def _extract_themes(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract key themes from the intelligence item
        
        Args:
            item: Intelligence item to analyze
            
        Returns:
            List[Dict[str, Any]]: List of themes with relevance scores
        """
        content = item.get("content", "")
        title = item.get("title", "")
        
        prompt = f"Title: {title}\n\nContent: {content}\n\nIdentify the top 3-5 key themes in this intelligence item. For each theme, provide a short name, brief description, and relevance score (0.0-1.0). Format your response as a JSON array."
        
        response = await self._call_ollama(prompt, self.prompts["extract_themes"])
        
        # Parse JSON response
        try:
            # Extract JSON array from the response
            json_str = self._extract_json_from_text(response)
            if json_str:
                themes = json.loads(json_str)
                return themes
        except Exception as e:
            self.logger.error(f"Error parsing themes JSON: {e}", exc_info=True)
        
        # Fallback if JSON parsing fails
        return [{"name": "parsing_error", "description": "Failed to parse themes", "relevance": 0.0}]
    
    async def _classify_threat(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the threat level and type in the intelligence item
        
        Args:
            item: Intelligence item to classify
            
        Returns:
            Dict[str, Any]: Threat classification with level, type, and confidence
        """
        content = item.get("content", "")
        title = item.get("title", "")
        
        prompt = f"Title: {title}\n\nContent: {content}\n\nClassify the threat described in this intelligence item. Provide the threat level (None, Low, Medium, High, Critical), threat type (e.g., Terrorism, Civil Unrest, Natural Disaster, Health, etc.), and your confidence in this assessment (0.0-1.0). Format your response as a JSON object."
        
        response = await self._call_ollama(prompt, self.prompts["classify_threat"])
        
        # Parse JSON response
        try:
            # Extract JSON object from the response
            json_str = self._extract_json_from_text(response)
            if json_str:
                threat = json.loads(json_str)
                return threat
        except Exception as e:
            self.logger.error(f"Error parsing threat JSON: {e}", exc_info=True)
        
        # Fallback if JSON parsing fails
        return {"level": "Unknown", "type": "Unknown", "confidence": 0.0}
    
    async def _extract_locations(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract geographic locations mentioned in the intelligence item
        
        Args:
            item: Intelligence item to analyze
            
        Returns:
            List[Dict[str, Any]]: List of locations with coordinates and confidence
        """
        content = item.get("content", "")
        title = item.get("title", "")
        
        prompt = f"Title: {title}\n\nContent: {content}\n\nExtract all geographic locations (countries, cities, regions) mentioned in this intelligence item. For each location, provide the name, location type (Country, City, Region, etc.), and your confidence in this extraction (0.0-1.0). Format your response as a JSON array."
        
        response = await self._call_ollama(prompt, self.prompts["extract_locations"])
        
        # Parse JSON response
        try:
            # Extract JSON array from the response
            json_str = self._extract_json_from_text(response)
            if json_str:
                locations = json.loads(json_str)
                return locations
        except Exception as e:
            self.logger.error(f"Error parsing locations JSON: {e}", exc_info=True)
        
        # Fallback if JSON parsing fails
        return []
    
    async def _assess_impact(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the potential impact on missionary operations
        
        Args:
            item: Intelligence item to assess
            
        Returns:
            Dict[str, Any]: Impact assessment with severity and recommendations
        """
        content = item.get("content", "")
        title = item.get("title", "")
        
        prompt = f"Title: {title}\n\nContent: {content}\n\nAssess the potential impact of this intelligence on Christian missionary operations in the region. Provide an impact severity (None, Low, Medium, High, Critical), a brief explanation, and 1-2 specific recommendations for missionaries. Format your response as a JSON object."
        
        response = await self._call_ollama(prompt, self.prompts["assess_impact"])
        
        # Parse JSON response
        try:
            # Extract JSON object from the response
            json_str = self._extract_json_from_text(response)
            if json_str:
                impact = json.loads(json_str)
                return impact
        except Exception as e:
            self.logger.error(f"Error parsing impact JSON: {e}", exc_info=True)
        
        # Fallback if JSON parsing fails
        return {"severity": "Unknown", "explanation": "Failed to assess impact", "recommendations": []}
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract JSON from text that might contain other content
        
        Args:
            text: Text that might contain JSON
            
        Returns:
            str: Extracted JSON string
        """
        # Look for JSON between brackets or braces
        import re
        
        # Try to find array
        array_match = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if array_match:
            return f"[{array_match.group(1)}]"
        
        # Try to find object
        object_match = re.search(r'\{(.*?)\}', text, re.DOTALL)
        if object_match:
            return f"{{{object_match.group(1)}}}"
        
        return ""
    
    def _get_summarize_prompt(self) -> str:
        """Get the system prompt for summarization"""
        return """You are an intelligence analyst summarizing information for missionary operations.
Your task is to create concise, factual summaries of intelligence items.
Focus on key facts, locations, events, and potential threats.
Be objective and avoid speculation.
Your summary should be 2-3 sentences long and highlight the most important information."""
    
    def _get_extract_themes_prompt(self) -> str:
        """Get the system prompt for theme extraction"""
        return """You are an intelligence analyst extracting key themes from intelligence items.
Identify the most important themes in the content related to security, travel, political, religious, health, or natural disaster topics.
For each theme, provide:
1. A short name (1-3 words)
2. A brief description (1 sentence)
3. A relevance score (0.0-1.0) indicating how central this theme is to the intelligence item

Format your response as a JSON array of objects with "name", "description", and "relevance" fields.
Example: [{"name": "Civil Unrest", "description": "Ongoing protests in the capital city with potential for violence", "relevance": 0.8}]"""
    
    def _get_classify_threat_prompt(self) -> str:
        """Get the system prompt for threat classification"""
        return """You are an intelligence analyst classifying threats for missionary operations.
Assess the threat level and type described in the intelligence item.

Threat levels:
- None: No discernible threat
- Low: Minimal threat requiring basic awareness
- Medium: Moderate threat requiring increased vigilance
- High: Significant threat requiring active mitigation measures
- Critical: Severe threat requiring immediate action

Threat types include: Terrorism, Civil Unrest, Crime, Political Instability, Natural Disaster, Health, Infrastructure, etc.

Format your response as a JSON object with "level", "type", and "confidence" fields.
Example: {"level": "Medium", "type": "Civil Unrest", "confidence": 0.7}

Your confidence score (0.0-1.0) should reflect your certainty in this assessment based on the available information."""
    
    def _get_extract_locations_prompt(self) -> str:
        """Get the system prompt for location extraction"""
        return """You are an intelligence analyst extracting geographic information from intelligence items.
Identify all locations mentioned in the content, including countries, cities, regions, and specific places.
For each location, provide:
1. The name of the location
2. The location type (Country, City, Region, Landmark, etc.)
3. A confidence score (0.0-1.0) indicating your certainty that this is a geographic location

Format your response as a JSON array of objects with "name", "type", and "confidence" fields.
Example: [{"name": "Paris", "type": "City", "confidence": 0.95}, {"name": "France", "type": "Country", "confidence": 0.99}]"""
    
    def _get_assess_impact_prompt(self) -> str:
        """Get the system prompt for missionary impact assessment"""
        return """You are an intelligence analyst assessing potential impacts on Christian missionary operations.
Evaluate how the information in this intelligence item might affect missionaries working in the region.

Impact severity levels:
- None: No impact on missionary operations
- Low: Minimal impact, normal operations can continue
- Medium: Moderate impact, some adjustments to operations recommended
- High: Significant impact, substantial changes to operations required
- Critical: Severe impact, evacuation or suspension of operations may be necessary

Format your response as a JSON object with "severity", "explanation", and "recommendations" fields.
Example: {
  "severity": "Medium",
  "explanation": "Ongoing protests may disrupt transportation and create security concerns in the capital city",
  "recommendations": ["Avoid demonstration areas in the capital", "Maintain low profile when traveling"]
}

Provide 1-2 specific, actionable recommendations for missionaries based on this intelligence."""
