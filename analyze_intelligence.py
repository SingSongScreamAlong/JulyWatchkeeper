#!/usr/bin/env python3
"""
Intelligence Analysis Utility
This script analyzes collected intelligence data and generates reports
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
import matplotlib.pyplot as plt
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.analyze')

class IntelligenceAnalyzer:
    """Intelligence data analysis and reporting tool"""
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """Initialize the analyzer with database connection"""
        self.db_path = db_path
        self.conn = None
        
        if not os.path.exists(db_path):
            logger.error(f"Database not found at {db_path}")
            sys.exit(1)
            
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {db_path}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_recent_intelligence(self, days: int = 7) -> List[Dict]:
        """Get intelligence items from the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query = """
        SELECT * FROM intelligence_items 
        WHERE timestamp >= ? 
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (cutoff_str,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving recent intelligence: {e}")
            return []
    
    def get_high_threat_intelligence(self, threshold: float = 7.0) -> List[Dict]:
        """Get high threat intelligence items"""
        query = """
        SELECT * FROM intelligence_items 
        WHERE threat_level >= ? 
        ORDER BY threat_level DESC, timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (threshold,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving high threat intelligence: {e}")
            return []
    
    def get_intelligence_by_region(self, region: str) -> List[Dict]:
        """Get intelligence items for a specific region"""
        query = """
        SELECT * FROM intelligence_items 
        WHERE region = ? 
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (region,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving intelligence for region {region}: {e}")
            return []
    
    def get_intelligence_by_location(self, location: str) -> List[Dict]:
        """Get intelligence items for a specific location"""
        query = """
        SELECT * FROM intelligence_items 
        WHERE location LIKE ? 
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (f"%{location}%",))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving intelligence for location {location}: {e}")
            return []
    
    def get_intelligence_stats(self) -> Dict[str, Any]:
        """Get statistics about collected intelligence"""
        stats = {}
        
        try:
            cursor = self.conn.cursor()
            
            # Total items
            cursor.execute("SELECT COUNT(*) FROM intelligence_items")
            stats['total_items'] = cursor.fetchone()[0]
            
            # Items by region
            cursor.execute("""
                SELECT region, COUNT(*) as count 
                FROM intelligence_items 
                GROUP BY region 
                ORDER BY count DESC
            """)
            stats['items_by_region'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average threat level
            cursor.execute("SELECT AVG(threat_level) FROM intelligence_items")
            stats['avg_threat_level'] = round(cursor.fetchone()[0], 2)
            
            # High threat items (>= 7.0)
            cursor.execute("SELECT COUNT(*) FROM intelligence_items WHERE threat_level >= 7.0")
            stats['high_threat_count'] = cursor.fetchone()[0]
            
            # Items by source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM intelligence_items 
                GROUP BY source 
                ORDER BY count DESC
            """)
            stats['items_by_source'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average sentiment (if available)
            cursor.execute("SELECT AVG(sentiment) FROM intelligence_items WHERE sentiment IS NOT NULL")
            result = cursor.fetchone()[0]
            stats['avg_sentiment'] = round(result, 2) if result is not None else None
            
            # Average confidence (if available)
            cursor.execute("SELECT AVG(confidence) FROM intelligence_items WHERE confidence IS NOT NULL")
            result = cursor.fetchone()[0]
            stats['avg_confidence'] = round(result, 2) if result is not None else None
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving intelligence statistics: {e}")
            return {}
    
    def generate_threat_map(self, output_file: str = 'reports/threat_map.html'):
        """Generate an interactive threat map using folium"""
        try:
            import folium
            from folium.plugins import HeatMap
            
            # Get intelligence items with coordinates
            query = """
            SELECT title, location, latitude, longitude, threat_level 
            FROM intelligence_items 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
            
            cursor = self.conn.cursor()
            cursor.execute(query)
            items = [dict(row) for row in cursor.fetchall()]
            
            if not items:
                logger.warning("No geo-located intelligence items found")
                return False
            
            # Create map centered on average coordinates
            avg_lat = sum(float(item['latitude']) for item in items) / len(items)
            avg_lon = sum(float(item['longitude']) for item in items) / len(items)
            
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=3)
            
            # Add markers for each item
            for item in items:
                threat_level = float(item['threat_level'])
                color = 'green' if threat_level < 5 else 'orange' if threat_level < 7 else 'red'
                
                folium.Marker(
                    location=[float(item['latitude']), float(item['longitude'])],
                    popup=f"{item['title']} (Threat: {threat_level})",
                    tooltip=item['location'],
                    icon=folium.Icon(color=color)
                ).add_to(m)
            
            # Add heat map layer
            heat_data = [[float(item['latitude']), float(item['longitude']), float(item['threat_level'])] 
                         for item in items]
            HeatMap(heat_data).add_to(m)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save map
            m.save(output_file)
            logger.info(f"Threat map saved to {output_file}")
            return True
            
        except ImportError:
            logger.error("folium package not installed. Install with: pip install folium")
            return False
        except Exception as e:
            logger.error(f"Error generating threat map: {e}")
            return False
    
    def generate_report(self, report_type: str, output_file: str = None) -> bool:
        """Generate intelligence report of specified type"""
        if report_type == 'summary':
            return self._generate_summary_report(output_file)
        elif report_type == 'threat':
            return self._generate_threat_report(output_file)
        elif report_type == 'regional':
            return self._generate_regional_report(output_file)
        else:
            logger.error(f"Unknown report type: {report_type}")
            return False
    
    def _generate_summary_report(self, output_file: str = None) -> bool:
        """Generate summary intelligence report"""
        try:
            stats = self.get_intelligence_stats()
            recent_items = self.get_recent_intelligence(7)
            high_threat_items = self.get_high_threat_intelligence(7.0)
            
            # Create report content
            report = {
                "report_type": "Intelligence Summary",
                "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "statistics": stats,
                "high_threat_items": high_threat_items[:10],  # Top 10
                "recent_items": recent_items[:10]  # Top 10
            }
            
            # Write report to file if specified
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=4)
                logger.info(f"Summary report saved to {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return False
    
    def _generate_threat_report(self, output_file: str = None) -> bool:
        """Generate threat intelligence report"""
        try:
            high_threat_items = self.get_high_threat_intelligence(7.0)
            
            # Group by region
            items_by_region = {}
            for item in high_threat_items:
                region = item['region']
                if region not in items_by_region:
                    items_by_region[region] = []
                items_by_region[region].append(item)
            
            # Create report content
            report = {
                "report_type": "Threat Intelligence Report",
                "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "total_high_threat_items": len(high_threat_items),
                "items_by_region": {
                    region: [
                        {
                            "title": item["title"],
                            "threat_level": item["threat_level"],
                            "missionary_relevance": item["missionary_relevance"],
                            "timestamp": item["timestamp"],
                            "location": item.get("location"),
                            "source": item["source"]
                        }
                        for item in items
                    ]
                    for region, items in items_by_region.items()
                }
            }
            
            # Write report to file if specified
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=4)
                logger.info(f"Threat report saved to {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating threat report: {e}")
            return False
    
    def _generate_regional_report(self, output_file: str = None) -> bool:
        """Generate regional intelligence report"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT region FROM intelligence_items")
            regions = [row[0] for row in cursor.fetchall()]
            
            # Get items for each region
            regional_data = {}
            for region in regions:
                items = self.get_intelligence_by_region(region)
                if items:
                    regional_data[region] = {
                        "item_count": len(items),
                        "avg_threat_level": sum(item["threat_level"] for item in items) / len(items),
                        "high_threat_count": sum(1 for item in items if item["threat_level"] >= 7.0),
                        "recent_items": [
                            {
                                "title": item["title"],
                                "threat_level": item["threat_level"],
                                "timestamp": item["timestamp"],
                                "country": item["country"],
                                "location": item.get("location")
                            }
                            for item in sorted(items, key=lambda x: x["timestamp"], reverse=True)[:5]
                        ]
                    }
            
            # Create report content
            report = {
                "report_type": "Regional Intelligence Report",
                "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "regions": regional_data
            }
            
            # Write report to file if specified
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=4)
                logger.info(f"Regional report saved to {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating regional report: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Watchkeeper Intelligence Analyzer')
    parser.add_argument('--db', default='data/intelligence.db', help='Path to intelligence database')
    parser.add_argument('--report', choices=['summary', 'threat', 'regional'], default='summary',
                      help='Type of report to generate')
    parser.add_argument('--output', help='Output file for report (JSON format)')
    parser.add_argument('--map', action='store_true', help='Generate threat map')
    parser.add_argument('--map-output', default='reports/threat_map.html', 
                      help='Output file for threat map (HTML format)')
    args = parser.parse_args()
    
    analyzer = IntelligenceAnalyzer(args.db)
    
    try:
        if args.report:
            success = analyzer.generate_report(args.report, args.output)
            if success:
                print(f"Successfully generated {args.report} report")
            else:
                print(f"Failed to generate {args.report} report")
        
        if args.map:
            success = analyzer.generate_threat_map(args.map_output)
            if success:
                print(f"Successfully generated threat map at {args.map_output}")
            else:
                print("Failed to generate threat map")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
