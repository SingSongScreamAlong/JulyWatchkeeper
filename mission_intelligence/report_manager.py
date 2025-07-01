"""
Mission Intelligence Report Manager

This module provides functionality to manage mission intelligence reports,
including creation, retrieval, updating, and deletion.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger("watchkeeper.mission_intelligence")

class MissionIntelligenceReportManager:
    """
    Manages mission intelligence reports in the WATCHKEEPER system.
    """
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """
        Initialize the report manager with database connection.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
    
    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a complete mission intelligence report with all sections.
        
        Args:
            report_id: ID of the report to retrieve
            
        Returns:
            Complete report as a dictionary, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get base report information
            cursor.execute(
                "SELECT * FROM mission_intelligence_reports WHERE id = ?", 
                (report_id,)
            )
            base_report = cursor.fetchone()
            
            if not base_report:
                logger.warning(f"Report ID {report_id} not found")
                return None
            
            report = dict(base_report)
            
            # Get all sections
            section_tables = [
                "report_executive_summary",
                "report_decision_support",
                "report_security_assessment",
                "report_threat_analysis",
                "report_natural_disasters",
                "report_religious_landscape",
                "report_cultural_dynamics",
                "report_social_climate",
                "report_spiritual_receptivity",
                "report_ministry_environment",
                "report_partnership_assessment",
                "report_transportation",
                "report_accommodation",
                "report_communication",
                "report_healthcare",
                "report_health_risks",
                "report_medical_preparation",
                "report_embassy_contacts",
                "report_emergency_services",
                "report_ministry_networks",
                "report_source_documentation",
                "report_quality_assurance",
                "report_intelligence_collection",
                "report_update_procedures",
                "report_team_composition",
                "report_mission_optimization",
                "report_duration_intelligence",
                "report_effectiveness_indicators",
                "report_risk_mitigation"
            ]
            
            # Add each section to the report
            for table in section_tables:
                section_name = table.replace("report_", "")
                cursor.execute(f"SELECT * FROM {table} WHERE report_id = ?", (report_id,))
                section_data = cursor.fetchone()
                
                if section_data:
                    report[section_name] = dict(section_data)
                else:
                    report[section_name] = {"status": "missing"}
            
            # Get linked intelligence sources
            cursor.execute('''
                SELECT i.*, ris.section, ris.relevance_score
                FROM intelligence_items i
                JOIN report_intelligence_sources ris ON i.id = ris.intelligence_id
                WHERE ris.report_id = ?
            ''', (report_id,))
            
            sources = {}
            for row in cursor.fetchall():
                source = dict(row)
                section = source.pop('section')
                if section not in sources:
                    sources[section] = []
                sources[section].append(source)
            
            report['intelligence_sources'] = sources
            
            return report
            
        except Exception as e:
            logger.error(f"Error retrieving report {report_id}: {e}")
            return None
        finally:
            conn.close()
    
    def get_all_reports(self, 
                       region: str = None, 
                       country: str = None, 
                       mission_type: str = None,
                       limit: int = 50,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all mission intelligence reports, optionally filtered.
        
        Args:
            region: Optional region filter
            country: Optional country filter
            mission_type: Optional mission type filter
            limit: Maximum number of reports to return
            offset: Number of reports to skip for pagination
            
        Returns:
            List of report summaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM mission_intelligence_reports"
            params = []
            
            # Add filters if provided
            conditions = []
            if region:
                conditions.append("region = ?")
                params.append(region)
            if country:
                conditions.append("country = ?")
                params.append(country)
            if mission_type:
                conditions.append("mission_type = ?")
                params.append(mission_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            reports = [dict(row) for row in cursor.fetchall()]
            
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving reports: {e}")
            return []
        finally:
            conn.close()
    
    def delete_report(self, report_id: int) -> bool:
        """
        Delete a mission intelligence report.
        
        Args:
            report_id: ID of the report to delete
            
        Returns:
            True if deletion was successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if report exists
            cursor.execute(
                "SELECT id FROM mission_intelligence_reports WHERE id = ?", 
                (report_id,)
            )
            if not cursor.fetchone():
                logger.warning(f"Report ID {report_id} not found for deletion")
                return False
            
            # Delete the report (cascading delete will handle related tables)
            cursor.execute(
                "DELETE FROM mission_intelligence_reports WHERE id = ?", 
                (report_id,)
            )
            
            conn.commit()
            logger.info(f"Deleted report ID: {report_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting report {report_id}: {e}")
            return False
        finally:
            conn.close()
    
    def export_report_json(self, report_id: int) -> Optional[str]:
        """
        Export a report as JSON.
        
        Args:
            report_id: ID of the report to export
            
        Returns:
            JSON string of the report, or None if not found
        """
        report = self.get_report(report_id)
        if not report:
            return None
        
        # Convert datetime objects to strings
        for key, value in report.items():
            if isinstance(value, datetime):
                report[key] = value.isoformat()
        
        return json.dumps(report, indent=2)
    
    def export_report_html(self, report_id: int) -> Optional[str]:
        """
        Export a report as HTML for display in the Sentinel Dashboard.
        
        Args:
            report_id: ID of the report to export
            
        Returns:
            HTML string of the report, or None if not found
        """
        report = self.get_report(report_id)
        if not report:
            return None
        
        # Generate HTML representation
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mission Intelligence Report: {report.get('title', 'Untitled')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .report-header {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    border-left: 5px solid #007bff;
                }}
                .section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    background-color: #fff;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .section-title {{
                    color: #007bff;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                .alert {{
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .alert-green {{ background-color: #d4edda; color: #155724; }}
                .alert-yellow {{ background-color: #fff3cd; color: #856404; }}
                .alert-orange {{ background-color: #ffe5d0; color: #fd7e14; }}
                .alert-red {{ background-color: #f8d7da; color: #721c24; }}
                .alert-black {{ background-color: #343a40; color: #fff; }}
                .source-item {{
                    padding: 10px;
                    margin-bottom: 5px;
                    background-color: #f8f9fa;
                    border-left: 3px solid #007bff;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="report-header">
                <h1>{report.get('title', 'Untitled Mission Intelligence Report')}</h1>
                <p><strong>Mission ID:</strong> {report.get('mission_id', 'Unknown')}</p>
                <p><strong>Region:</strong> {report.get('region', 'Unknown')} | <strong>Country:</strong> {report.get('country', 'Unknown')}</p>
                <p><strong>Created:</strong> {report.get('created_at', 'Unknown')} | <strong>Updated:</strong> {report.get('updated_at', 'Unknown')}</p>
                <p><strong>Valid Until:</strong> {report.get('validity_period_end', 'Unknown')}</p>
                
                <div class="alert alert-{report.get('alert_status', 'yellow').lower()}">
                    <h3>ALERT STATUS: {report.get('alert_status', 'UNKNOWN').upper()}</h3>
                    <p><strong>Threat Level:</strong> {report.get('overall_threat_level', 'Unknown')}/10</p>
                    <p><strong>Confidence:</strong> {report.get('confidence_level', 'Unknown')}</p>
                    <p><strong>Recommendation:</strong> {report.get('go_no_go_recommendation', False) and 'GO' or 'NO-GO'}</p>
                    <p><strong>Rationale:</strong> {report.get('go_no_go_rationale', 'Not provided')}</p>
                </div>
            </div>
        """
        
        # Executive Summary Section
        exec_summary = report.get('executive_summary', {})
        html += f"""
            <div class="section">
                <h2 class="section-title">📋 EXECUTIVE SUMMARY</h2>
                <h3>Key Decision Points</h3>
                <p>{exec_summary.get('key_decision_points', 'Not provided')}</p>
                
                <h3>Critical Briefing Highlights</h3>
                <p>{exec_summary.get('critical_briefing_highlights', 'Not provided')}</p>
                
                <h3>Alternative Timing Recommendations</h3>
                <p>{exec_summary.get('alternative_timing_recommendations', 'Not provided')}</p>
            </div>
        """
        
        # Continue with other sections...
        # This is a simplified version - a complete implementation would include all sections
        
        # Security & Threat Assessment
        security = report.get('security_assessment', {})
        html += f"""
            <div class="section">
                <h2 class="section-title">🛡️ SECURITY & THREAT ASSESSMENT</h2>
                <h3>Government & Political Stability</h3>
                <p><strong>Government Stability:</strong> {security.get('government_stability', 'Not provided')}</p>
                <p><strong>Political Changes:</strong> {security.get('political_changes', 'Not provided')}</p>
                <p><strong>Government Attitude:</strong> {security.get('government_attitude', 'Not provided')}</p>
                <p><strong>Religious Freedom:</strong> {security.get('religious_freedom', 'Not provided')}</p>
            </div>
        """
        
        # Add intelligence sources section
        sources = report.get('intelligence_sources', {})
        html += f"""
            <div class="section">
                <h2 class="section-title">📊 INTELLIGENCE SOURCES & VERIFICATION</h2>
                <p>The following intelligence sources were used in this report:</p>
        """
        
        for section, section_sources in sources.items():
            html += f"<h3>{section.replace('_', ' ').title()}</h3>"
            for source in section_sources:
                html += f"""
                    <div class="source-item">
                        <p><strong>{source.get('title', 'Untitled')}</strong></p>
                        <p>Source: {source.get('source', 'Unknown')} | Date: {source.get('collection_date', 'Unknown')}</p>
                        <p>Relevance Score: {source.get('relevance_score', 'N/A')}</p>
                    </div>
                """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about mission intelligence reports.
        
        Returns:
            Dictionary with report statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Total number of reports
            cursor.execute("SELECT COUNT(*) FROM mission_intelligence_reports")
            stats['total_reports'] = cursor.fetchone()[0]
            
            # Reports by region
            cursor.execute(
                "SELECT region, COUNT(*) FROM mission_intelligence_reports GROUP BY region"
            )
            stats['reports_by_region'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Reports by mission type
            cursor.execute(
                "SELECT mission_type, COUNT(*) FROM mission_intelligence_reports GROUP BY mission_type"
            )
            stats['reports_by_mission_type'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Reports by alert status
            cursor.execute(
                "SELECT alert_status, COUNT(*) FROM mission_intelligence_reports GROUP BY alert_status"
            )
            stats['reports_by_alert_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average threat level
            cursor.execute(
                "SELECT AVG(overall_threat_level) FROM mission_intelligence_reports"
            )
            stats['average_threat_level'] = cursor.fetchone()[0]
            
            # Recent reports (last 30 days)
            cursor.execute(
                "SELECT COUNT(*) FROM mission_intelligence_reports WHERE created_at > datetime('now', '-30 days')"
            )
            stats['recent_reports'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting report statistics: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
