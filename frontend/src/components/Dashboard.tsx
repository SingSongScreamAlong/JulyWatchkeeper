/**
 * Main Dashboard Component
 * Overview of WATCHKEEPER system status and metrics
 */

import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import api from '../services/api';
import type { DashboardStats } from '../types';
import IntelligenceFeed from './IntelligenceFeed';
import AlertsPanel from './AlertsPanel';
import ThreatMap from './ThreatMap';
import StatsCards from './StatsCards';

const Dashboard: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>(
    'dashboardStats',
    () => api.getDashboardStats(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Error loading dashboard</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">WATCHKEEPER Dashboard</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        {stats && <StatsCards stats={stats} />}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Intelligence Feed - Takes 2 columns */}
          <div className="lg:col-span-2">
            <IntelligenceFeed />
          </div>

          {/* Alerts Panel */}
          <div className="lg:col-span-1">
            <AlertsPanel />
          </div>
        </div>

        {/* Threat Map */}
        <div className="mt-6">
          <ThreatMap />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
