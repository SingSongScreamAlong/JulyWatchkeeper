"""
Dashboard Integration for Mission Intelligence Reports

This module provides functionality to integrate mission intelligence reports
with the Sentinel Dashboard for visualization and monitoring.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import os
import math

from .report_manager import MissionIntelligenceReportManager

# Configure logging
logger = logging.getLogger("watchkeeper.mission_intelligence")

class DashboardIntegration:
    """
    Integrates mission intelligence reports with the Sentinel Dashboard.
    Provides data visualization, alerts, and monitoring capabilities.
    """
    
    def __init__(self, db_path: str = 'data/intelligence.db', dashboard_path: str = 'dashboard'):
        """
        Initialize the dashboard integration with database connection.
        
        Args:
            db_path: Path to the SQLite database
            dashboard_path: Path to the dashboard directory
        """
        self.db_path = db_path
        self.dashboard_path = dashboard_path
        self.report_manager = MissionIntelligenceReportManager(db_path)
        
        # Ensure dashboard directory exists
        os.makedirs(os.path.join(self.dashboard_path, 'data'), exist_ok=True)
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate data for the Sentinel Dashboard.
        
        Returns:
            Dictionary with dashboard data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        dashboard_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reports": {
                "total": 0,
                "by_region": {},
                "by_alert_status": {},
                "recent": []
            },
            "threats": {
                "high_threat_regions": [],
                "threat_trends": [],
                "alert_distribution": {}
            },
            "intelligence": {
                "source_verification": {},
                "collection_coverage": {},
                "intelligence_gaps": []
            }
        }
        
        try:
            # Get report statistics
            stats = self.report_manager.get_report_statistics()
            dashboard_data["reports"]["total"] = stats.get("total_reports", 0)
            dashboard_data["reports"]["by_region"] = stats.get("reports_by_region", {})
            dashboard_data["reports"]["by_alert_status"] = stats.get("reports_by_alert_status", {})
            
            # Get recent reports
            cursor.execute("""
                SELECT id, title, region, country, alert_status, overall_threat_level,
                       created_at, updated_at
                FROM mission_intelligence_reports
                ORDER BY created_at DESC
                LIMIT 10
            """)
            dashboard_data["reports"]["recent"] = [dict(row) for row in cursor.fetchall()]
            
            # Get high threat regions
            cursor.execute("""
                SELECT region, AVG(overall_threat_level) as avg_threat
                FROM mission_intelligence_reports
                GROUP BY region
                HAVING avg_threat > 7
                ORDER BY avg_threat DESC
            """)
            dashboard_data["threats"]["high_threat_regions"] = [
                {"region": row[0], "threat_level": row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Get threat trends (simplified - would use time series in production)
            cursor.execute("""
                SELECT strftime('%Y-%m', created_at) as month, 
                       AVG(overall_threat_level) as avg_threat
                FROM mission_intelligence_reports
                WHERE created_at > datetime('now', '-6 months')
                GROUP BY month
                ORDER BY month
            """)
            dashboard_data["threats"]["threat_trends"] = [
                {"month": row[0], "avg_threat": row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Get alert distribution
            cursor.execute("""
                SELECT alert_status, COUNT(*) as count
                FROM mission_intelligence_reports
                GROUP BY alert_status
            """)
            dashboard_data["threats"]["alert_distribution"] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            # Get source verification stats
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN source_verified = 1 THEN 1 ELSE 0 END) as verified,
                       SUM(CASE WHEN source_verified = 0 THEN 1 ELSE 0 END) as unverified
                FROM verification_info
            """)
            row = cursor.fetchone()
            if row:
                dashboard_data["intelligence"]["source_verification"] = {
                    "total": row[0],
                    "verified": row[1],
                    "unverified": row[2],
                    "verification_rate": row[1] / row[0] if row[0] > 0 else 0
                }
            
            # Get collection coverage by region
            cursor.execute("""
                SELECT r.region, COUNT(DISTINCT i.id) as coverage
                FROM mission_intelligence_reports r
                LEFT JOIN report_intelligence_sources ris ON r.id = ris.report_id
                LEFT JOIN intelligence_items i ON ris.intelligence_id = i.id
                GROUP BY r.region
            """)
            dashboard_data["intelligence"]["collection_coverage"] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            # Identify intelligence gaps (regions with low source coverage)
            for region, coverage in dashboard_data["intelligence"]["collection_coverage"].items():
                if coverage < 5:  # Arbitrary threshold
                    dashboard_data["intelligence"]["intelligence_gaps"].append({
                        "region": region,
                        "coverage": coverage,
                        "recommendation": "Increase intelligence collection for this region"
                    })
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def export_dashboard_data(self) -> bool:
        """
        Export dashboard data to JSON files for the Sentinel Dashboard.
        
        Returns:
            True if export was successful
        """
        try:
            # Generate dashboard data
            dashboard_data = self.generate_dashboard_data()
            
            # Save to JSON file
            data_path = os.path.join(self.dashboard_path, 'data', 'mission_intelligence.json')
            with open(data_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            
            # Generate individual report data
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM mission_intelligence_reports")
            report_ids = [row[0] for row in cursor.fetchall()]
            
            for report_id in report_ids:
                report_html = self.report_manager.export_report_html(report_id)
                if report_html:
                    report_path = os.path.join(self.dashboard_path, 'data', f'report_{report_id}.html')
                    with open(report_path, 'w') as f:
                        f.write(report_html)
            
            logger.info(f"Dashboard data exported to {self.dashboard_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting dashboard data: {e}")
            return False
    
    def generate_alert_widgets(self) -> List[Dict[str, Any]]:
        """
        Generate alert widgets for the Sentinel Dashboard.
        
        Returns:
            List of alert widget configurations
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        widgets = []
        
        try:
            # High threat alerts
            cursor.execute("""
                SELECT id, title, region, country, alert_status, overall_threat_level
                FROM mission_intelligence_reports
                WHERE alert_status IN ('RED', 'BLACK') AND overall_threat_level >= 8
                ORDER BY overall_threat_level DESC, created_at DESC
                LIMIT 5
            """)
            
            high_threats = cursor.fetchall()
            if high_threats:
                widgets.append({
                    "type": "alert",
                    "title": "HIGH THREAT MISSIONS",
                    "priority": "critical",
                    "items": [dict(row) for row in high_threats]
                })
            
            # Recent intelligence updates
            cursor.execute("""
                SELECT id, title, region, country, updated_at
                FROM mission_intelligence_reports
                WHERE updated_at > datetime('now', '-24 hours')
                ORDER BY updated_at DESC
                LIMIT 5
            """)
            
            recent_updates = cursor.fetchall()
            if recent_updates:
                widgets.append({
                    "type": "updates",
                    "title": "RECENT INTELLIGENCE UPDATES",
                    "priority": "info",
                    "items": [dict(row) for row in recent_updates]
                })
            
            # Unverified sources alert
            cursor.execute("""
                SELECT COUNT(*) FROM verification_info WHERE source_verified = 0
            """)
            unverified_count = cursor.fetchone()[0]
            
            if unverified_count > 0:
                widgets.append({
                    "type": "alert",
                    "title": "UNVERIFIED INTELLIGENCE SOURCES",
                    "priority": "warning",
                    "count": unverified_count,
                    "message": f"There are {unverified_count} unverified intelligence sources that require verification."
                })
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error generating alert widgets: {e}")
            return []
        finally:
            conn.close()
    
    def generate_map_data(self) -> Dict[str, Any]:
        """
        Generate map data for the Sentinel Dashboard.
        
        Returns:
            Dictionary with map data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        map_data = {
            "type": "FeatureCollection",
            "features": []
        }
        
        try:
            # Get country data with threat levels
            cursor.execute("""
                SELECT country, 
                       AVG(overall_threat_level) as avg_threat,
                       COUNT(*) as report_count
                FROM mission_intelligence_reports
                GROUP BY country
            """)
            
            countries = cursor.fetchall()
            
            # This is a simplified example - in production, you would use real
            # geospatial data with proper coordinates for each country
            for country in countries:
                # Placeholder coordinates - in production these would be real
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": country["country"],
                        "threat_level": country["avg_threat"],
                        "report_count": country["report_count"],
                        "color": self._get_threat_color(country["avg_threat"])
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [0, 0]  # Placeholder
                    }
                }
                map_data["features"].append(feature)
            
            return map_data
            
        except Exception as e:
            logger.error(f"Error generating map data: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def _get_threat_color(self, threat_level: float) -> str:
        """
        Get color based on threat level.
        
        Args:
            threat_level: Threat level (0-10)
            
        Returns:
            Hex color code
        """
        if threat_level >= 8:
            return "#FF0000"  # Red
        elif threat_level >= 6:
            return "#FFA500"  # Orange
        elif threat_level >= 4:
            return "#FFFF00"  # Yellow
        else:
            return "#00FF00"  # Green
    
    def generate_dashboard_components(self) -> Dict[str, Any]:
        """
        Generate all components for the Sentinel Dashboard.
        
        Returns:
            Dictionary with all dashboard components
        """
        components = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            },
            "overview": self.generate_dashboard_data(),
            "alerts": self.generate_alert_widgets(),
            "map": self.generate_map_data(),
            "reports": {
                "recent": self.report_manager.get_all_reports(limit=10),
                "high_threat": self.report_manager.get_all_reports(limit=5)  # Would filter by threat in production
            }
        }
        
        # Export to dashboard
        data_path = os.path.join(self.dashboard_path, 'data', 'dashboard_components.json')
        try:
            with open(data_path, 'w') as f:
                json.dump(components, f, indent=2)
            logger.info(f"Dashboard components exported to {data_path}")
        except Exception as e:
            logger.error(f"Error exporting dashboard components: {e}")
        
        return components
    
    def render_mission_report_card(self, report_id: int) -> str:
        """
        Generate HTML for a mission report card to be displayed in the dashboard.
        
        Args:
            report_id: ID of the report
            
        Returns:
            HTML string for the report card
        """
        report = self.report_manager.get_report(report_id)
        if not report:
            return "<div class='error'>Report not found</div>"
        
        # Determine card color based on alert status
        color_class = "card-green"
        if report.get("alert_status") == "RED":
            color_class = "card-red"
        elif report.get("alert_status") == "ORANGE":
            color_class = "card-orange"
        elif report.get("alert_status") == "YELLOW":
            color_class = "card-yellow"
        elif report.get("alert_status") == "BLACK":
            color_class = "card-black"
        
        # Format the card HTML
        html = f"""
        <div class="mission-report-card {color_class}" data-report-id="{report_id}">
            <div class="card-header">
                <h3>{report.get('title', 'Untitled Report')}</h3>
                <span class="badge">{report.get('alert_status', 'UNKNOWN')}</span>
            </div>
            <div class="card-body">
                <div class="location">
                    <i class="fa fa-map-marker"></i> {report.get('region', 'Unknown Region')}, {report.get('country', 'Unknown Country')}
                </div>
                <div class="threat-level">
                    Threat Level: <strong>{report.get('overall_threat_level', 'Unknown')}/10</strong>
                </div>
                <div class="mission-type">
                    Mission Type: {report.get('mission_type', 'Unknown')}
                </div>
                <div class="dates">
                    <div>Created: {report.get('created_at', 'Unknown')}</div>
                    <div>Updated: {report.get('updated_at', 'Unknown')}</div>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary view-report" data-report-id="{report_id}">View Report</button>
                <button class="btn btn-secondary update-report" data-report-id="{report_id}">Update</button>
            </div>
        </div>
        """
        
        return html
    
    def generate_dashboard_summary_widget(self) -> str:
        """
        Generate HTML for a dashboard summary widget.
        
        Returns:
            HTML string for the summary widget
        """
        stats = self.report_manager.get_report_statistics()
        
        html = f"""
        <div class="dashboard-summary-widget">
            <h2>Mission Intelligence Summary</h2>
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">{stats.get('total_reports', 0)}</div>
                    <div class="stat-label">Total Reports</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats.get('recent_reports', 0)}</div>
                    <div class="stat-label">Recent Reports (30d)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats.get('average_threat_level', 0):.1f}</div>
                    <div class="stat-label">Avg Threat Level</div>
                </div>
            </div>
            
            <h3>Reports by Region</h3>
            <div class="region-chart">
                <!-- Chart would be rendered by JavaScript in production -->
                <ul>
        """
        
        for region, count in stats.get('reports_by_region', {}).items():
            html += f"<li>{region}: {count}</li>"
        
        html += """
                </ul>
            </div>
            
            <h3>Alert Status Distribution</h3>
            <div class="alert-chart">
                <!-- Chart would be rendered by JavaScript in production -->
                <ul>
        """
        
        for status, count in stats.get('reports_by_alert_status', {}).items():
            html += f"<li>{status}: {count}</li>"
        
        html += """
                </ul>
            </div>
            
            <div class="summary-footer">
                <button class="btn btn-primary" id="view-all-reports">View All Reports</button>
                <button class="btn btn-secondary" id="export-summary">Export Summary</button>
            </div>
        </div>
        """
        
        return html
