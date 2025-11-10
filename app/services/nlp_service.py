"""Multi-Language NLP Service

Provides language detection, translation, and NLP analysis for multiple languages.
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class NLPService:
    """Multi-language natural language processing"""

    def __init__(self):
        self.supported_languages = [
            'en', 'es', 'fr', 'de', 'ar', 'zh', 'ru', 'hi', 'pt', 'ja'
        ]

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text"""
        try:
            from langdetect import detect, detect_langs

            detected_lang = detect(text)
            confidence_scores = detect_langs(text)

            return {
                'language': detected_lang,
                'confidence': confidence_scores[0].prob if confidence_scores else 0.0,
                'alternatives': [
                    {'language': lang.lang, 'confidence': lang.prob}
                    for lang in confidence_scores[:3]
                ]
            }

        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }

    def translate_to_english(
        self,
        text: str,
        source_lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to English"""
        try:
            # Detect language if not provided
            if not source_lang:
                detection = self.detect_language(text)
                source_lang = detection['language']

            # Skip if already English
            if source_lang == 'en':
                return {
                    'original_text': text,
                    'translated_text': text,
                    'source_language': 'en',
                    'target_language': 'en',
                    'translation_needed': False
                }

            # Translate using googletrans
            try:
                from googletrans import Translator

                translator = Translator()
                translation = translator.translate(text, src=source_lang, dest='en')

                return {
                    'original_text': text,
                    'translated_text': translation.text,
                    'source_language': source_lang,
                    'target_language': 'en',
                    'translation_needed': True,
                    'confidence': 0.8  # Simplified confidence
                }

            except Exception as trans_error:
                logger.error(f"Translation error: {trans_error}")
                return {
                    'original_text': text,
                    'translated_text': text,
                    'source_language': source_lang,
                    'error': str(trans_error),
                    'translation_needed': True,
                    'translation_failed': True
                }

        except Exception as e:
            logger.error(f"Translation service error: {e}")
            return {
                'error': str(e),
                'original_text': text
            }

    def extract_entities(
        self,
        text: str,
        lang: str = 'en'
    ) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        # Simplified entity extraction
        # In production, use spaCy or transformers with multilingual models

        entities = {
            'locations': [],
            'organizations': [],
            'persons': [],
            'dates': []
        }

        # Simple keyword-based extraction for demo
        location_keywords = [
            'city', 'country', 'region', 'province', 'state',
            'afghanistan', 'pakistan', 'syria', 'iraq', 'yemen'
        ]

        org_keywords = [
            'government', 'military', 'police', 'ministry',
            'un', 'nato', 'embassy'
        ]

        text_lower = text.lower()

        # Extract potential locations
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,;:')

            if word_lower in location_keywords:
                # Capture word before location keyword if capitalized
                if i > 0 and words[i-1][0].isupper():
                    entities['locations'].append(words[i-1] + ' ' + word)
                else:
                    entities['locations'].append(word)

            if word_lower in org_keywords:
                entities['organizations'].append(word)

        # Remove duplicates
        entities['locations'] = list(set(entities['locations']))
        entities['organizations'] = list(set(entities['organizations']))

        return entities

    def analyze_sentiment(
        self,
        text: str,
        lang: str = 'en'
    ) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            # Translate to English if needed
            if lang != 'en':
                translation = self.translate_to_english(text, lang)
                text = translation.get('translated_text', text)

            # Use TextBlob for sentiment analysis
            from textblob import TextBlob

            blob = TextBlob(text)
            sentiment = blob.sentiment

            # Categorize sentiment
            polarity = sentiment.polarity

            if polarity > 0.1:
                category = 'positive'
            elif polarity < -0.1:
                category = 'negative'
            else:
                category = 'neutral'

            return {
                'polarity': polarity,
                'subjectivity': sentiment.subjectivity,
                'category': category,
                'language': lang
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'category': 'neutral',
                'error': str(e)
            }

    def process_intelligence_item(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """Complete NLP processing for an intelligence item"""

        text = f"{title} {content}"

        # Detect language
        lang_detection = self.detect_language(text)
        detected_lang = lang_detection['language']

        # Translate if needed
        if detected_lang != 'en':
            translation = self.translate_to_english(text, detected_lang)
            english_text = translation.get('translated_text', text)
        else:
            english_text = text
            translation = None

        # Extract entities from English text
        entities = self.extract_entities(english_text, 'en')

        # Analyze sentiment
        sentiment = self.analyze_sentiment(english_text, 'en')

        # Extract keywords
        keywords = self._extract_keywords(english_text)

        return {
            'detected_language': detected_lang,
            'language_confidence': lang_detection.get('confidence', 0.0),
            'translation': translation,
            'english_text': english_text,
            'entities': entities,
            'sentiment': sentiment,
            'keywords': keywords,
            'multilingual': detected_lang != 'en'
        }

    def _extract_keywords(
        self,
        text: str,
        top_n: int = 10
    ) -> List[str]:
        """Extract important keywords from text"""
        # Simplified keyword extraction
        # In production, use TF-IDF or BERT-based methods

        from collections import Counter
        import re

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
            'are', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'it', 'its'
        }

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter stop words and count
        filtered = [w for w in words if w not in stop_words]
        word_counts = Counter(filtered)

        # Get top N keywords
        keywords = [word for word, count in word_counts.most_common(top_n)]

        return keywords

    def get_cultural_context(
        self,
        text: str,
        detected_lang: str,
        entities: Dict
    ) -> Dict[str, Any]:
        """Add cultural context to intelligence"""
        # This would integrate with cultural databases
        # Simplified implementation

        context = {
            'language_region': self._get_language_region(detected_lang),
            'cultural_notes': [],
            'regional_context': []
        }

        # Add context based on detected locations
        for location in entities.get('locations', []):
            if 'afghanistan' in location.lower():
                context['cultural_notes'].append('Region with significant missionary activity restrictions')
            elif 'pakistan' in location.lower():
                context['cultural_notes'].append('Exercise heightened security awareness')

        return context

    def _get_language_region(self, lang_code: str) -> str:
        """Map language code to region"""
        lang_regions = {
            'ar': 'Middle East / North Africa',
            'zh': 'East Asia',
            'es': 'Latin America / Spain',
            'fr': 'Africa / Europe',
            'hi': 'South Asia',
            'ru': 'Eastern Europe / Central Asia',
            'pt': 'Brazil / Africa',
            'de': 'Central Europe',
            'ja': 'East Asia'
        }

        return lang_regions.get(lang_code, 'Unknown')


# Singleton instance
_nlp_service = None


def get_nlp_service() -> NLPService:
    """Get singleton NLP service instance"""
    global _nlp_service

    if _nlp_service is None:
        _nlp_service = NLPService()

    return _nlp_service


from typing import Any
