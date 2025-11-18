/**
 * Incident Reporting Form
 * Mobile-friendly form for field incident reporting
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import api from '../services/api';

interface IncidentFormProps {
  onClose?: () => void;
  onSuccess?: () => void;
}

const IncidentForm: React.FC<IncidentFormProps> = ({ onClose, onSuccess }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    incident_type: 'other',
    severity: 'medium',
    location_name: '',
    latitude: '',
    longitude: '',
  });

  const createIncidentMutation = useMutation(
    (data: any) => api.createIncident(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('incidents');
        if (onSuccess) onSuccess();
        if (onClose) onClose();
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const incidentData = {
      ...formData,
      latitude: formData.latitude ? parseFloat(formData.latitude) : undefined,
      longitude: formData.longitude ? parseFloat(formData.longitude) : undefined,
    };

    createIncidentMutation.mutate(incidentData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData({
            ...formData,
            latitude: position.coords.latitude.toString(),
            longitude: position.coords.longitude.toString(),
          });
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Could not get your location. Please enter manually.');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  const severityColors = {
    low: 'bg-green-500 text-white',
    medium: 'bg-yellow-500 text-white',
    high: 'bg-orange-500 text-white',
    critical: 'bg-red-600 text-white',
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Report Incident</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Incident Title *
          </label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Brief description of the incident"
          />
        </div>

        {/* Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Incident Type *
          </label>
          <select
            name="incident_type"
            value={formData.incident_type}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="security">Security Threat</option>
            <option value="health">Health Emergency</option>
            <option value="natural_disaster">Natural Disaster</option>
            <option value="civil_unrest">Civil Unrest</option>
            <option value="accident">Accident</option>
            <option value="theft">Theft/Crime</option>
            <option value="harassment">Harassment</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Severity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity *
          </label>
          <div className="grid grid-cols-4 gap-2">
            {(['low', 'medium', 'high', 'critical'] as const).map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setFormData({ ...formData, severity: level })}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  formData.severity === level
                    ? severityColors[level]
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description *
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Provide detailed information about the incident..."
          />
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            name="location_name"
            value={formData.location_name}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-2"
            placeholder="Location name (e.g., city, building)"
          />

          <div className="grid grid-cols-2 gap-4">
            <input
              type="number"
              name="latitude"
              value={formData.latitude}
              onChange={handleChange}
              step="any"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Latitude"
            />
            <input
              type="number"
              name="longitude"
              value={formData.longitude}
              onChange={handleChange}
              step="any"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Longitude"
            />
          </div>

          <button
            type="button"
            onClick={getCurrentLocation}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            📍 Use my current location
          </button>
        </div>

        {/* Submit Buttons */}
        <div className="flex items-center justify-end gap-4 pt-4 border-t">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={createIncidentMutation.isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createIncidentMutation.isLoading ? 'Submitting...' : 'Submit Incident'}
          </button>
        </div>

        {createIncidentMutation.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            Error submitting incident. Please try again.
          </div>
        )}
      </form>
    </div>
  );
};

export default IncidentForm;
