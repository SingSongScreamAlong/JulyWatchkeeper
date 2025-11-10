/**
 * Alerts Panel Component
 * Real-time alerts with acknowledgment capability
 */

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import api from '../services/api';
import websocket from '../services/websocket';
import type { Alert, WebSocketMessage } from '../types';

const AlertsPanel: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<Alert[]>(
    'activeAlerts',
    () => api.getAlerts({ status: 'active', limit: 10 }),
    { refetchInterval: 30000 }
  );

  const acknowledgeMutation = useMutation(
    (alertId: number) => api.acknowledgeAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('activeAlerts');
      },
    }
  );

  useEffect(() => {
    if (data) {
      setAlerts(data);
    }
  }, [data]);

  // Subscribe to real-time alert updates
  useEffect(() => {
    websocket.subscribe('alerts');

    const unsubscribe = websocket.on('alert', (message: WebSocketMessage) => {
      if (message.action === 'create') {
        setAlerts((prev) => [message.data, ...prev]);

        // Play alert sound for critical alerts
        if (message.data.severity === 'critical') {
          playAlertSound();
        }
      } else if (message.action === 'update') {
        setAlerts((prev) =>
          prev.map((alert) => (alert.id === message.data.id ? message.data : alert))
        );
      }
    });

    return () => {
      websocket.unsubscribe('alerts');
      unsubscribe();
    };
  }, []);

  const handleAcknowledge = (alertId: number) => {
    acknowledgeMutation.mutate(alertId);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-600 text-white border-red-700';
      case 'high':
        return 'bg-orange-500 text-white border-orange-600';
      case 'medium':
        return 'bg-yellow-500 text-white border-yellow-600';
      default:
        return 'bg-blue-500 text-white border-blue-600';
    }
  };

  const playAlertSound = () => {
    // Play browser notification sound
    const audio = new Audio('/alert-sound.mp3');
    audio.play().catch(() => {
      // Silently fail if audio can't play
    });

    // Show browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('🚨 Critical Alert', {
        body: 'A new critical alert has been issued',
        icon: '/icon-192.png',
      });
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Active Alerts</h2>
      </div>

      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {isLoading ? (
          <div className="p-6 text-center text-gray-500">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <div className="text-4xl mb-2">✅</div>
            <div>No active alerts</div>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 border-l-4 ${
                alert.severity === 'critical' ? 'animate-pulse' : ''
              }`}
              style={{
                borderLeftColor:
                  alert.severity === 'critical'
                    ? '#dc2626'
                    : alert.severity === 'high'
                    ? '#f59e0b'
                    : '#3b82f6',
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityColor(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">{format(new Date(alert.created_at), 'MMM d, HH:mm')}</span>
                  </div>

                  <h3 className="text-sm font-semibold text-gray-900 mb-1">{alert.title}</h3>

                  <p className="text-sm text-gray-600 mb-3">{alert.message}</p>

                  {alert.status === 'active' && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={acknowledgeMutation.isLoading}
                      className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                      {acknowledgeMutation.isLoading ? 'Acknowledging...' : 'Acknowledge'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {alerts.length > 0 && (
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View All Alerts →
          </button>
        </div>
      )}
    </div>
  );
};

export default AlertsPanel;
