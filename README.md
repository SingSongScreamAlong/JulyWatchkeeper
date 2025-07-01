# WATCHKEEPER: Advanced Intelligence Collection System

WATCHKEEPER is a sophisticated intelligence collection and analysis system designed to gather, process, and analyze information from diverse internet sources to provide comprehensive situational awareness and threat assessment. It seamlessly integrates with the Sentinel Dashboard for real-time intelligence sharing and visualization.

## Features

- **Multi-Source Intelligence Collection**
  - RSS Feed Processing
  - API Data Collection
  - Advanced Web Scraping
  - Stealth Web Navigation

- **Enhanced Data Processing**
  - Geolocation Support
  - Sentiment Analysis
  - Confidence Scoring
  - Publication Date Tracking
  - Keyword Extraction

- **Comprehensive Analysis**
  - Threat Assessment
  - Regional Intelligence Reports
  - Interactive Threat Maps
  - Source Verification
  - Multi-Source Consensus Analysis

- **Deployment Options**
  - Docker Containerization
  - PostgreSQL Integration
  - API Server for External Access
  - Configurable Source Management

## System Architecture

WATCHKEEPER consists of several key components:

1. **Intelligence Collector**: Gathers data from RSS feeds, APIs, and web sources
2. **Intelligence Analyzer**: Processes and analyzes collected intelligence
3. **Alert System**: Monitors for high-threat intelligence and sends alerts
4. **Database**: Stores intelligence items with rich metadata
5. **API Server**: Provides external access to intelligence data
6. **Guardian System**: Orchestrates the intelligence collection cycles

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL (included in Docker setup)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/watchkeeper.git
   cd watchkeeper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python init_database.py --force
   ```

4. Set up environment variables (create a .env file):
   ```
   # API Keys for Data Sources
   OSAC_API_KEY=your_osac_api_key
   ACLED_API_KEY=your_acled_api_key
   
   # API Authentication
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

### Running with Docker

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Access the API server at http://localhost:8000

### Running Locally

1. Start the intelligence collection:
   ```bash
   python guardian.py --monitor
   ```

2. Start the API server:
   ```bash
   python api_server.py
   ```

## Intelligence Source Configuration

WATCHKEEPER uses JSON configuration files to define intelligence sources. Sources are categorized by type:

- **RSS Sources**: Standard RSS/Atom feeds
- **API Sources**: REST API endpoints with JSON responses
- **Web Sources**: Web pages requiring advanced scraping

Example source configuration:
```json
{
  "name": "Example Source",
  "url": "https://example.com/feed",
  "type": "rss",
  "language": "en",
  "category": "security",
  "reliability": 8,
  "enabled": true
}
```

## Utility Scripts

- **merge_sources.py**: Merge multiple source configuration files
- **verify_sources.py**: Verify and validate intelligence sources
- **analyze_intelligence.py**: Generate intelligence reports and visualizations
- **init_database.py**: Initialize the database with schema and sample data
- **test_integration.py**: Test the WatchKeeper-Sentinel integration

## Sentinel Dashboard Integration

WATCHKEEPER integrates with the Sentinel Dashboard through multiple mechanisms:

1. **API Integration**: Intelligence data is sent to Sentinel via authenticated API calls
2. **File-Based Integration**: Dashboard data and HTML reports are exported for Sentinel consumption
3. **Real-Time Updates**: WebSocket-based real-time updates for immediate intelligence sharing

For detailed integration documentation, see [SENTINEL_INTEGRATION.md](SENTINEL_INTEGRATION.md).

## Database Schema

The intelligence_items table includes the following fields:

- id (INTEGER PRIMARY KEY)
- title (TEXT)
- content (TEXT)
- summary (TEXT)
- source (TEXT)
- url (TEXT)
- timestamp (TEXT) - ISO format
- publication_date (TEXT) - ISO format
- collection_date (TEXT) - ISO format
- threat_level (REAL)
- missionary_relevance (REAL)
- region (TEXT)
- country (TEXT)
- location (TEXT)
- latitude (REAL)
- longitude (REAL)
- keywords (TEXT)
- sentiment (REAL)
- confidence (REAL)

## Contributing

Contributions to WATCHKEEPER are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
