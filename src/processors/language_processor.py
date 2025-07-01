"""
Language Processor for WATCHKEEPER

This module implements multi-language processing for intelligence items.
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

from src.processors.base_processor import BaseProcessor
from src.utils.logger import get_logger
from src.utils.config import get_config

class LanguageProcessor(BaseProcessor):
    """
    Language processor for intelligence items
    
    This processor handles multi-language processing:
    1. Language detection
    2. Translation to English
    3. Language-specific processing
    """
    
    def __init__(self):
        """Initialize the language processor"""
        super().__init__("language_processor")
        self.config = get_config().get("processors", {}).get("language", {})
        
        # Supported languages
        self.supported_languages = {
            "en": "English",
            "fr": "French",
            "de": "German"
        }
        
        # Translation API configuration
        self.translation_api = self.config.get("translation_api", "ollama")
        self.api_key = self.config.get("api_key", "")
        self.model_name = self.config.get("model_name", "llama3.1:8b")
        
        # Ollama API endpoint
        self.api_base = self.config.get("ollama_api", "http://localhost:11434")
        
        # Maximum concurrent requests
        self.max_concurrent = self.config.get("max_concurrent", 1)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Language detection patterns
        self.language_patterns = {
            "fr": ["le", "la", "les", "un", "une", "des", "ce", "cette", "ces", "est", "sont", "et", "ou", "mais", "pour", "dans", "avec", "sans", "sur", "sous", "entre", "avant", "après", "pendant", "depuis", "jusqu'à", "vers", "selon", "malgré", "parce que", "car", "donc", "ainsi", "alors", "cependant", "néanmoins", "toutefois", "pourtant", "quand", "lorsque", "si", "quoique", "bien que"],
            "de": ["der", "die", "das", "ein", "eine", "ist", "sind", "und", "oder", "aber", "für", "in", "mit", "ohne", "auf", "unter", "zwischen", "vor", "nach", "während", "seit", "bis", "zu", "nach", "gemäß", "trotz", "weil", "denn", "deshalb", "so", "dann", "jedoch", "dennoch", "trotzdem", "wenn", "als", "ob", "obwohl"]
        }
    
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item for language handling
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with language information and translations
        """
        if not item.get("content"):
            self.logger.warning("Item has no content to process")
            return item
        
        # Create a copy of the item to avoid modifying the original
        processed_item = item.copy()
        
        # Add language_data section if it doesn't exist
        if "language_data" not in processed_item:
            processed_item["language_data"] = {}
        
        try:
            # Get content and title
            content = item.get("content", "")
            title = item.get("title", "")
            
            # Detect language
            detected_language = self._detect_language(content)
            processed_item["language_data"]["detected_language"] = detected_language
            
            # If not English, translate to English
            if detected_language != "en":
                self.logger.info(f"Translating content from {self.supported_languages.get(detected_language, detected_language)} to English")
                
                # Translate title and content
                translated_title = await self._translate(title, detected_language, "en")
                translated_content = await self._translate(content, detected_language, "en")
                
                # Store original and translated content
                processed_item["language_data"]["original"] = {
                    "title": title,
                    "content": content
                }
                
                processed_item["language_data"]["translated"] = {
                    "title": translated_title,
                    "content": translated_content
                }
                
                # Update item with translated content for downstream processing
                processed_item["title"] = translated_title
                processed_item["content"] = translated_content
                processed_item["language_data"]["is_translated"] = True
            else:
                processed_item["language_data"]["is_translated"] = False
            
            self.logger.debug(f"Processed language: {self.supported_languages.get(detected_language, detected_language)}")
            
        except Exception as e:
            self.logger.error(f"Error in language processing: {e}", exc_info=True)
        
        return processed_item
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Language code (en, fr, de) or 'unknown'
        """
        # Default to English if no text
        if not text:
            return "en"
        
        # Simple word-based language detection
        text = text.lower()
        
        # Count pattern matches for each language
        scores = {"en": 0}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                # Count whole word matches
                import re
                matches = len(re.findall(r'\b' + re.escape(pattern) + r'\b', text))
                score += matches
            
            scores[lang] = score
        
        # If no strong signals for other languages, default to English
        if max(scores.values()) < 3:
            return "en"
        
        # Return the language with the highest score
        return max(scores, key=scores.get)
    
    async def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            str: Translated text
        """
        if self.translation_api == "ollama":
            return await self._translate_with_ollama(text, source_lang, target_lang)
        elif self.translation_api == "google":
            return await self._translate_with_google(text, source_lang, target_lang)
        else:
            self.logger.error(f"Unsupported translation API: {self.translation_api}")
            return text
    
    async def _translate_with_ollama(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Ollama
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            str: Translated text
        """
        # Use semaphore to limit concurrent requests
        async with self.semaphore:
            try:
                url = f"{self.api_base}/api/generate"
                
                source_name = self.supported_languages.get(source_lang, source_lang)
                target_name = self.supported_languages.get(target_lang, target_lang)
                
                system_prompt = f"""You are a professional translator from {source_name} to {target_name}.
Translate the following text accurately and fluently.
Only return the translated text, with no additional comments, explanations, or formatting."""
                
                payload = {
                    "model": self.model_name,
                    "prompt": text,
                    "system": system_prompt,
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            self.logger.error(f"Ollama API error: {response.status}, {error_text}")
                            return text
                        
                        result = await response.json()
                        return result.get("response", text)
            
            except Exception as e:
                self.logger.error(f"Error translating with Ollama: {e}", exc_info=True)
                return text
    
    async def _translate_with_google(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Google Translate API
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            str: Translated text
        """
        if not self.api_key:
            self.logger.error("Google Translate API key not configured")
            return text
        
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            
            params = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Google Translate API error: {response.status}, {error_text}")
                        return text
                    
                    result = await response.json()
                    translations = result.get("data", {}).get("translations", [])
                    
                    if translations:
                        return translations[0].get("translatedText", text)
                    else:
                        return text
        
        except Exception as e:
            self.logger.error(f"Error translating with Google: {e}", exc_info=True)
            return text
