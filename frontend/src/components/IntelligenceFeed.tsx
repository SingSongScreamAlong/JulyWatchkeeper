/**
 * Intelligence Feed Component
 * Real-time feed of intelligence items
 */

import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import api from '../services/api';
import websocket from '../services/websocket';
import type { IntelligenceItem, WebSocketMessage } from '../types';

const IntelligenceFeed: React.FC = () => {
  const [items, setItems] = useState<IntelligenceItem[]>([]);
  const [filter, setFilter] = useState<{
    category?: string;
    region?: string;
    min_threat?: number;
  }>({});

  const { data, isLoading } = useQuery<IntelligenceItem[]>(
    ['intelligence', filter],
    () => api.getIntelligence({ ...filter, limit: 20 }),
    { refetchInterval: 60000 }
  );

  useEffect(() => {
    if (data) {
      setItems(data);
    }
  }, [data]);

  // Subscribe to real-time updates
  useEffect(() => {
    websocket.subscribe('intelligence');

    const unsubscribe = websocket.on('intelligence', (message: WebSocketMessage) => {
      if (message.action === 'create') {
        setItems((prev) => [message.data, ...prev].slice(0, 20));
      }
    });

    return () => {
      websocket.unsubscribe('intelligence');
      unsubscribe();
    };
  }, []);

  const getThreatBadge = (level: number) => {
    if (level >= 8) return 'bg-red-600 text-white';
    if (level >= 6) return 'bg-orange-500 text-white';
    if (level >= 4) return 'bg-yellow-500 text-white';
    return 'bg-green-500 text-white';
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Intelligence Feed</h2>
          <div className="flex gap-2">
            <select
              className="text-sm border border-gray-300 rounded-md px-3 py-1"
              value={filter.category || ''}
              onChange={(e) => setFilter({ ...filter, category: e.target.value || undefined })}
            >
              <option value="">All Categories</option>
              <option value="security">Security</option>
              <option value="political">Political</option>
              <option value="health">Health</option>
              <option value="economic">Economic</option>
            </select>

            <select
              className="text-sm border border-gray-300 rounded-md px-3 py-1"
              value={filter.min_threat || ''}
              onChange={(e) =>
                setFilter({ ...filter, min_threat: e.target.value ? Number(e.target.value) : undefined })
              }
            >
              <option value="">All Threats</option>
              <option value="6">High (6+)</option>
              <option value="8">Critical (8+)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {isLoading ? (
          <div className="p-6 text-center text-gray-500">Loading intelligence...</div>
        ) : items.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No intelligence items found</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getThreatBadge(item.threat_level)}`}>
                      Threat {item.threat_level}
                    </span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                      {item.category}
                    </span>
                    <span className="text-xs text-gray-500">{item.region}</span>
                  </div>

                  <h3 className="text-base font-semibold text-gray-900 mb-1">{item.title}</h3>

                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{item.content}</p>

                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>Source: {item.source}</span>
                    <span>•</span>
                    <span>Missionary Relevance: {item.missionary_relevance}/10</span>
                    <span>•</span>
                    <span>{format(new Date(item.created_at), 'MMM d, HH:mm')}</span>
                  </div>
                </div>

                <button className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View Details →
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default IntelligenceFeed;
