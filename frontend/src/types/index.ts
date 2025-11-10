/**
 * WATCHKEEPER Frontend Type Definitions
 */

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  organization?: string;
}

export interface IntelligenceItem {
  id: number;
  title: string;
  content: string;
  source: string;
  category: string;
  region: string;
  threat_level: number;
  missionary_relevance: number;
  sentiment?: number;
  confidence?: number;
  collection_date: string;
  created_at: string;
  latitude?: number;
  longitude?: number;
  tags?: string[];
  keywords?: string[];
}

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  target_personnel?: number[];
  target_groups?: string[];
}

export interface Incident {
  id: number;
  title: string;
  description: string;
  incident_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'reported' | 'investigating' | 'resolved';
  location_name: string;
  latitude?: number;
  longitude?: number;
  reported_by: number;
  incident_date: string;
  created_at: string;
  resolved_at?: string;
}

export interface Personnel {
  id: number;
  name: string;
  organization: string;
  region: string;
  status: 'active' | 'inactive' | 'on_leave';
  current_latitude?: number;
  current_longitude?: number;
  last_checkin?: string;
  checkin_frequency?: number;
  emergency_contact?: string;
}

export interface ThreatPrediction {
  region: string;
  current_avg_threat: number;
  trend: number;
  prediction: 'escalating' | 'stable' | 'de-escalating';
  predicted_threat_level: number;
  confidence: number;
  timeframe_days: number;
}

export interface DashboardStats {
  total_intelligence: number;
  active_alerts: number;
  unacknowledged_alerts: number;
  open_incidents: number;
  active_personnel: number;
  personnel_in_danger: number;
  threat_level_avg: number;
  recent_collections: number;
}

export interface SearchResult {
  id: number;
  title: string;
  content?: string;
  description?: string;
  index_type: 'intelligence' | 'incidents' | 'alerts' | 'personnel';
  score: number;
  created_at: string;
  highlights?: {
    title?: string[];
    content?: string[];
  };
}

export interface WebSocketMessage {
  type: 'intelligence' | 'alert' | 'incident' | 'personnel_location' | 'system';
  action: 'create' | 'update' | 'delete';
  data: any;
  timestamp: string;
}

export interface MapMarker {
  id: number;
  type: 'intelligence' | 'incident' | 'personnel' | 'danger_zone';
  position: [number, number];
  title: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  data: any;
}

export interface Geofence {
  id: number;
  name: string;
  fence_type: 'danger_zone' | 'safe_zone' | 'checkpoint';
  geometry_type: 'circle' | 'polygon';
  coordinates: number[][];
  radius?: number;
  threat_level: number;
  active: boolean;
}

export interface Organization {
  id: number;
  name: string;
  type: string;
  region: string;
  created_at: string;
}

export interface SharedIntelligence {
  id: number;
  intelligence_id: number;
  shared_with_org_id: number;
  share_level: 'summary_only' | 'full' | 'classified';
  expiry_date?: string;
  created_at: string;
}
