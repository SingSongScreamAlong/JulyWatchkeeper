# WATCHKEEPER Frontend Dashboard

React-based dashboard for WATCHKEEPER intelligence system.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Stack

- React 18 + TypeScript
- Tailwind CSS for styling
- React Query for data fetching
- Recharts for visualizations
- Leaflet for maps
- WebSocket for real-time updates

## Key Features

- Real-time intelligence feed
- Interactive threat map with personnel locations
- Alert management dashboard
- Incident reporting form
- Analytics and charts
- Mobile-responsive design

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/       # Main dashboard
│   │   ├── Intelligence/    # Intelligence feed
│   │   ├── Map/            # Interactive map
│   │   ├── Alerts/         # Alert management
│   │   ├── Incidents/      # Incident forms
│   │   └── Personnel/      # Personnel tracking
│   ├── services/           # API services
│   ├── hooks/              # Custom hooks
│   ├── utils/              # Utilities
│   └── App.tsx             # Main app
├── public/
└── package.json
```

## Environment Variables

Create `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_MAP_API_KEY=your_mapbox_key
```

## Development

Components use TypeScript for type safety. All API calls go through
the service layer in `src/services/`.

Real-time updates handled via WebSocket connection in `src/services/websocket.ts`.

## Deployment

```bash
npm run build
# Deploy build/ directory to static hosting
```

Recommended: Vercel, Netlify, or S3 + CloudFront
