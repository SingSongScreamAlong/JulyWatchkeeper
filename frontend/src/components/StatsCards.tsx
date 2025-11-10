/**
 * Stats Cards Component
 * Displays key metrics at a glance
 */

import React from 'react';
import type { DashboardStats } from '../types';

interface StatsCardsProps {
  stats: DashboardStats;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const cards = [
    {
      title: 'Active Alerts',
      value: stats.active_alerts,
      subtitle: `${stats.unacknowledged_alerts} unacknowledged`,
      color: stats.unacknowledged_alerts > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800',
      icon: '🚨',
    },
    {
      title: 'Open Incidents',
      value: stats.open_incidents,
      subtitle: 'Requiring attention',
      color: stats.open_incidents > 5 ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800',
      icon: '⚠️',
    },
    {
      title: 'Active Personnel',
      value: stats.active_personnel,
      subtitle: `${stats.personnel_in_danger} in danger zones`,
      color: stats.personnel_in_danger > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800',
      icon: '👥',
    },
    {
      title: 'Intelligence Items',
      value: stats.recent_collections,
      subtitle: 'Last 24 hours',
      color: 'bg-purple-100 text-purple-800',
      icon: '📡',
    },
    {
      title: 'Threat Level',
      value: stats.threat_level_avg.toFixed(1),
      subtitle: 'Regional average',
      color: getThreatColor(stats.threat_level_avg),
      icon: '📊',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((card) => (
        <div key={card.title} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{card.value}</p>
              <p className="mt-2 text-xs text-gray-500">{card.subtitle}</p>
            </div>
            <div className={`px-3 py-2 rounded-full ${card.color} text-2xl`}>
              {card.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

function getThreatColor(level: number): string {
  if (level >= 8) return 'bg-red-100 text-red-800';
  if (level >= 6) return 'bg-orange-100 text-orange-800';
  if (level >= 4) return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
}

export default StatsCards;
