#!/usr/bin/env python3
"""
Multi-Source Consensus Analysis
This script analyzes intelligence from multiple sources to generate consensus reports
"""

import sqlite3
import logging
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path
import re
import spacy
from textblob import TextBlob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.consensus')

class ConsensusAnalyzer:
    """Multi-source intelligence consensus analysis tool"""
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """Initialize the analyzer with database connection"""
        self.db_path = db_path
        self.conn = None
        self.nlp = None
        
        if not os.path.exists(db_path):
            logger.error(f"Database not found at {db_path}")
            sys.exit(1)
            
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {db_path}")
            
            # Initialize spaCy for NLP tasks
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy NLP model")
            except:
                logger.warning("Could not load spaCy model. Run: python -m spacy download en_core_web_sm")
                
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_related_intelligence(self, topic: str, days: int = 30, min_similarity: float = 0.6) -> List[Dict]:
        """Get intelligence items related to a specific topic"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get recent intelligence items
        query = """
        SELECT * FROM intelligence_items 
        WHERE timestamp >= ? 
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (cutoff_str,))
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            
            # Filter by topic similarity if NLP is available
            if self.nlp and topic:
                topic_doc = self.nlp(topic)
                related_items = []
                
                for item in items:
                    # Create a combined text from title and content
                    combined_text = f"{item['title']} {item['content']}"
                    item_doc = self.nlp(combined_text)
                    
                    # Calculate similarity
                    similarity = topic_doc.similarity(item_doc)
                    
                    if similarity >= min_similarity:
                        item['topic_similarity'] = round(similarity, 3)
                        related_items.append(item)
                
                return related_items
            else:
                # Fallback to keyword matching
                topic_keywords = set(re.findall(r'\w+', topic.lower()))
                related_items = []
                
                for item in items:
                    combined_text = f"{item['title']} {item['content']}".lower()
                    item_keywords = set(re.findall(r'\w+', combined_text))
                    
                    # Calculate keyword overlap
                    if topic_keywords:
                        overlap = len(topic_keywords.intersection(item_keywords)) / len(topic_keywords)
                        
                        if overlap >= min_similarity:
                            item['topic_similarity'] = round(overlap, 3)
                            related_items.append(item)
                
                return related_items
                
        except Exception as e:
            logger.error(f"Error retrieving related intelligence: {e}")
            return []
    
    def get_intelligence_by_location(self, location: str, radius_km: float = 100) -> List[Dict]:
        """Get intelligence items for a specific location within radius"""
        query = """
        SELECT * FROM intelligence_items 
        WHERE location LIKE ? OR country LIKE ? OR region LIKE ?
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            pattern = f"%{location}%"
            cursor.execute(query, (pattern, pattern, pattern))
            location_items = [dict(row) for row in cursor.fetchall()]
            
            # Filter by geographic coordinates if available
            geo_items = []
            for item in location_items:
                if item.get('latitude') and item.get('longitude'):
                    geo_items.append(item)
            
            # If we have items with coordinates and geopy is available, filter by radius
            if geo_items:
                try:
                    from geopy.distance import geodesic
                    
                    # Get average coordinates for the location
                    avg_lat = sum(float(item['latitude']) for item in geo_items) / len(geo_items)
                    avg_lon = sum(float(item['longitude']) for item in geo_items) / len(geo_items)
                    center = (avg_lat, avg_lon)
                    
                    # Filter items by radius
                    radius_items = []
                    for item in location_items:
                        if item.get('latitude') and item.get('longitude'):
                            item_coords = (float(item['latitude']), float(item['longitude']))
                            distance = geodesic(center, item_coords).kilometers
                            
                            if distance <= radius_km:
                                item['distance_km'] = round(distance, 1)
                                radius_items.append(item)
                        else:
                            # Include items without coordinates but matching location text
                            radius_items.append(item)
                    
                    return radius_items
                except ImportError:
                    logger.warning("geopy not available for distance calculation")
                    return location_items
            else:
                return location_items
                
        except Exception as e:
            logger.error(f"Error retrieving intelligence for location {location}: {e}")
            return []
    
    def analyze_consensus(self, items: List[Dict]) -> Dict[str, Any]:
        """Analyze consensus among multiple intelligence items"""
        if not items:
            return {"error": "No intelligence items provided"}
        
        # Group items by source
        sources = defaultdict(list)
        for item in items:
            source = item.get('source', 'Unknown')
            sources[source].append(item)
        
        # Calculate source weights based on reliability and number of items
        source_weights = {}
        for source, source_items in sources.items():
            # Use average reliability if available, otherwise default to 0.5
            reliability = sum(item.get('reliability_score', 0.5) for item in source_items) / len(source_items)
            # Adjust weight by number of items (more items = more evidence)
            source_weights[source] = reliability * (1 + 0.1 * min(len(source_items), 10))
        
        # Normalize weights
        total_weight = sum(source_weights.values())
        if total_weight > 0:
            for source in source_weights:
                source_weights[source] /= total_weight
        
        # Extract key information from items
        regions = []
        countries = []
        locations = []
        threat_levels = []
        sentiments = []
        confidences = []
        keywords_list = []
        
        for item in items:
            if item.get('region'):
                regions.append(item['region'])
            if item.get('country'):
                countries.append(item['country'])
            if item.get('location'):
                locations.append(item['location'])
            if item.get('threat_level') is not None:
                threat_levels.append(float(item['threat_level']))
            if item.get('sentiment') is not None:
                sentiments.append(float(item['sentiment']))
            if item.get('confidence') is not None:
                confidences.append(float(item['confidence']))
            if item.get('keywords'):
                keywords_list.extend(item['keywords'].split(','))
        
        # Calculate consensus values
        consensus = {
            "source_count": len(sources),
            "item_count": len(items),
            "source_weights": source_weights,
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        # Most common region, country, location
        if regions:
            region_counts = pd.Series(regions).value_counts()
            consensus["region"] = region_counts.index[0]
            consensus["region_confidence"] = float(region_counts.iloc[0]) / len(regions)
        
        if countries:
            country_counts = pd.Series(countries).value_counts()
            consensus["country"] = country_counts.index[0]
            consensus["country_confidence"] = float(country_counts.iloc[0]) / len(countries)
        
        if locations:
            location_counts = pd.Series(locations).value_counts()
            consensus["location"] = location_counts.index[0]
            consensus["location_confidence"] = float(location_counts.iloc[0]) / len(locations)
        
        # Weighted average threat level
        if threat_levels:
            consensus["threat_level"] = round(sum(threat_levels) / len(threat_levels), 2)
            consensus["threat_level_std"] = round(np.std(threat_levels), 2)
        
        # Weighted average sentiment
        if sentiments:
            consensus["sentiment"] = round(sum(sentiments) / len(sentiments), 2)
            consensus["sentiment_std"] = round(np.std(sentiments), 2)
        
        # Weighted average confidence
        if confidences:
            consensus["confidence"] = round(sum(confidences) / len(confidences), 2)
            consensus["confidence_std"] = round(np.std(confidences), 2)
        
        # Most common keywords
        if keywords_list:
            # Clean and normalize keywords
            clean_keywords = [k.strip().lower() for k in keywords_list if k.strip()]
            if clean_keywords:
                keyword_counts = pd.Series(clean_keywords).value_counts()
                top_keywords = keyword_counts.head(10).index.tolist()
                consensus["keywords"] = top_keywords
        
        # Extract entities if NLP is available
        if self.nlp:
            all_text = " ".join([f"{item.get('title', '')} {item.get('content', '')}" for item in items])
            doc = self.nlp(all_text)
            
            # Extract named entities
            entities = defaultdict(list)
            for ent in doc.ents:
                entities[ent.label_].append(ent.text)
            
            # Count and sort entities
            for label, values in entities.items():
                if values:
                    counts = pd.Series(values).value_counts()
                    consensus[f"entities_{label}"] = counts.head(5).index.tolist()
        
        # Generate summary text
        summary_text = self._generate_summary(items, consensus)
        consensus["summary"] = summary_text
        
        return consensus
    
    def _generate_summary(self, items: List[Dict], consensus: Dict) -> str:
        """Generate a summary text from consensus analysis"""
        summary_parts = []
        
        # Location information
        location_parts = []
        if consensus.get('country'):
            location_parts.append(consensus['country'])
        if consensus.get('region'):
            location_parts.append(consensus['region'])
        
        if location_parts:
            location_str = " and ".join(location_parts)
            summary_parts.append(f"Multiple sources report intelligence from {location_str}.")
        
        # Threat assessment
        if consensus.get('threat_level') is not None:
            threat_level = consensus['threat_level']
            if threat_level >= 8:
                threat_desc = "critical"
            elif threat_level >= 6:
                threat_desc = "high"
            elif threat_level >= 4:
                threat_desc = "moderate"
            else:
                threat_desc = "low"
                
            summary_parts.append(f"The consensus threat level is {threat_desc} ({threat_level:.1f}/10).")
        
        # Source agreement
        if consensus.get('source_count', 0) > 1:
            item_count = consensus.get('item_count', 0)
            source_count = consensus.get('source_count', 0)
            summary_parts.append(f"This assessment is based on {item_count} intelligence items from {source_count} different sources.")
        
        # Keywords
        if consensus.get('keywords'):
            keywords = consensus['keywords'][:5]  # Top 5 keywords
            keyword_str = ", ".join(keywords)
            summary_parts.append(f"Key topics include: {keyword_str}.")
        
        # Join all parts
        summary = " ".join(summary_parts)
        return summary
    
    def generate_consensus_report(self, topic: str = None, location: str = None, 
                                 days: int = 30, output_file: str = None) -> Dict[str, Any]:
        """Generate a consensus report for a topic or location"""
        items = []
        
        if topic:
            topic_items = self.get_related_intelligence(topic, days)
            items.extend(topic_items)
            logger.info(f"Found {len(topic_items)} intelligence items related to topic: {topic}")
        
        if location:
            location_items = self.get_intelligence_by_location(location)
            # Avoid duplicates
            location_ids = set(item['id'] for item in location_items)
            existing_ids = set(item['id'] for item in items)
            unique_location_items = [item for item in location_items if item['id'] not in existing_ids]
            
            items.extend(unique_location_items)
            logger.info(f"Found {len(unique_location_items)} additional intelligence items for location: {location}")
        
        if not items:
            logger.warning("No intelligence items found for the specified criteria")
            return {"error": "No intelligence items found"}
        
        # Analyze consensus
        consensus = self.analyze_consensus(items)
        
        # Create report
        report = {
            "report_type": "Multi-Source Consensus Analysis",
            "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "query": {
                "topic": topic,
                "location": location,
                "days": days
            },
            "consensus": consensus,
            "source_items": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "source": item["source"],
                    "timestamp": item["timestamp"],
                    "threat_level": item["threat_level"],
                    "similarity": item.get("topic_similarity")
                }
                for item in items[:20]  # Limit to top 20 items
            ]
        }
        
        # Write report to file if specified
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=4)
            logger.info(f"Consensus report saved to {output_file}")
        
        return report

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Watchkeeper Multi-Source Consensus Analyzer')
    parser.add_argument('--db', default='data/intelligence.db', help='Path to intelligence database')
    parser.add_argument('--topic', help='Topic to analyze')
    parser.add_argument('--location', help='Location to analyze')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back')
    parser.add_argument('--output', default='reports/consensus_report.json', 
                      help='Output file for consensus report')
    args = parser.parse_args()
    
    if not args.topic and not args.location:
        print("Error: Either --topic or --location must be specified")
        sys.exit(1)
    
    analyzer = ConsensusAnalyzer(args.db)
    
    try:
        report = analyzer.generate_consensus_report(
            topic=args.topic,
            location=args.location,
            days=args.days,
            output_file=args.output
        )
        
        if "error" in report:
            print(f"Error: {report['error']}")
        else:
            print("\nConsensus Analysis Report:")
            print(f"Based on {report['consensus']['item_count']} intelligence items from {report['consensus']['source_count']} sources")
            
            if 'summary' in report['consensus']:
                print("\nSummary:")
                print(report['consensus']['summary'])
            
            if 'threat_level' in report['consensus']:
                print(f"\nThreat Level: {report['consensus']['threat_level']:.1f}/10")
            
            if 'keywords' in report['consensus']:
                print("\nKey Topics:")
                print(", ".join(report['consensus']['keywords']))
            
            print(f"\nDetailed report saved to {args.output}")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
