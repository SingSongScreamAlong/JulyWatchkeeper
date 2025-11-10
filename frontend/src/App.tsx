/**
 * Main App Component
 * WATCHKEEPER Frontend Application
 */

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import websocket from './services/websocket';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('access_token');

    if (token) {
      setIsAuthenticated(true);

      // Connect to WebSocket
      websocket.connect(token);

      // Request notification permission
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }

    return () => {
      websocket.disconnect();
    };
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg">
          <h1 className="text-2xl font-bold mb-4">WATCHKEEPER</h1>
          <p className="text-gray-600 mb-4">Please log in to access the dashboard</p>
          <button
            onClick={() => {
              // Redirect to login page or show login form
              window.location.href = '/login';
            }}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Log In
          </button>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
