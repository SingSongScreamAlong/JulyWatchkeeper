"""Travel Route Safety Analysis Service

Analyzes travel routes for safety based on threat intelligence and geofencing.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class RouteAnalysisService:
    """Analyzes travel routes for safety"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in kilometers using Haversine formula"""
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def analyze_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        waypoints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Analyze a route for safety"""

        # Calculate direct distance
        direct_distance = self.calculate_distance(start_lat, start_lon, end_lat, end_lon)

        # Build route points
        route_points = [
            {'lat': start_lat, 'lon': start_lon, 'name': 'Start'}
        ]

        if waypoints:
            route_points.extend(waypoints)

        route_points.append({'lat': end_lat, 'lon': end_lon, 'name': 'End'})

        # Analyze each segment
        segments = []
        total_risk = 0.0
        high_risk_segments = []

        for i in range(len(route_points) - 1):
            segment = await self._analyze_segment(
                route_points[i],
                route_points[i + 1]
            )
            segments.append(segment)
            total_risk += segment['risk_score']

            if segment['risk_score'] >= 7.0:
                high_risk_segments.append(segment)

        # Calculate overall risk
        avg_risk = total_risk / len(segments) if segments else 0

        # Check for geofence intersections
        danger_zones = await self._check_geofence_intersections(route_points)

        # Identify checkpoints
        checkpoints = await self._identify_checkpoints(route_points)

        # Find intelligence along route
        nearby_intelligence = await self._find_intelligence_along_route(route_points)

        return {
            'distance_km': direct_distance,
            'segments': segments,
            'overall_risk_score': round(avg_risk, 2),
            'high_risk_segments': high_risk_segments,
            'danger_zones_crossed': danger_zones,
            'checkpoints': checkpoints,
            'nearby_intelligence': nearby_intelligence,
            'recommended': avg_risk < 6.0,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

    async def _analyze_segment(self, point_a: Dict, point_b: Dict) -> Dict[str, Any]:
        """Analyze safety of a route segment"""
        distance = self.calculate_distance(
            point_a['lat'], point_a['lon'],
            point_b['lat'], point_b['lon']
        )

        # Check for nearby threats
        threats = await self._find_threats_near_segment(point_a, point_b)

        # Calculate risk score based on threats
        risk_score = self._calculate_segment_risk(threats, distance)

        return {
            'from': point_a.get('name', f"{point_a['lat']:.2f},{point_a['lon']:.2f}"),
            'to': point_b.get('name', f"{point_b['lat']:.2f},{point_b['lon']:.2f}"),
            'distance_km': round(distance, 2),
            'risk_score': risk_score,
            'threats': threats
        }

    async def _find_threats_near_segment(
        self,
        point_a: Dict,
        point_b: Dict,
        radius_km: float = 50
    ) -> List[Dict]:
        """Find threats near a route segment"""
        from ..models.intelligence import IntelligenceItem
        from datetime import timedelta

        # Get recent high-threat intelligence
        recent_cutoff = datetime.utcnow() - timedelta(days=7)

        intelligence_items = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.threat_level >= 6.0,
            IntelligenceItem.created_at >= recent_cutoff,
            IntelligenceItem.latitude.isnot(None),
            IntelligenceItem.longitude.isnot(None)
        ).all()

        threats = []

        # Check if any intelligence is near the segment
        for intel in intelligence_items:
            # Check distance to both points (simplified - should check segment distance)
            dist_a = self.calculate_distance(
                point_a['lat'], point_a['lon'],
                intel.latitude, intel.longitude
            )
            dist_b = self.calculate_distance(
                point_b['lat'], point_b['lon'],
                intel.latitude, intel.longitude
            )

            min_dist = min(dist_a, dist_b)

            if min_dist <= radius_km:
                threats.append({
                    'id': intel.id,
                    'title': intel.title,
                    'threat_level': intel.threat_level,
                    'distance_km': round(min_dist, 2),
                    'location': intel.location
                })

        return threats

    def _calculate_segment_risk(self, threats: List[Dict], distance_km: float) -> float:
        """Calculate risk score for a segment"""
        if not threats:
            return 1.0  # Base risk

        # Weight threats by proximity and severity
        risk = 0.0

        for threat in threats:
            threat_level = threat['threat_level']
            distance = threat['distance_km']

            # Closer threats are more dangerous
            proximity_factor = max(0, 1 - (distance / 50))

            risk += threat_level * proximity_factor

        # Normalize to 0-10 scale
        return min(10.0, risk)

    async def _check_geofence_intersections(self, route_points: List[Dict]) -> List[Dict]:
        """Check if route crosses any danger zones"""
        from ..models.personnel import Geofence

        danger_zones = self.db.query(Geofence).filter(
            Geofence.active == True,
            Geofence.fence_type == 'danger_zone'
        ).all()

        intersections = []

        for zone in danger_zones:
            for point in route_points:
                distance = self.calculate_distance(
                    point['lat'], point['lon'],
                    zone.center_latitude, zone.center_longitude
                )

                if distance <= zone.radius_meters / 1000:  # Convert to km
                    intersections.append({
                        'zone_id': zone.id,
                        'zone_name': zone.name,
                        'threat_level': zone.threat_level,
                        'description': zone.description
                    })
                    break  # Only add each zone once

        return intersections

    async def _identify_checkpoints(self, route_points: List[Dict]) -> List[Dict]:
        """Identify potential checkpoints along route"""
        # In a real implementation, this would use:
        # - Border crossing data
        # - Known checkpoint locations
        # - Historical data

        checkpoints = []

        # Simplified: Look for potential border crossings based on distance
        for i in range(len(route_points) - 1):
            segment_distance = self.calculate_distance(
                route_points[i]['lat'], route_points[i]['lon'],
                route_points[i + 1]['lat'], route_points[i + 1]['lon']
            )

            # Large jumps might indicate border crossings
            if segment_distance > 200:
                checkpoints.append({
                    'type': 'potential_border_crossing',
                    'location': f"Between {route_points[i].get('name', 'waypoint')} and {route_points[i + 1].get('name', 'waypoint')}",
                    'note': 'Long distance segment may involve border crossing'
                })

        return checkpoints

    async def _find_intelligence_along_route(
        self,
        route_points: List[Dict],
        radius_km: float = 100
    ) -> List[Dict]:
        """Find relevant intelligence along route"""
        from ..models.intelligence import IntelligenceItem
        from datetime import timedelta

        recent_cutoff = datetime.utcnow() - timedelta(days=14)

        intelligence_items = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.created_at >= recent_cutoff,
            IntelligenceItem.latitude.isnot(None),
            IntelligenceItem.longitude.isnot(None)
        ).all()

        nearby = []

        for intel in intelligence_items:
            for point in route_points:
                distance = self.calculate_distance(
                    point['lat'], point['lon'],
                    intel.latitude, intel.longitude
                )

                if distance <= radius_km:
                    nearby.append({
                        'id': intel.id,
                        'title': intel.title,
                        'threat_level': intel.threat_level,
                        'distance_km': round(distance, 2),
                        'date': intel.collection_date
                    })
                    break

        # Sort by threat level
        nearby.sort(key=lambda x: x['threat_level'], reverse=True)

        return nearby[:10]  # Top 10

    async def suggest_safer_alternatives(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        current_risk: float
    ) -> List[Dict]:
        """Suggest safer alternative routes"""
        # This is a simplified implementation
        # In production, would use routing APIs with threat overlay

        alternatives = []

        # Calculate detour via safe intermediate points
        # This would integrate with OSM routing in production

        alternatives.append({
            'name': 'Alternative Route 1',
            'description': 'Route avoiding known high-risk areas',
            'estimated_risk': max(1.0, current_risk - 2.0),
            'additional_distance_km': 50,
            'note': 'Suggested alternative - detailed routing not yet implemented'
        })

        return alternatives if current_risk >= 7.0 else []
