"""
Relevance Processor for WATCHKEEPER

This module implements missionary relevance assessment for intelligence items.
"""

import re
from typing import Dict, Any, List, Optional, Set, Tuple

from src.processors.base_processor import BaseProcessor
from src.utils.logger import get_logger
from src.utils.config import get_config

class RelevanceProcessor(BaseProcessor):
    """
    Relevance processor for intelligence items
    
    This processor assesses the relevance of intelligence items to missionary operations using:
    1. Keyword-based relevance scoring
    2. Location-based relevance assessment
    3. Integration with AI analysis
    """
    
    def __init__(self):
        """Initialize the relevance processor"""
        super().__init__("relevance_processor")
        self.config = get_config().get("processors", {}).get("relevance", {})
        
        # Load keyword dictionaries with relevance weights
        self.keywords = self._load_keywords()
        
        # Load mission field locations with weights
        self.mission_locations = self._load_mission_locations()
        
        # Relevance score ranges and labels
        self.relevance_ranges = [
            (0, 2, "Not Relevant"),
            (3, 4, "Low Relevance"),
            (5, 6, "Moderately Relevant"),
            (7, 8, "Highly Relevant"),
            (9, 10, "Critical Relevance")
        ]
    
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item to assess missionary relevance
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with relevance assessment
        """
        if not item.get("content"):
            self.logger.warning("Item has no content to process")
            return item
        
        # Create a copy of the item to avoid modifying the original
        processed_item = item.copy()
        
        # Add relevance_assessment section if it doesn't exist
        if "relevance_assessment" not in processed_item:
            processed_item["relevance_assessment"] = {}
        
        try:
            # Get content and title
            content = item.get("content", "")
            title = item.get("title", "")
            
            # Combine title and content for analysis
            text = f"{title}\n\n{content}"
            
            # Calculate keyword-based relevance
            keyword_score, matched_keywords = self._calculate_keyword_relevance(text)
            
            # Calculate location-based relevance
            location_score, relevant_locations = self._calculate_location_relevance(item)
            
            # Get missionary impact from AI analysis if available
            impact_score = self._get_impact_score(item)
            
            # Calculate final relevance score (weighted average)
            # 40% keyword score, 40% location score, 20% impact score if available
            if impact_score is not None:
                final_score = (keyword_score * 0.4) + (location_score * 0.4) + (impact_score * 0.2)
            else:
                # 50% keyword score, 50% location score if no impact score
                final_score = (keyword_score * 0.5) + (location_score * 0.5)
            
            # Round to nearest integer and clamp between 0-10
            final_score = max(0, min(10, round(final_score)))
            
            # Get relevance label based on score
            relevance_label = self._get_relevance_label(final_score)
            
            # Update relevance assessment
            processed_item["relevance_assessment"] = {
                "score": final_score,
                "label": relevance_label,
                "keyword_score": keyword_score,
                "location_score": location_score,
                "impact_score": impact_score,
                "matched_keywords": matched_keywords,
                "relevant_locations": relevant_locations
            }
            
            self.logger.debug(f"Assessed missionary relevance: {relevance_label} ({final_score}/10)")
            
        except Exception as e:
            self.logger.error(f"Error in relevance processing: {e}", exc_info=True)
        
        return processed_item
    
    def _load_keywords(self) -> Dict[str, Dict[str, float]]:
        """
        Load keyword dictionaries with relevance weights
        
        Returns:
            Dict[str, Dict[str, float]]: Keyword dictionaries by category
        """
        # Default keywords if not configured
        default_keywords = {
            "missionary": {
                "missionary": 1.0,
                "mission": 0.9,
                "evangelist": 0.9,
                "evangelism": 0.9,
                "church": 0.8,
                "christian": 0.8,
                "christianity": 0.8,
                "bible": 0.8,
                "gospel": 0.8,
                "pastor": 0.8,
                "ministry": 0.8,
                "prayer": 0.7,
                "worship": 0.7,
                "faith": 0.7,
                "religious": 0.7,
                "religion": 0.6
            },
            "persecution": {
                "persecution": 1.0,
                "persecuted": 0.9,
                "arrested": 0.8,
                "detained": 0.8,
                "imprisoned": 0.8,
                "banned": 0.8,
                "restricted": 0.7,
                "prohibited": 0.7,
                "illegal": 0.7,
                "censored": 0.7,
                "monitored": 0.6,
                "surveillance": 0.6
            },
            "security": {
                "kidnapping": 0.9,
                "abduction": 0.9,
                "hostage": 0.9,
                "violence": 0.8,
                "attack": 0.8,
                "targeted": 0.8,
                "threat": 0.7,
                "warning": 0.7,
                "danger": 0.7,
                "unsafe": 0.7,
                "evacuation": 0.7,
                "evacuate": 0.7
            },
            "travel": {
                "visa": 0.8,
                "passport": 0.8,
                "border": 0.7,
                "entry": 0.7,
                "exit": 0.7,
                "customs": 0.7,
                "immigration": 0.7,
                "travel": 0.6,
                "restricted": 0.6,
                "closed": 0.6,
                "reopened": 0.6,
                "flight": 0.5,
                "airport": 0.5
            },
            "humanitarian": {
                "aid": 0.8,
                "relief": 0.8,
                "humanitarian": 0.8,
                "charity": 0.7,
                "donation": 0.7,
                "volunteer": 0.7,
                "clinic": 0.7,
                "hospital": 0.6,
                "medicine": 0.6,
                "medical": 0.6,
                "education": 0.6,
                "school": 0.6,
                "orphanage": 0.7,
                "refugee": 0.7
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
    
    def _load_mission_locations(self) -> Dict[str, float]:
        """
        Load mission field locations with relevance weights
        
        Returns:
            Dict[str, float]: Location names with relevance weights
        """
        # Default mission locations if not configured
        default_locations = {
            # High priority mission fields
            "Afghanistan": 0.9,
            "North Korea": 0.9,
            "Iran": 0.9,
            "Somalia": 0.9,
            "Yemen": 0.9,
            "Pakistan": 0.8,
            "Eritrea": 0.8,
            "Nigeria": 0.8,
            "Sudan": 0.8,
            "Libya": 0.8,
            "Iraq": 0.8,
            "Syria": 0.8,
            
            # Medium priority mission fields
            "China": 0.7,
            "Saudi Arabia": 0.7,
            "Myanmar": 0.7,
            "Vietnam": 0.7,
            "India": 0.7,
            "Turkmenistan": 0.7,
            "Egypt": 0.7,
            "Turkey": 0.7,
            "Colombia": 0.7,
            "Ethiopia": 0.7,
            "Kenya": 0.7,
            "Tanzania": 0.7,
            
            # Regular mission fields
            "Indonesia": 0.6,
            "Russia": 0.6,
            "Mexico": 0.6,
            "Brazil": 0.6,
            "Philippines": 0.6,
            "Thailand": 0.6,
            "Ukraine": 0.6,
            "South Africa": 0.6,
            "Peru": 0.6,
            "Haiti": 0.6
        }
        
        # Load from config if available
        configured_locations = self.config.get("mission_locations", {})
        
        # Merge default with configured locations
        locations = default_locations.copy()
        locations.update(configured_locations)
        
        return locations
    
    def _calculate_keyword_relevance(self, text: str) -> Tuple[float, Dict[str, List[str]]]:
        """
        Calculate relevance score based on keyword matching
        
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
    
    def _calculate_location_relevance(self, item: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculate relevance score based on locations mentioned
        
        Args:
            item: Intelligence item
            
        Returns:
            Tuple[float, List[Dict[str, Any]]]: Score and relevant locations
        """
        relevant_locations = []
        max_relevance = 0
        
        # Check locations from geo_data if available
        if "geo_data" in item and "locations" in item["geo_data"]:
            for location in item["geo_data"]["locations"]:
                location_name = location.get("name", "")
                
                # Check if this is a mission location
                for mission_loc, weight in self.mission_locations.items():
                    if mission_loc.lower() in location_name.lower():
                        # Add to relevant locations
                        relevant_locations.append({
                            "name": location_name,
                            "mission_location": mission_loc,
                            "relevance": weight
                        })
                        
                        # Update max relevance
                        max_relevance = max(max_relevance, weight)
        
        # Check locations from AI analysis if available
        if "ai_analysis" in item and "locations" in item["ai_analysis"]:
            for location in item["ai_analysis"]["locations"]:
                location_name = location.get("name", "")
                
                # Check if this is a mission location
                for mission_loc, weight in self.mission_locations.items():
                    if mission_loc.lower() in location_name.lower():
                        # Check if already added
                        already_added = False
                        for rel_loc in relevant_locations:
                            if rel_loc["mission_location"] == mission_loc:
                                already_added = True
                                break
                        
                        if not already_added:
                            # Add to relevant locations
                            relevant_locations.append({
                                "name": location_name,
                                "mission_location": mission_loc,
                                "relevance": weight
                            })
                            
                            # Update max relevance
                            max_relevance = max(max_relevance, weight)
        
        # Calculate final score (0-10 scale)
        # Use the maximum relevance of any location, scaled to 0-10
        location_score = max_relevance * 10
        
        return location_score, relevant_locations
    
    def _get_impact_score(self, item: Dict[str, Any]) -> Optional[float]:
        """
        Get missionary impact score from AI analysis
        
        Args:
            item: Intelligence item
            
        Returns:
            Optional[float]: Impact score (0-10) or None if not available
        """
        # Check if AI analysis is available
        if "ai_analysis" not in item or "missionary_impact" not in item["ai_analysis"]:
            return None
        
        # Get impact assessment
        impact = item["ai_analysis"]["missionary_impact"]
        severity = impact.get("severity", "None")
        
        # Map severity to score
        severity_scores = {
            "None": 0,
            "Low": 2,
            "Medium": 5,
            "High": 8,
            "Critical": 10
        }
        
        # Get score for this severity
        score = severity_scores.get(severity, 0)
        
        return score
    
    def _get_relevance_label(self, score: int) -> str:
        """
        Get relevance label based on score
        
        Args:
            score: Relevance score (0-10)
            
        Returns:
            str: Relevance label
        """
        for min_score, max_score, label in self.relevance_ranges:
            if min_score <= score <= max_score:
                return label
        
        return "Unknown"
