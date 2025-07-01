# WatchKeeper-Sentinel Integration Documentation

## Overview

This document provides a comprehensive guide to the integration between WatchKeeper and the Sentinel Dashboard. It covers the current implementation status, configuration requirements, and recommendations for production deployment.

## Integration Architecture

The WatchKeeper-Sentinel integration consists of three main components:

1. **API Integration**: WatchKeeper sends intelligence data to Sentinel via REST API calls
2. **File-Based Integration**: WatchKeeper exports intelligence data as JSON files and HTML reports
3. **Real-Time Updates**: WebSocket-based real-time updates from WatchKeeper to Sentinel

### Architecture Diagram

```
+----------------+                  +-------------------+
|                |  1. API Calls   |                   |
|                |---------------->|                   |
|                |                  |                   |
|   WatchKeeper  |  2. File Export |     Sentinel      |
|                |---------------->|     Dashboard     |
|                |                  |                   |
|                |  3. WebSockets  |                   |
|                |<--------------->|                   |
+----------------+                  +-------------------+
```

## Configuration

The integration is configured through environment variables in the `.env` file:

```bash
# API Configuration
API_KEY=watchkeeper_secure_api_key_2025
API_HOST=0.0.0.0
API_PORT=8000

# Sentinel Integration
SENTINEL_API_ENDPOINT=https://sentinel-dashboard.example.com/api/v1/intelligence
SENTINEL_API_KEY=sentinel_integration_key_2025

# WebSocket Configuration
WEBSOCKET_ENABLED=true
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8000
```

## API Integration

The API integration is implemented in the `guardian.py` module through the `IntelligenceCollector.send_to_sentinel` method. This method:

1. Prepares intelligence items with verification metadata
2. Constructs a payload with the items and metadata
3. Sends the payload to the Sentinel API endpoint using the configured API key
4. Handles errors and returns a status report

### API Authentication

API authentication is implemented using API keys. The WatchKeeper API expects an API key in the `Authorization` header of requests, and the Sentinel API expects the WatchKeeper API key in its requests.

## File-Based Integration

The file-based integration is implemented in the `mission_intelligence/dashboard_integration.py` module through the `DashboardIntegration` class. This class:

1. Generates dashboard data from intelligence items
2. Exports the data to JSON files in the dashboard directory
3. Generates HTML report cards for individual intelligence reports

## Real-Time Updates

Real-time updates are implemented using WebSockets. The integration consists of:

1. **WebSocket Server**: Implemented in the API (`src/api/websocket.py`)
2. **WebSocket Client**: Implemented in the dashboard (`dashboard/websocket_client.py`)
3. **Topic-Based Broadcasting**: Intelligence updates, system status, and alerts

### WebSocket Topics

- `intelligence_updates`: New or updated intelligence items
- `system_status`: WatchKeeper system status updates
- `alerts`: Critical alerts and notifications

## Testing

A test Sentinel interface is provided in `src/test_sentinel_interface.py`. This script:

1. Implements a mock Sentinel API endpoint
2. Simulates WebSocket connections and broadcasts
3. Provides a UI for testing the integration

To run the test interface:

```bash
python src/test_sentinel_interface.py
```

The test interface will be available at http://localhost:8080.

## Production Deployment Recommendations

1. **Security**:
   - Use strong, unique API keys for both WatchKeeper and Sentinel
   - Enable HTTPS for all API endpoints
   - Restrict CORS origins to specific domains

2. **Reliability**:
   - Implement retry logic for API calls
   - Add monitoring for WebSocket connections
   - Set up alerts for integration failures

3. **Performance**:
   - Optimize the frequency of intelligence data updates
   - Implement rate limiting for API calls
   - Use connection pooling for database access

4. **Monitoring**:
   - Log all API calls and WebSocket events
   - Monitor API response times and error rates
   - Set up alerts for integration failures

## Troubleshooting

### API Integration Issues

- Check API key configuration in `.env` file
- Verify Sentinel API endpoint is accessible
- Check API logs for error messages

### WebSocket Issues

- Verify WebSocket server is running on the configured port
- Check WebSocket client connection status in the dashboard
- Look for connection errors in the logs

### File-Based Integration Issues

- Check file permissions in the dashboard directory
- Verify the database connection is working
- Check for error messages in the logs

## Conclusion

The WatchKeeper-Sentinel integration provides a robust, multi-layered approach to sharing intelligence data. By combining API calls, file-based exports, and real-time WebSocket updates, the integration ensures that the Sentinel Dashboard always has access to the latest intelligence data from WatchKeeper.
