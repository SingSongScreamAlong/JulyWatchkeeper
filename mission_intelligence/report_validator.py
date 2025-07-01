"""
Mission Intelligence Report Validator

This module provides functionality to validate mission intelligence reports
against the comprehensive requirements specified in the WATCHKEEPER system.
"""

import sqlite3
import logging
from typing import Dict, List, Any, Tuple, Set

# Configure logging
logger = logging.getLogger("watchkeeper.mission_intelligence")

class MissionIntelligenceReportValidator:
    """
    Validates mission intelligence reports to ensure they meet all required standards
    and contain all necessary sections with proper sourcing.
    """
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """
        Initialize the report validator with database connection.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        
        # Define the required sections and their mandatory fields
        self.required_sections = {
            "executive_summary": [
                "key_decision_points", 
                "critical_briefing_highlights"
            ],
            "decision_support": [
                "security_concerns", 
                "ministry_opportunities", 
                "critical_timing_considerations", 
                "resource_requirements", 
                "budget_impact", 
                "insurance_liability", 
                "recommended_team_composition"
            ],
            "security_assessment": [
                "government_stability", 
                "political_changes", 
                "government_attitude", 
                "religious_freedom", 
                "visa_requirements", 
                "embassy_support"
            ],
            "threat_analysis": [
                "terrorism_threat", 
                "criminal_activity", 
                "areas_to_avoid", 
                "safe_zones", 
                "transportation_security", 
                "communication_security", 
                "cyber_security"
            ],
            "natural_disasters": [
                "weather_patterns", 
                "disaster_probability", 
                "health_hazards", 
                "emergency_response", 
                "evacuation_routes"
            ],
            "religious_landscape": [
                "dominant_religions", 
                "christian_presence", 
                "interfaith_relationships", 
                "religious_freedom", 
                "persecution_patterns", 
                "government_policies", 
                "missionary_history"
            ],
            "cultural_dynamics": [
                "cultural_values", 
                "communication_styles", 
                "gender_roles", 
                "family_structures", 
                "dress_codes", 
                "language_requirements"
            ],
            "social_climate": [
                "social_tensions", 
                "economic_conditions", 
                "media_landscape", 
                "corruption_levels", 
                "human_rights", 
                "womens_rights"
            ],
            "spiritual_receptivity": [
                "spiritual_openness", 
                "responsive_demographics", 
                "effective_approaches", 
                "gospel_barriers"
            ],
            "ministry_environment": [
                "legal_framework", 
                "registration_requirements", 
                "evangelism_laws", 
                "church_planting"
            ],
            "partnership_assessment": [
                "missionary_presence", 
                "local_church_capacity", 
                "financial_infrastructure"
            ],
            "transportation": [
                "airport_access", 
                "domestic_transportation", 
                "road_conditions", 
                "evacuation_routes"
            ],
            "accommodation": [
                "accommodation_options", 
                "security_assessment", 
                "utilities_reliability", 
                "cost_of_living", 
                "food_safety", 
                "banking_services"
            ],
            "communication": [
                "mobile_coverage", 
                "internet_availability", 
                "wifi_security", 
                "social_media_restrictions", 
                "emergency_protocols"
            ],
            "healthcare": [
                "healthcare_quality", 
                "hospital_locations", 
                "emergency_services", 
                "medical_insurance", 
                "medication_availability", 
                "medical_evacuation"
            ],
            "health_risks": [
                "endemic_diseases", 
                "food_water_safety", 
                "vector_diseases", 
                "travelers_diarrhea"
            ],
            "medical_preparation": [
                "required_vaccinations", 
                "medical_kit", 
                "medication_import", 
                "health_insurance"
            ],
            "embassy_contacts": [
                "embassy_contact", 
                "consular_services", 
                "emergency_numbers", 
                "evacuation_assistance"
            ],
            "emergency_services": [
                "police_numbers", 
                "medical_emergency", 
                "fire_department"
            ],
            "ministry_networks": [
                "local_church_contacts"
            ],
            "source_documentation": [
                "intelligence_sources", 
                "reliability_ratings", 
                "collection_date", 
                "verification_methodology", 
                "confidence_levels", 
                "bias_considerations", 
                "update_frequency"
            ],
            "quality_assurance": [
                "fact_checking", 
                "expert_review", 
                "cultural_sensitivity", 
                "monitoring_protocols"
            ],
            "intelligence_collection": [
                "realtime_monitoring", 
                "early_warning", 
                "alert_systems", 
                "social_media_monitoring", 
                "news_monitoring"
            ],
            "update_procedures": [
                "update_frequency", 
                "emergency_alerts", 
                "communication_channels", 
                "escalation_procedures", 
                "stakeholder_notification", 
                "quality_control"
            ],
            "team_composition": [
                "team_size", 
                "gender_composition", 
                "professional_skills", 
                "language_requirements", 
                "leadership_structure"
            ],
            "effectiveness_indicators": [
                "opportunity_utilization", 
                "cultural_integration", 
                "relationship_building", 
                "security_prevention", 
                "financial_efficiency", 
                "long_term_impact"
            ],
            "risk_mitigation": [
                "threat_detection", 
                "emergency_preparedness", 
                "communication_reliability", 
                "medical_preparation", 
                "cultural_sensitivity", 
                "legal_compliance", 
                "technology_security", 
                "transportation_safety", 
                "disaster_preparedness"
            ]
        }
    
    def validate_report(self, report_id: int) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate a mission intelligence report against all requirements.
        
        Args:
            report_id: ID of the report to validate
            
        Returns:
            Tuple containing:
            - Boolean indicating if report is valid
            - Dictionary of validation issues by section
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        issues = {}
        
        try:
            # Validate base report information
            cursor.execute(
                "SELECT * FROM mission_intelligence_reports WHERE id = ?", 
                (report_id,)
            )
            report = cursor.fetchone()
            
            if not report:
                logger.error(f"Report ID {report_id} not found")
                return False, {"general": ["Report not found"]}
            
            # Check each required section
            for section, required_fields in self.required_sections.items():
                section_issues = self._validate_section(cursor, report_id, section, required_fields)
                if section_issues:
                    issues[section] = section_issues
            
            # Validate source documentation
            source_issues = self._validate_sources(cursor, report_id)
            if source_issues:
                issues["sources"] = source_issues
            
            is_valid = len(issues) == 0
            
            return is_valid, issues
            
        except Exception as e:
            logger.error(f"Error validating report {report_id}: {e}")
            return False, {"general": [f"Validation error: {str(e)}"]}
        finally:
            conn.close()
    
    def _validate_section(self, 
                         cursor, 
                         report_id: int, 
                         section: str, 
                         required_fields: List[str]) -> List[str]:
        """
        Validate a specific section of a report.
        
        Args:
            cursor: Database cursor
            report_id: ID of the report
            section: Section name
            required_fields: List of required fields in the section
            
        Returns:
            List of validation issues for the section
        """
        table_name = f"report_{section}"
        issues = []
        
        try:
            # Check if section exists
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE report_id = ?", 
                (report_id,)
            )
            section_data = cursor.fetchone()
            
            if not section_data:
                return [f"Section '{section}' is missing"]
            
            # Check required fields
            for field in required_fields:
                if field not in section_data.keys():
                    issues.append(f"Required field '{field}' is missing")
                elif not section_data[field] or section_data[field].startswith("INCOMPLETE"):
                    issues.append(f"Required field '{field}' is incomplete")
            
            return issues
            
        except sqlite3.OperationalError:
            return [f"Section '{section}' table does not exist"]
        except Exception as e:
            return [f"Error validating section '{section}': {str(e)}"]
    
    def _validate_sources(self, cursor, report_id: int) -> List[str]:
        """
        Validate that the report has proper source documentation.
        
        Args:
            cursor: Database cursor
            report_id: ID of the report
            
        Returns:
            List of source validation issues
        """
        issues = []
        
        try:
            # Check if source documentation exists
            cursor.execute(
                "SELECT * FROM report_source_documentation WHERE report_id = ?", 
                (report_id,)
            )
            source_doc = cursor.fetchone()
            
            if not source_doc:
                return ["Source documentation is missing"]
            
            # Check if intelligence sources are linked
            cursor.execute(
                "SELECT COUNT(*) FROM report_intelligence_sources WHERE report_id = ?", 
                (report_id,)
            )
            source_count = cursor.fetchone()[0]
            
            if source_count == 0:
                issues.append("No intelligence sources are linked to this report")
            
            # Check source coverage across sections
            cursor.execute(
                "SELECT DISTINCT section FROM report_intelligence_sources WHERE report_id = ?", 
                (report_id,)
            )
            covered_sections = set([row[0] for row in cursor.fetchall()])
            
            # Get critical sections that must have sources
            critical_sections = {
                "security_assessment", "threat_analysis", "religious_landscape", 
                "spiritual_receptivity", "ministry_environment"
            }
            
            missing_coverage = critical_sections - covered_sections
            if missing_coverage:
                for section in missing_coverage:
                    issues.append(f"Section '{section}' has no linked intelligence sources")
            
            return issues
            
        except Exception as e:
            return [f"Error validating sources: {str(e)}"]
    
    def get_report_completion_status(self, report_id: int) -> Dict[str, Any]:
        """
        Get the completion status of a report.
        
        Args:
            report_id: ID of the report
            
        Returns:
            Dictionary with completion statistics
        """
        is_valid, issues = self.validate_report(report_id)
        
        total_sections = len(self.required_sections)
        sections_with_issues = len(issues)
        completion_percentage = ((total_sections - sections_with_issues) / total_sections) * 100
        
        return {
            "report_id": report_id,
            "is_valid": is_valid,
            "completion_percentage": completion_percentage,
            "sections_complete": total_sections - sections_with_issues,
            "sections_incomplete": sections_with_issues,
            "total_sections": total_sections,
            "issues_by_section": issues
        }
    
    def get_missing_sources(self, report_id: int) -> Dict[str, List[str]]:
        """
        Get sections that are missing proper source documentation.
        
        Args:
            report_id: ID of the report
            
        Returns:
            Dictionary mapping sections to missing source types
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        missing_sources = {}
        
        try:
            # Get all sections that should have sources
            for section in self.required_sections.keys():
                # Check if section has linked intelligence sources
                cursor.execute(
                    "SELECT COUNT(*) FROM report_intelligence_sources WHERE report_id = ? AND section = ?", 
                    (report_id, section)
                )
                source_count = cursor.fetchone()[0]
                
                if source_count == 0:
                    missing_sources[section] = ["No intelligence sources linked"]
            
            return missing_sources
            
        except Exception as e:
            logger.error(f"Error checking missing sources: {e}")
            return {"error": [str(e)]}
        finally:
            conn.close()
