/**
 * API Service Layer
 * Centralized API communication for WATCHKEEPER frontend
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import type {
  User,
  IntelligenceItem,
  Alert,
  Incident,
  Personnel,
  DashboardStats,
  SearchResult,
  ThreatPrediction,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(username: string, password: string): Promise<{ access_token: string; user: User }> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    localStorage.setItem('access_token', response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get('/dashboard/stats');
    return response.data;
  }

  // Intelligence
  async getIntelligence(params?: {
    skip?: number;
    limit?: number;
    source?: string;
    category?: string;
    region?: string;
    min_threat?: number;
  }): Promise<IntelligenceItem[]> {
    const response = await this.client.get('/intelligence', { params });
    return response.data;
  }

  async getIntelligenceById(id: number): Promise<IntelligenceItem> {
    const response = await this.client.get(`/intelligence/${id}`);
    return response.data;
  }

  // Alerts
  async getAlerts(params?: {
    status?: string;
    severity?: string;
    skip?: number;
    limit?: number;
  }): Promise<Alert[]> {
    const response = await this.client.get('/alerts', { params });
    return response.data;
  }

  async acknowledgeAlert(alertId: number): Promise<Alert> {
    const response = await this.client.post(`/alerts/${alertId}/acknowledge`);
    return response.data;
  }

  async resolveAlert(alertId: number): Promise<Alert> {
    const response = await this.client.post(`/alerts/${alertId}/resolve`);
    return response.data;
  }

  // Incidents
  async getIncidents(params?: {
    status?: string;
    severity?: string;
    skip?: number;
    limit?: number;
  }): Promise<Incident[]> {
    const response = await this.client.get('/incidents', { params });
    return response.data;
  }

  async createIncident(incident: Partial<Incident>): Promise<Incident> {
    const response = await this.client.post('/incidents', incident);
    return response.data;
  }

  async updateIncident(id: number, updates: Partial<Incident>): Promise<Incident> {
    const response = await this.client.patch(`/incidents/${id}`, updates);
    return response.data;
  }

  // Personnel
  async getPersonnel(params?: {
    status?: string;
    region?: string;
    skip?: number;
    limit?: number;
  }): Promise<Personnel[]> {
    const response = await this.client.get('/personnel', { params });
    return response.data;
  }

  async getPersonnelById(id: number): Promise<Personnel> {
    const response = await this.client.get(`/personnel/${id}`);
    return response.data;
  }

  async updatePersonnelLocation(
    id: number,
    latitude: number,
    longitude: number
  ): Promise<Personnel> {
    const response = await this.client.post(`/personnel/${id}/location`, {
      latitude,
      longitude,
    });
    return response.data;
  }

  // Search
  async searchIntelligence(
    query: string,
    filters?: Record<string, any>
  ): Promise<{ total: number; results: SearchResult[] }> {
    const response = await this.client.get('/search/intelligence', {
      params: { q: query, ...filters },
    });
    return response.data;
  }

  async searchAll(query: string): Promise<{ total: number; results: SearchResult[] }> {
    const response = await this.client.get('/search/all', {
      params: { q: query },
    });
    return response.data;
  }

  async getTrendingTerms(days: number = 7): Promise<{ trending_terms: any[] }> {
    const response = await this.client.get('/search/trending', {
      params: { days },
    });
    return response.data;
  }

  // Analytics
  async getThreatPrediction(region: string): Promise<ThreatPrediction> {
    const response = await this.client.get('/analytics/threat-prediction', {
      params: { region },
    });
    return response.data;
  }

  async getRegionalStats(): Promise<any> {
    const response = await this.client.get('/analytics/regional-stats');
    return response.data;
  }

  // Geofences
  async getGeofences(): Promise<any[]> {
    const response = await this.client.get('/geofences');
    return response.data;
  }

  // Route Analysis
  async analyzeRoute(
    start_lat: number,
    start_lon: number,
    end_lat: number,
    end_lon: number
  ): Promise<any> {
    const response = await this.client.post('/routes/analyze', {
      start_lat,
      start_lon,
      end_lat,
      end_lon,
    });
    return response.data;
  }
}

export const api = new APIService();
export default api;
