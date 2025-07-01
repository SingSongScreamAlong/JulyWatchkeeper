"""
Severity Processor for WATCHKEEPER

This module implements severity scoring for intelligence items.
"""

import re
from typing import Dict, Any, List, Optional, Set, Tuple

from src.processors.base_processor import BaseProcessor
from src.utils.logger import get_logger
from src.utils.config import get_config

class SeverityProcessor(BaseProcessor):
    """
    Severity processor for intelligence items
    
    This processor assesses the severity of intelligence items using:
    1. Keyword-based scoring
    2. Threat level assessment
    3. AI analysis integration
    """
    
    def __init__(self):
        """Initialize the severity processor"""
        super().__init__("severity_processor")
        self.config = get_config().get("processors", {}).get("severity", {})
        
        # Load keyword dictionaries with severity weights
        self.keywords = self._load_keywords()
        
        # Threat level mapping to numeric scores
        self.threat_level_scores = {
            "None": 0,
            "Low": 2,
            "Medium": 5,
            "High": 8,
            "Critical": 10
        }
        
        # Severity score ranges and labels
        self.severity_ranges = [
            (0, 2, "Minimal"),
            (3, 4, "Low"),
            (5, 6, "Moderate"),
            (7, 8, "High"),
            (9, 10, "Critical")
        ]
    
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item to assess severity
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with severity assessment
        """
        if not item.get("content"):
            self.logger.warning("Item has no content to process")
            return item
        
        # Create a copy of the item to avoid modifying the original
        processed_item = item.copy()
        
        # Add severity_assessment section if it doesn't exist
        if "severity_assessment" not in processed_item:
            processed_item["severity_assessment"] = {}
        
        try:
            # Get content and title
            content = item.get("content", "")
            title = item.get("title", "")
            
            # Combine title and content for analysis
            text = f"{title}\n\n{content}"
            
            # Calculate keyword-based score
            keyword_score, matched_keywords = self._calculate_keyword_score(text)
            
            # Get threat level score from AI analysis if available
            threat_score = self._get_threat_level_score(item)
            
            # Calculate final severity score (weighted average)
            # 60% keyword score, 40% threat score if available, otherwise 100% keyword score
            if threat_score is not None:
                final_score = (keyword_score * 0.6) + (threat_score * 0.4)
            else:
                final_score = keyword_score
            
            # Round to nearest integer and clamp between 0-10
            final_score = max(0, min(10, round(final_score)))
            
            # Get severity label based on score
            severity_label = self._get_severity_label(final_score)
            
            # Update severity assessment
            processed_item["severity_assessment"] = {
                "score": final_score,
                "label": severity_label,
                "keyword_score": keyword_score,
                "threat_score": threat_score,
                "matched_keywords": matched_keywords
            }
            
            self.logger.debug(f"Assessed severity: {severity_label} ({final_score}/10)")
            
        except Exception as e:
            self.logger.error(f"Error in severity processing: {e}", exc_info=True)
        
        return processed_item
    
    def _load_keywords(self) -> Dict[str, Dict[str, float]]:
        """
        Load keyword dictionaries with severity weights
        
        Returns:
            Dict[str, Dict[str, float]]: Keyword dictionaries by category
        """
        # Default keywords if not configured
        default_keywords = {
            "violence": {
                "attack": 0.8,
                "bomb": 0.9,
                "explosion": 0.9,
                "gunfire": 0.8,
                "shooting": 0.8,
                "killed": 0.7,
                "wounded": 0.6,
                "casualties": 0.7,
                "terrorist": 0.9,
                "hostage": 0.9,
                "violence": 0.7,
                "riot": 0.7,
                "armed": 0.6
            },
            "disaster": {
                "earthquake": 0.8,
                "tsunami": 0.9,
                "hurricane": 0.8,
                "typhoon": 0.8,
                "flood": 0.7,
                "wildfire": 0.7,
                "landslide": 0.7,
                "volcano": 0.8,
                "evacuation": 0.6,
                "disaster": 0.7,
                "emergency": 0.6
            },
            "health": {
                "outbreak": 0.7,
                "epidemic": 0.8,
                "pandemic": 0.9,
                "virus": 0.6,
                "disease": 0.6,
                "infection": 0.6,
                "quarantine": 0.7,
                "contaminated": 0.7,
                "vaccine": 0.5,
                "hospital": 0.5
            },
            "political": {
                "coup": 0.8,
                "overthrow": 0.7,
                "revolution": 0.7,
                "protest": 0.5,
                "demonstration": 0.4,
                "unrest": 0.6,
                "conflict": 0.6,
                "tension": 0.5,
                "martial law": 0.8,
                "curfew": 0.7,
                "banned": 0.6,
                "arrested": 0.6
            },
            "travel": {
                "warning": 0.6,
                "advisory": 0.5,
                "avoid": 0.6,
                "restricted": 0.7,
                "closed": 0.6,
                "evacuate": 0.8,
                "stranded": 0.7,
                "unsafe": 0.7
            },
            "religious": {
                "persecution": 0.9,
                "extremist": 0.8,
                "radical": 0.7,
                "targeted": 0.7,
                "banned": 0.8,
                "arrested": 0.7,
                "detained": 0.7,
                "missionary": 0.6,
                "christian": 0.5,
                "church": 0.5
            }
        }
        
        # Load from config if available
        configured_keywords = self.config.get("keywords", {})
        
        # Merge default with configured keywords
        keywords = default_keywords.copy()
        for category, words in configured_keywords.items():
            if category in keywords:
                keywords[category].update(words)
            else:
                keywords[category] = words
        
        return keywords
    
    def _calculate_keyword_score(self, text: str) -> Tuple[float, Dict[str, List[str]]]:
        """
        Calculate severity score based on keyword matching
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple[float, Dict[str, List[str]]]: Score and matched keywords by category
        """
        text = text.lower()
        total_score = 0
        total_weight = 0
        matched_keywords = {}
        
        # Check each category
        for category, keywords in self.keywords.items():
            category_matches = []
            category_score = 0
            category_weight = 0
            
            # Check each keyword
            for keyword, weight in keywords.items():
                # Count occurrences
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                
                if count > 0:
                    # Add to matched keywords
                    category_matches.append(keyword)
                    
                    # Calculate score contribution
                    # Score increases with multiple occurrences but with diminishing returns
                    score_contribution = weight * min(count, 3) * (1.0 / 3.0)
                    category_score += score_contribution
                    category_weight += weight
            
            # Add category matches to results
            if category_matches:
                matched_keywords[category] = category_matches
                total_score += category_score
                total_weight += category_weight
        
        # Calculate final score (0-10 scale)
        if total_weight > 0:
            # Normalize to 0-10 scale
            normalized_score = (total_score / total_weight) * 10
            # Apply sigmoid-like scaling to emphasize mid-range values
            final_score = 10 * (1 / (1 + 2.71828 ** (-normalized_score + 5))) 
        else:
            final_score = 0
        
        return final_score, matched_keywords
    
    def _get_threat_level_score(self, item: Dict[str, Any]) -> Optional[float]:
        """
        Get threat level score from AI analysis
        
        Args:
            item: Intelligence item
            
        Returns:
            Optional[float]: Threat level score (0-10) or None if not available
        """
        # Check if AI analysis is available
        if "ai_analysis" not in item or "threat" not in item["ai_analysis"]:
            return None
        
        # Get threat level
        threat = item["ai_analysis"]["threat"]
        level = threat.get("level", "None")
        confidence = threat.get("confidence", 0.5)
        
        # Get score for this level
        score = self.threat_level_scores.get(level, 0)
        
        # Adjust score based on confidence
        adjusted_score = score * confidence
        
        return adjusted_score
    
    def _get_severity_label(self, score: int) -> str:
        """
        Get severity label based on score
        
        Args:
            score: Severity score (0-10)
            
        Returns:
            str: Severity label
        """
        for min_score, max_score, label in self.severity_ranges:
            if min_score <= score <= max_score:
                return label
        
        return "Unknown"
