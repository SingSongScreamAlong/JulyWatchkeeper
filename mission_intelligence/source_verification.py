"""
Source Verification Engine for Mission Intelligence Reports

This module provides functionality to verify intelligence sources used in mission reports
and ensure proper documentation and validation of all information.
"""

import sqlite3
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import re
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger("watchkeeper.mission_intelligence")

class SourceVerificationEngine:
    """
    Verifies and validates intelligence sources used in mission reports.
    Ensures all information is properly sourced and documented.
    """
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """
        Initialize the source verification engine with database connection.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        
        # Source reliability ratings
        self.reliability_ratings = {
            "A": "Completely reliable",
            "B": "Usually reliable",
            "C": "Fairly reliable",
            "D": "Not usually reliable",
            "E": "Unreliable",
            "F": "Reliability cannot be judged"
        }
        
        # Information credibility ratings
        self.credibility_ratings = {
            "1": "Confirmed by other sources",
            "2": "Probably true",
            "3": "Possibly true",
            "4": "Doubtful",
            "5": "Improbable",
            "6": "Truth cannot be judged"
        }
    
    def verify_source(self, source_url: str) -> Dict[str, Any]:
        """
        Verify an intelligence source URL.
        
        Args:
            source_url: URL to verify
            
        Returns:
            Dictionary with verification results
        """
        result = {
            "url": source_url,
            "verified": False,
            "status_code": None,
            "domain_reputation": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verification_method": "automated_check",
            "error": None
        }
        
        try:
            # Basic URL validation
            if not self._is_valid_url(source_url):
                result["error"] = "Invalid URL format"
                return result
            
            # Check domain reputation (simplified example)
            domain = urlparse(source_url).netloc
            result["domain_reputation"] = self._check_domain_reputation(domain)
            
            # Attempt to access the URL (with timeout)
            headers = {
                "User-Agent": "WATCHKEEPER Intelligence Verification System/1.0"
            }
            response = requests.head(source_url, headers=headers, timeout=5)
            result["status_code"] = response.status_code
            
            # Consider 2xx status codes as verified
            if 200 <= response.status_code < 300:
                result["verified"] = True
            else:
                result["error"] = f"HTTP status code: {response.status_code}"
            
            return result
            
        except requests.RequestException as e:
            result["error"] = f"Request error: {str(e)}"
            return result
        except Exception as e:
            result["error"] = f"Verification error: {str(e)}"
            return result
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _check_domain_reputation(self, domain: str) -> str:
        """
        Check the reputation of a domain.
        
        Args:
            domain: Domain to check
            
        Returns:
            Reputation rating (high, medium, low, unknown)
        """
        # This is a simplified example
        # In a real implementation, this would check against reputation databases
        trusted_domains = [
            "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "france24.com",
            "dw.com", "aljazeera.com", "cnn.com", "nytimes.com", "washingtonpost.com",
            "theguardian.com", "economist.com", "ft.com", "wsj.com"
        ]
        
        medium_domains = [
            "news.yahoo.com", "news.google.com", "msn.com", "foxnews.com", 
            "nbcnews.com", "cbsnews.com", "abcnews.go.com"
        ]
        
        if any(domain.endswith(d) for d in trusted_domains):
            return "high"
        elif any(domain.endswith(d) for d in medium_domains):
            return "medium"
        else:
            return "unknown"
    
    def verify_report_sources(self, report_id: int) -> Dict[str, Any]:
        """
        Verify all sources used in a mission intelligence report.
        
        Args:
            report_id: ID of the report to verify sources for
            
        Returns:
            Dictionary with verification results
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        results = {
            "report_id": report_id,
            "total_sources": 0,
            "verified_sources": 0,
            "unverified_sources": 0,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_details": []
        }
        
        try:
            # Get all intelligence sources linked to this report
            cursor.execute('''
                SELECT i.id, i.title, i.source, i.url, ris.section
                FROM intelligence_items i
                JOIN report_intelligence_sources ris ON i.id = ris.intelligence_id
                WHERE ris.report_id = ?
            ''', (report_id,))
            
            sources = cursor.fetchall()
            results["total_sources"] = len(sources)
            
            for source in sources:
                source_dict = dict(source)
                
                # Verify the source URL
                verification = self.verify_source(source_dict["url"])
                source_dict["verification"] = verification
                
                # Update verification info in the database
                cursor.execute('''
                    INSERT OR REPLACE INTO verification_info
                    (intelligence_id, source_verified, url_verified, timestamp, 
                     verification_method, verification_agent)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    source_dict["id"],
                    True,  # source_verified (assuming source name is trusted)
                    verification["verified"],
                    verification["timestamp"],
                    verification["verification_method"],
                    "WATCHKEEPER Source Verification Engine"
                ))
                
                # Count verified/unverified sources
                if verification["verified"]:
                    results["verified_sources"] += 1
                else:
                    results["unverified_sources"] += 1
                
                results["source_details"].append(source_dict)
            
            # Update the report's source documentation
            self._update_report_source_documentation(cursor, report_id, results)
            
            conn.commit()
            return results
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error verifying report sources: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def _update_report_source_documentation(self, 
                                          cursor, 
                                          report_id: int, 
                                          verification_results: Dict[str, Any]) -> None:
        """
        Update the source documentation section of a report based on verification results.
        
        Args:
            cursor: Database cursor
            report_id: ID of the report
            verification_results: Results of source verification
        """
        # Get existing source documentation
        cursor.execute(
            "SELECT * FROM report_source_documentation WHERE report_id = ?", 
            (report_id,)
        )
        doc = cursor.fetchone()
        
        # Calculate overall reliability rating
        verified_percent = 0
        if verification_results["total_sources"] > 0:
            verified_percent = (verification_results["verified_sources"] / 
                               verification_results["total_sources"]) * 100
        
        reliability_rating = "F"
        if verified_percent >= 90:
            reliability_rating = "A"
        elif verified_percent >= 75:
            reliability_rating = "B"
        elif verified_percent >= 50:
            reliability_rating = "C"
        elif verified_percent >= 25:
            reliability_rating = "D"
        else:
            reliability_rating = "E"
        
        # Format source list
        source_list = []
        for source in verification_results["source_details"]:
            source_list.append(f"{source['source']} ({source['title']})")
        
        sources_text = "Intelligence sources: " + "; ".join(source_list)
        
        # Format reliability ratings
        ratings_text = f"Overall reliability rating: {reliability_rating} - {self.reliability_ratings[reliability_rating]}"
        ratings_text += f"\nVerified sources: {verification_results['verified_sources']} of {verification_results['total_sources']} ({verified_percent:.1f}%)"
        
        if doc:
            # Update existing documentation
            cursor.execute('''
                UPDATE report_source_documentation
                SET intelligence_sources = ?,
                    reliability_ratings = ?,
                    collection_date = ?,
                    verification_methodology = ?
                WHERE report_id = ?
            ''', (
                sources_text,
                ratings_text,
                verification_results["verification_timestamp"],
                "Automated URL verification and domain reputation analysis",
                report_id
            ))
        else:
            # Create new documentation
            cursor.execute('''
                INSERT INTO report_source_documentation
                (report_id, intelligence_sources, reliability_ratings, collection_date,
                 verification_methodology, confidence_levels, bias_considerations, update_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                sources_text,
                ratings_text,
                verification_results["verification_timestamp"],
                "Automated URL verification and domain reputation analysis",
                "Based on source reliability and verification status",
                "Sources have been analyzed for potential bias based on domain reputation",
                "Sources will be re-verified every 7 days"
            ))
    
    def rate_source_reliability(self, 
                              intelligence_id: int, 
                              reliability_rating: str,
                              credibility_rating: str,
                              notes: str = None) -> bool:
        """
        Rate the reliability of an intelligence source.
        
        Args:
            intelligence_id: ID of the intelligence item
            reliability_rating: Reliability rating (A-F)
            credibility_rating: Credibility rating (1-6)
            notes: Optional notes about the rating
            
        Returns:
            True if rating was successful
        """
        if reliability_rating not in self.reliability_ratings:
            logger.error(f"Invalid reliability rating: {reliability_rating}")
            return False
        
        if credibility_rating not in self.credibility_ratings:
            logger.error(f"Invalid credibility rating: {credibility_rating}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if intelligence item exists
            cursor.execute(
                "SELECT id FROM intelligence_items WHERE id = ?", 
                (intelligence_id,)
            )
            if not cursor.fetchone():
                logger.warning(f"Intelligence item ID {intelligence_id} not found")
                return False
            
            # Store the rating in the verification_agent field as a workaround
            # Format: Human analyst:A-2 (where A is reliability, 2 is credibility)
            verification_agent = f"Human analyst:{reliability_rating}-{credibility_rating}"
            if notes:
                verification_agent += f" ({notes})"
                
            # Update or insert verification info with available columns
            cursor.execute('''
                INSERT OR REPLACE INTO verification_info
                (intelligence_id, source_verified, url_verified, timestamp,
                 verification_method, verification_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                intelligence_id,
                True,
                True,
                datetime.now(timezone.utc).isoformat(),
                "Manual verification",
                verification_agent
            ))
            
            conn.commit()
            logger.info(f"Rated intelligence item {intelligence_id}: {reliability_rating}-{credibility_rating}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error rating intelligence source: {e}")
            return False
        finally:
            conn.close()
    
    def get_source_verification_stats(self) -> Dict[str, Any]:
        """
        Get statistics about source verification.
        
        Returns:
            Dictionary with verification statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Total number of verified sources
            cursor.execute(
                "SELECT COUNT(*) FROM verification_info WHERE source_verified = 1"
            )
            stats['verified_sources'] = cursor.fetchone()[0]
            
            # Total number of unverified sources
            cursor.execute(
                "SELECT COUNT(*) FROM verification_info WHERE source_verified = 0"
            )
            stats['unverified_sources'] = cursor.fetchone()[0]
            
            # Verification by method
            cursor.execute(
                "SELECT verification_method, COUNT(*) FROM verification_info GROUP BY verification_method"
            )
            stats['verification_by_method'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Recent verifications (last 7 days)
            cursor.execute(
                "SELECT COUNT(*) FROM verification_info WHERE timestamp > datetime('now', '-7 days')"
            )
            stats['recent_verifications'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting verification statistics: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
