#!/usr/bin/env python3
"""
WATCHKEEPER Briefing Generator
Generates comprehensive intelligence briefings from collected data
"""

import sqlite3
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

class BriefingGenerator:
    """Generates formatted intelligence briefings"""

    def __init__(self, db_path: str = 'data/intelligence.db'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_intelligence_for_period(self, days: int = 1) -> List[Dict]:
        """Get intelligence items from the last N days"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')

        query = """
        SELECT * FROM intelligence_items
        WHERE collection_date >= ?
        ORDER BY threat_level DESC, collection_date DESC
        """

        cursor = self.conn.cursor()
        cursor.execute(query, (cutoff_date,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self, items: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics from intelligence items"""
        if not items:
            return {
                'total_items': 0,
                'avg_threat': 0.0,
                'high_threat_count': 0,
                'regions': [],
                'max_threat': 0.0,
                'min_threat': 0.0
            }

        threat_levels = [item['threat_level'] for item in items]
        regions = defaultdict(int)
        for item in items:
            if item['region']:
                regions[item['region']] += 1

        return {
            'total_items': len(items),
            'avg_threat': sum(threat_levels) / len(threat_levels),
            'high_threat_count': sum(1 for t in threat_levels if t >= 7.0),
            'regions': dict(regions),
            'max_threat': max(threat_levels),
            'min_threat': min(threat_levels),
            'avg_relevance': sum(item['missionary_relevance'] for item in items) / len(items)
        }

    def get_threat_assessment(self, avg_threat: float) -> str:
        """Get overall threat assessment"""
        if avg_threat >= 8.0:
            return "CRITICAL - Immediate action required"
        elif avg_threat >= 7.0:
            return "HIGH - Enhanced security measures recommended"
        elif avg_threat >= 5.0:
            return "MODERATE - Standard precautions advised"
        elif avg_threat >= 3.0:
            return "LOW - Normal operations with routine monitoring"
        else:
            return "MINIMAL - No significant threats detected"

    def get_alert_level(self, avg_threat: float) -> str:
        """Get alert level color code"""
        if avg_threat >= 8.0:
            return "BLACK"
        elif avg_threat >= 7.0:
            return "RED"
        elif avg_threat >= 5.0:
            return "ORANGE"
        elif avg_threat >= 3.0:
            return "YELLOW"
        else:
            return "GREEN"

    def generate_text_briefing(self, date: str = None, days: int = 1) -> str:
        """Generate a text-formatted intelligence briefing"""
        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%d')

        # Get intelligence data
        items = self.get_intelligence_for_period(days)
        stats = self.get_stats(items)

        # Build briefing
        briefing = []
        briefing.append("=" * 80)
        briefing.append("WATCHKEEPER INTELLIGENCE BRIEFING")
        briefing.append("=" * 80)
        briefing.append(f"Date: {date}")
        briefing.append(f"Coverage Period: Last {days} day(s)")
        briefing.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        briefing.append("=" * 80)
        briefing.append("")

        # Executive Summary
        briefing.append("EXECUTIVE SUMMARY")
        briefing.append("-" * 80)
        briefing.append(f"Total Intelligence Items: {stats['total_items']}")
        briefing.append(f"Average Threat Level: {stats['avg_threat']:.1f}/10")
        briefing.append(f"High Threat Items (≥7.0): {stats['high_threat_count']}")
        briefing.append(f"Overall Threat Assessment: {self.get_threat_assessment(stats['avg_threat'])}")
        briefing.append(f"Alert Level: {self.get_alert_level(stats['avg_threat'])}")
        briefing.append(f"Missionary Relevance: {stats['avg_relevance']:.1f}/10")
        briefing.append("")

        # Regional Breakdown
        if stats['regions']:
            briefing.append("REGIONAL DISTRIBUTION")
            briefing.append("-" * 80)
            for region, count in sorted(stats['regions'].items(), key=lambda x: x[1], reverse=True):
                briefing.append(f"  • {region}: {count} item(s)")
            briefing.append("")

        # High Priority Items
        high_threat_items = [item for item in items if item['threat_level'] >= 7.0]
        if high_threat_items:
            briefing.append("HIGH PRIORITY INTELLIGENCE (Threat Level ≥ 7.0)")
            briefing.append("-" * 80)
            for idx, item in enumerate(high_threat_items, 1):
                briefing.append(f"\n{idx}. {item['title']}")
                briefing.append(f"   Threat Level: {item['threat_level']}/10 | Relevance: {item['missionary_relevance']}/10")
                briefing.append(f"   Region: {item['region']} | Country: {item['country']}")
                briefing.append(f"   Location: {item['location']}")
                briefing.append(f"   Source: {item['source']}")
                briefing.append(f"   Date: {item['collection_date']}")
                briefing.append(f"\n   Summary:")
                briefing.append(f"   {item['summary']}")
                if item['keywords']:
                    briefing.append(f"\n   Keywords: {item['keywords']}")
            briefing.append("")

        # Moderate Priority Items
        moderate_threat_items = [item for item in items if 5.0 <= item['threat_level'] < 7.0]
        if moderate_threat_items:
            briefing.append("MODERATE PRIORITY INTELLIGENCE (Threat Level 5.0-6.9)")
            briefing.append("-" * 80)
            for idx, item in enumerate(moderate_threat_items, 1):
                briefing.append(f"\n{idx}. {item['title']}")
                briefing.append(f"   Threat Level: {item['threat_level']}/10 | Relevance: {item['missionary_relevance']}/10")
                briefing.append(f"   Region: {item['region']} | Location: {item['location']}")
                briefing.append(f"   Summary: {item['summary']}")
            briefing.append("")

        # Recommendations
        briefing.append("RECOMMENDATIONS")
        briefing.append("-" * 80)

        if stats['avg_threat'] >= 8.0:
            briefing.append("⚠ CRITICAL ALERT - Immediate Actions:")
            briefing.append("  • Initiate emergency protocols for affected regions")
            briefing.append("  • Contact all missionary personnel in high-threat areas")
            briefing.append("  • Consider evacuation or postponement of missions")
            briefing.append("  • Monitor situation continuously")
        elif stats['avg_threat'] >= 7.0:
            briefing.append("⚠ HIGH ALERT - Recommended Actions:")
            briefing.append("  • Brief all personnel on current threats")
            briefing.append("  • Implement enhanced security measures")
            briefing.append("  • Review and update emergency contact procedures")
            briefing.append("  • Restrict non-essential travel to affected areas")
        elif stats['avg_threat'] >= 5.0:
            briefing.append("⚠ MODERATE ALERT - Recommended Actions:")
            briefing.append("  • Maintain heightened awareness")
            briefing.append("  • Follow standard security protocols")
            briefing.append("  • Keep emergency contact information current")
            briefing.append("  • Monitor situation daily")
        else:
            briefing.append("✓ NORMAL OPERATIONS")
            briefing.append("  • Continue routine monitoring")
            briefing.append("  • Maintain standard security practices")
            briefing.append("  • Review intelligence updates regularly")

        briefing.append("")

        # Regional Specific Recommendations
        if stats['regions']:
            briefing.append("REGIONAL GUIDANCE")
            briefing.append("-" * 80)

            # Get threat levels by region
            region_threats = defaultdict(list)
            for item in items:
                if item['region']:
                    region_threats[item['region']].append(item['threat_level'])

            for region, threats in sorted(region_threats.items()):
                avg_regional_threat = sum(threats) / len(threats)
                briefing.append(f"\n{region}:")
                briefing.append(f"  Average Threat: {avg_regional_threat:.1f}/10")
                if avg_regional_threat >= 7.0:
                    briefing.append(f"  Status: HIGH RISK - Exercise extreme caution")
                    briefing.append(f"  Recommendation: Consider postponing non-essential missions")
                elif avg_regional_threat >= 5.0:
                    briefing.append(f"  Status: MODERATE RISK - Enhanced vigilance required")
                    briefing.append(f"  Recommendation: Proceed with caution, follow all protocols")
                else:
                    briefing.append(f"  Status: NORMAL - Standard operations")
                    briefing.append(f"  Recommendation: Continue with routine precautions")

        briefing.append("")
        briefing.append("=" * 80)
        briefing.append("END OF BRIEFING")
        briefing.append("=" * 80)
        briefing.append("")
        briefing.append("This briefing is CONFIDENTIAL and intended for authorized personnel only.")
        briefing.append("For questions or additional intelligence, contact WATCHKEEPER Operations.")
        briefing.append("")

        return "\n".join(briefing)

    def save_briefing(self, briefing: str, output_path: str = None):
        """Save briefing to file"""
        if not output_path:
            date_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = f"briefings/WATCHKEEPER_BRIEFING_{date_str}.txt"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(briefing)

        return output_path

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate WATCHKEEPER intelligence briefing')
    parser.add_argument('--date', type=str, help='Date for briefing (YYYY-MM-DD)', default=None)
    parser.add_argument('--days', type=int, help='Number of days to cover', default=1)
    parser.add_argument('--output', type=str, help='Output file path', default=None)
    parser.add_argument('--db', type=str, help='Database path', default='data/intelligence.db')

    args = parser.parse_args()

    generator = BriefingGenerator(args.db)

    try:
        # Generate briefing
        briefing = generator.generate_text_briefing(args.date, args.days)

        # Save to file
        output_path = generator.save_briefing(briefing, args.output)

        # Also print to console
        print(briefing)
        print(f"\n✓ Briefing saved to: {output_path}")

    finally:
        generator.close()

if __name__ == '__main__':
    main()
