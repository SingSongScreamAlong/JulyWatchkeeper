/**
 * Search Interface Component
 * Advanced search across all WATCHKEEPER data
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import api from '../services/api';
import type { SearchResult } from '../types';

const SearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    source: '',
    category: '',
    region: '',
    min_threat: '',
  });
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, error } = useQuery(
    ['search', searchTerm, filters],
    () => api.searchIntelligence(searchTerm, filters),
    {
      enabled: searchTerm.length > 0,
    }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchTerm(query);
  };

  const clearFilters = () => {
    setFilters({
      source: '',
      category: '',
      region: '',
      min_threat: '',
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Search Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Intelligence Search</h1>
        <p className="text-gray-600">Search across intelligence items, incidents, and alerts</p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <form onSubmit={handleSearch}>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search intelligence, incidents, alerts..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              🔍 Search
            </button>
          </div>

          {/* Advanced Filters */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
              Advanced Filters
            </summary>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                <input
                  type="text"
                  value={filters.source}
                  onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                  placeholder="e.g., Reuters"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  <option value="security">Security</option>
                  <option value="political">Political</option>
                  <option value="health">Health</option>
                  <option value="economic">Economic</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                <input
                  type="text"
                  value={filters.region}
                  onChange={(e) => setFilters({ ...filters, region: e.target.value })}
                  placeholder="e.g., Middle East"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Threat Level</label>
                <select
                  value={filters.min_threat}
                  onChange={(e) => setFilters({ ...filters, min_threat: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any</option>
                  <option value="4">Medium (4+)</option>
                  <option value="6">High (6+)</option>
                  <option value="8">Critical (8+)</option>
                </select>
              </div>
            </div>

            <button
              type="button"
              onClick={clearFilters}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800"
            >
              Clear Filters
            </button>
          </details>
        </form>
      </div>

      {/* Search Results */}
      <div className="bg-white rounded-lg shadow-lg">
        {isLoading && (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Searching...</p>
          </div>
        )}

        {error && (
          <div className="p-6 text-center text-red-600">
            Error performing search. Please try again.
          </div>
        )}

        {data && data.total === 0 && (
          <div className="p-12 text-center">
            <p className="text-gray-600">No results found for "{searchTerm}"</p>
            <p className="text-sm text-gray-500 mt-2">Try adjusting your search or filters</p>
          </div>
        )}

        {data && data.total > 0 && (
          <div>
            <div className="px-6 py-4 border-b border-gray-200">
              <p className="text-sm text-gray-600">
                Found <span className="font-semibold text-gray-900">{data.total}</span> results
                {data.took_ms && <span> in {data.took_ms}ms</span>}
              </p>
            </div>

            <div className="divide-y divide-gray-200">
              {data.results.map((result: SearchResult, index: number) => (
                <div key={`${result.index_type}-${result.id}-${index}`} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Type Badge */}
                      <span className={`inline-block px-2 py-1 rounded text-xs font-semibold mb-2 ${
                        result.index_type === 'intelligence' ? 'bg-purple-100 text-purple-800' :
                        result.index_type === 'incidents' ? 'bg-orange-100 text-orange-800' :
                        result.index_type === 'alerts' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {result.index_type.charAt(0).toUpperCase() + result.index_type.slice(1)}
                      </span>

                      {/* Title */}
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {result.title}
                      </h3>

                      {/* Highlights */}
                      {result.highlights && result.highlights.content && (
                        <div className="prose prose-sm max-w-none mb-2">
                          {result.highlights.content.map((highlight, i) => (
                            <p
                              key={i}
                              className="text-gray-600"
                              dangerouslySetInnerHTML={{ __html: highlight }}
                            />
                          ))}
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                        <span>Score: {result.score.toFixed(2)}</span>
                        <span>•</span>
                        <span>{new Date(result.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    {/* View Button */}
                    <button className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium">
                      View →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchInterface;
