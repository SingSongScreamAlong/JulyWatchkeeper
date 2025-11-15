#!/usr/bin/env python3
"""
WATCHKEEPER PDF Briefing Generator
Generates professional PDF intelligence briefings
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠ ReportLab not installed. Install with: pip install reportlab")

class PDFBriefingGenerator:
    """Generates PDF intelligence briefings"""

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
                'regions': {},
                'max_threat': 0.0,
                'min_threat': 0.0,
                'avg_relevance': 0.0
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

    def get_alert_color(self, alert_level: str):
        """Get color for alert level"""
        color_map = {
            'BLACK': colors.black,
            'RED': colors.red,
            'ORANGE': colors.orange,
            'YELLOW': colors.yellow,
            'GREEN': colors.green
        }
        return color_map.get(alert_level, colors.grey)

    def generate_pdf_briefing(self, date: str = None, days: int = 1, output_path: str = None):
        """Generate a PDF-formatted intelligence briefing"""
        if not REPORTLAB_AVAILABLE:
            print("❌ Cannot generate PDF: ReportLab not installed")
            return None

        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%d')

        if not output_path:
            date_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = f"briefings/WATCHKEEPER_BRIEFING_{date_str}.pdf"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Get data
        items = self.get_intelligence_for_period(days)
        stats = self.get_stats(items)

        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=12,
            spaceAfter=6
        )

        alert_level = self.get_alert_level(stats['avg_threat'])
        alert_color = self.get_alert_color(alert_level)

        # Title
        story.append(Paragraph("WATCHKEEPER", title_style))
        story.append(Paragraph("INTELLIGENCE BRIEFING", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Classification header
        classification_data = [[Paragraph("<b>CONFIDENTIAL</b>", styles['Normal'])]]
        classification_table = Table(classification_data, colWidths=[6.5*inch])
        classification_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(classification_table)
        story.append(Spacer(1, 0.2*inch))

        # Header info
        header_data = [
            ['Date:', date],
            ['Coverage Period:', f'Last {days} day(s)'],
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Alert Level:', alert_level]
        ]
        header_table = Table(header_data, colWidths=[2*inch, 4.5*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (1, 3), (1, 3), alert_color),
            ('TEXTCOLOR', (1, 3), (1, 3), colors.white if alert_level in ['BLACK', 'RED'] else colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))

        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary_data = [
            ['Total Intelligence Items:', str(stats['total_items'])],
            ['Average Threat Level:', f"{stats['avg_threat']:.1f}/10"],
            ['High Threat Items (≥7.0):', str(stats['high_threat_count'])],
            ['Overall Assessment:', self.get_threat_assessment(stats['avg_threat'])],
            ['Missionary Relevance:', f"{stats['avg_relevance']:.1f}/10"]
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        # Regional Distribution
        if stats['regions']:
            story.append(Paragraph("REGIONAL DISTRIBUTION", heading_style))
            region_data = [['Region', 'Items']]
            for region, count in sorted(stats['regions'].items(), key=lambda x: x[1], reverse=True):
                region_data.append([region, str(count)])

            region_table = Table(region_data, colWidths=[4*inch, 2.5*inch])
            region_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(region_table)
            story.append(Spacer(1, 0.2*inch))

        # High Priority Items
        high_threat_items = [item for item in items if item['threat_level'] >= 7.0]
        if high_threat_items:
            story.append(PageBreak())
            story.append(Paragraph("HIGH PRIORITY INTELLIGENCE", heading_style))
            story.append(Paragraph("<i>Threat Level ≥ 7.0</i>", styles['Italic']))
            story.append(Spacer(1, 0.1*inch))

            for idx, item in enumerate(high_threat_items, 1):
                # Item header
                item_title = Paragraph(f"<b>{idx}. {item['title']}</b>", styles['Heading3'])
                story.append(item_title)

                # Item details table
                details_data = [
                    ['Threat Level:', f"{item['threat_level']}/10"],
                    ['Relevance:', f"{item['missionary_relevance']}/10"],
                    ['Region:', item['region'] or 'N/A'],
                    ['Country:', item['country'] or 'N/A'],
                    ['Location:', item['location'] or 'N/A'],
                    ['Source:', item['source']],
                    ['Date:', item['collection_date'][:10]]
                ]

                details_table = Table(details_data, colWidths=[1.5*inch, 5*inch])
                details_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(details_table)
                story.append(Spacer(1, 0.1*inch))

                # Summary
                summary_para = Paragraph(f"<b>Summary:</b> {item['summary']}", styles['Normal'])
                story.append(summary_para)

                # Keywords
                if item['keywords']:
                    keywords_para = Paragraph(f"<b>Keywords:</b> {item['keywords']}", styles['Italic'])
                    story.append(keywords_para)

                story.append(Spacer(1, 0.2*inch))

        # Build PDF
        doc.build(story)
        return output_path

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate WATCHKEEPER PDF intelligence briefing')
    parser.add_argument('--date', type=str, help='Date for briefing (YYYY-MM-DD)', default=None)
    parser.add_argument('--days', type=int, help='Number of days to cover', default=1)
    parser.add_argument('--output', type=str, help='Output file path', default=None)
    parser.add_argument('--db', type=str, help='Database path', default='data/intelligence.db')

    args = parser.parse_args()

    generator = PDFBriefingGenerator(args.db)

    try:
        output_path = generator.generate_pdf_briefing(args.date, args.days, args.output)

        if output_path:
            print(f"✓ PDF briefing generated: {output_path}")
            print(f"✓ File size: {os.path.getsize(output_path)} bytes")
        else:
            print("❌ PDF generation failed")

    finally:
        generator.close()

if __name__ == '__main__':
    main()
