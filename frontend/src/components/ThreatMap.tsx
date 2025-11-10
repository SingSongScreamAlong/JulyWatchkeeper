/**
 * Threat Map Component
 * Interactive map showing intelligence locations, incidents, and personnel
 */

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { useQuery } from 'react-query';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../services/api';
import type { MapMarker } from '../types';

// Fix for default marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

const ThreatMap: React.FC = () => {
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [selectedLayer, setSelectedLayer] = useState<string>('all');

  // Fetch intelligence with locations
  const { data: intelligence } = useQuery(
    'intelligenceLocations',
    () => api.getIntelligence({ limit: 100 }),
    { refetchInterval: 60000 }
  );

  // Fetch incidents
  const { data: incidents } = useQuery(
    'incidentLocations',
    () => api.getIncidents({ limit: 100 }),
    { refetchInterval: 60000 }
  );

  // Fetch personnel
  const { data: personnel } = useQuery(
    'personnelLocations',
    () => api.getPersonnel({ limit: 100 }),
    { refetchInterval: 30000 }
  );

  // Fetch geofences
  const { data: geofences } = useQuery('geofences', () => api.getGeofences(), {
    refetchInterval: 300000,
  });

  useEffect(() => {
    const newMarkers: MapMarker[] = [];

    // Add intelligence markers
    if (intelligence && (selectedLayer === 'all' || selectedLayer === 'intelligence')) {
      intelligence
        .filter((item) => item.latitude && item.longitude)
        .forEach((item) => {
          newMarkers.push({
            id: item.id,
            type: 'intelligence',
            position: [item.latitude!, item.longitude!],
            title: item.title,
            severity: getThreatSeverity(item.threat_level),
            data: item,
          });
        });
    }

    // Add incident markers
    if (incidents && (selectedLayer === 'all' || selectedLayer === 'incidents')) {
      incidents
        .filter((incident) => incident.latitude && incident.longitude)
        .forEach((incident) => {
          newMarkers.push({
            id: incident.id,
            type: 'incident',
            position: [incident.latitude!, incident.longitude!],
            title: incident.title,
            severity: incident.severity,
            data: incident,
          });
        });
    }

    // Add personnel markers
    if (personnel && (selectedLayer === 'all' || selectedLayer === 'personnel')) {
      personnel
        .filter((person) => person.current_latitude && person.current_longitude)
        .forEach((person) => {
          newMarkers.push({
            id: person.id,
            type: 'personnel',
            position: [person.current_latitude!, person.current_longitude!],
            title: person.name,
            data: person,
          });
        });
    }

    setMarkers(newMarkers);
  }, [intelligence, incidents, personnel, selectedLayer]);

  const getThreatSeverity = (level: number): 'low' | 'medium' | 'high' | 'critical' => {
    if (level >= 8) return 'critical';
    if (level >= 6) return 'high';
    if (level >= 4) return 'medium';
    return 'low';
  };

  const getMarkerColor = (marker: MapMarker): string => {
    if (marker.type === 'personnel') return '#3b82f6'; // Blue

    switch (marker.severity) {
      case 'critical':
        return '#dc2626'; // Red
      case 'high':
        return '#f59e0b'; // Orange
      case 'medium':
        return '#eab308'; // Yellow
      default:
        return '#22c55e'; // Green
    }
  };

  const createCustomIcon = (marker: MapMarker) => {
    const color = getMarkerColor(marker);
    const emoji =
      marker.type === 'personnel' ? '👤' : marker.type === 'incident' ? '⚠️' : '📍';

    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
        <span style="font-size: 16px;">${emoji}</span>
      </div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Threat Map</h2>

          <div className="flex gap-2">
            <select
              className="text-sm border border-gray-300 rounded-md px-3 py-1"
              value={selectedLayer}
              onChange={(e) => setSelectedLayer(e.target.value)}
            >
              <option value="all">All Layers</option>
              <option value="intelligence">Intelligence</option>
              <option value="incidents">Incidents</option>
              <option value="personnel">Personnel</option>
            </select>
          </div>
        </div>
      </div>

      <div className="h-[500px] relative">
        <MapContainer
          center={[20, 0]}
          zoom={2}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Render markers */}
          {markers.map((marker) => (
            <Marker
              key={`${marker.type}-${marker.id}`}
              position={marker.position}
              icon={createCustomIcon(marker)}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-semibold text-sm mb-1">{marker.title}</h3>
                  <p className="text-xs text-gray-600 mb-2">Type: {marker.type}</p>
                  {marker.severity && (
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        marker.severity === 'critical'
                          ? 'bg-red-600 text-white'
                          : marker.severity === 'high'
                          ? 'bg-orange-500 text-white'
                          : 'bg-yellow-500 text-white'
                      }`}
                    >
                      {marker.severity.toUpperCase()}
                    </span>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Render danger zone circles */}
          {geofences
            ?.filter((gf) => gf.fence_type === 'danger_zone' && gf.geometry_type === 'circle')
            .map((gf) => (
              <Circle
                key={gf.id}
                center={[gf.coordinates[0][0], gf.coordinates[0][1]]}
                radius={gf.radius || 5000}
                pathOptions={{
                  color: 'red',
                  fillColor: 'red',
                  fillOpacity: 0.2,
                }}
              >
                <Popup>
                  <div className="p-2">
                    <h3 className="font-semibold text-sm">{gf.name}</h3>
                    <p className="text-xs text-gray-600">Danger Zone</p>
                    <p className="text-xs">Threat Level: {gf.threat_level}</p>
                  </div>
                </Popup>
              </Circle>
            ))}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-600"></div>
            <span>Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span>High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-600"></div>
            <span>Personnel</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreatMap;
