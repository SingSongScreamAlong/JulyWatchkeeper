# WATCHKEEPER Advanced Search

Elasticsearch-powered full-text search across all WATCHKEEPER data.

## Overview

WATCHKEEPER uses Elasticsearch for advanced search capabilities including:

- Full-text search across intelligence, incidents, alerts, and personnel
- Fuzzy matching and typo tolerance
- Geospatial search (find items near a location)
- Multi-field search with relevance scoring
- Aggregations and faceted search
- Real-time search suggestions
- Trending term analysis

## Quick Start

### 1. Start Elasticsearch

```bash
# Start with docker-compose
docker-compose up elasticsearch -d

# Wait for Elasticsearch to be ready
curl http://localhost:9200/_cluster/health
```

### 2. Initialize Indices

```bash
# Via API (requires authentication)
curl -X POST http://localhost:8000/api/v1/search/reindex \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "index_type=all"

# Or via Celery task
python -c "from app.tasks.search import initialize_indices; initialize_indices()"
```

### 3. Verify Indices

```bash
# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Check via API
curl http://localhost:8000/api/v1/search/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Endpoints

### Search Intelligence

**GET** `/api/v1/search/intelligence`

Search intelligence items with filters.

```bash
curl "http://localhost:8000/api/v1/search/intelligence?q=security+threat&region=Middle+East&min_threat=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Parameters:**
- `q` (required): Search query
- `source`: Filter by source
- `category`: Filter by category
- `region`: Filter by region
- `min_threat`: Minimum threat level (1-10)
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `from`: Pagination offset (default: 0)
- `size`: Results per page (max 100, default: 20)

**Response:**
```json
{
  "total": 42,
  "took_ms": 15,
  "results": [
    {
      "id": 123,
      "title": "Security Alert: Increased Threat Level",
      "content": "...",
      "source": "reuters",
      "region": "Middle East",
      "threat_level": 8,
      "score": 12.4,
      "highlights": {
        "title": ["<em>Security</em> Alert: Increased <em>Threat</em> Level"],
        "content": ["...increased <em>threat</em> level..."]
      }
    }
  ]
}
```

### Search All Types

**GET** `/api/v1/search/all`

Search across all data types (intelligence, incidents, alerts, personnel).

```bash
curl "http://localhost:8000/api/v1/search/all?q=emergency&size=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total": 128,
  "took_ms": 22,
  "results": [
    {
      "id": 45,
      "title": "Emergency Protocol Update",
      "index_type": "intelligence",
      "score": 15.2,
      "created_at": "2024-11-10T10:30:00Z"
    },
    {
      "id": 12,
      "title": "Emergency Evacuation - Region 5",
      "index_type": "incidents",
      "score": 13.8,
      "created_at": "2024-11-09T14:20:00Z"
    }
  ]
}
```

### Geospatial Search

**GET** `/api/v1/search/geospatial`

Find intelligence items near a location.

```bash
curl "http://localhost:8000/api/v1/search/geospatial?lat=33.888&lon=35.495&distance=50km&q=protest" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Parameters:**
- `lat`: Latitude (-90 to 90)
- `lon`: Longitude (-180 to 180)
- `distance`: Search radius (e.g., '50km', '30mi')
- `q`: Optional text query
- `from`, `size`: Pagination

**Example - Find all intelligence within 100km of Beirut:**
```bash
curl "http://localhost:8000/api/v1/search/geospatial?lat=33.888&lon=35.495&distance=100km" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Advanced Search

**POST** `/api/v1/search/advanced`

Complex search with multiple filters.

```bash
curl -X POST http://localhost:8000/api/v1/search/advanced \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "terrorist activity",
    "filters": {
      "source": "reuters",
      "min_threat_level": 7,
      "region": "Middle East",
      "date_from": "2024-10-01",
      "near_location": {
        "lat": 35.0,
        "lon": 40.0,
        "distance": "100km"
      }
    },
    "from_": 0,
    "size": 20
  }'
```

### Search Suggestions

**GET** `/api/v1/search/suggestions`

Get autocomplete suggestions.

```bash
curl "http://localhost:8000/api/v1/search/suggestions?prefix=secur" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "suggestions": [
    "security alert",
    "security breach",
    "security update",
    "security protocol"
  ]
}
```

### Trending Terms

**GET** `/api/v1/search/trending`

Get trending terms from recent intelligence.

```bash
curl "http://localhost:8000/api/v1/search/trending?days=7&size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "trending_terms": [
    {
      "term": "evacuation",
      "score": 45.2,
      "doc_count": 12
    },
    {
      "term": "protest",
      "score": 38.7,
      "doc_count": 15
    }
  ],
  "period_days": 7
}
```

### Field Aggregations

**GET** `/api/v1/search/aggregations/{index_type}/{field}`

Get aggregation counts for a field.

```bash
# Get top sources
curl "http://localhost:8000/api/v1/search/aggregations/intelligence/source?size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get threat level distribution
curl "http://localhost:8000/api/v1/search/aggregations/intelligence/threat_level" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "index_type": "intelligence",
  "field": "source",
  "aggregations": {
    "reuters": 245,
    "bbc": 189,
    "state_dept": 156,
    "un_ocha": 134
  }
}
```

## Search Query Syntax

### Basic Search

```
security threat          # Searches for both words
"security threat"        # Exact phrase
security OR threat       # Either word
security AND threat      # Both words required
security NOT military    # Exclude results with "military"
```

### Field-Specific Search

When using Elasticsearch directly:

```
title:security           # Search in title only
content:threat           # Search in content only
source:reuters           # Exact source match
threat_level:>=7         # Numeric range
```

### Wildcards and Fuzzy

```
secur*                   # Wildcard (security, secure, etc.)
security~                # Fuzzy match (allows typos)
```

## Indexing New Data

### Automatic Indexing

Intelligence items are automatically indexed when created:

```python
from app.tasks.search import index_new_intelligence

# After creating intelligence item
intelligence_id = 123
index_new_intelligence.delay(intelligence_id)
```

### Manual Reindexing

Trigger full reindex of specific data types:

```bash
# Reindex all intelligence
curl -X POST "http://localhost:8000/api/v1/search/reindex?index_type=intelligence" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Reindex everything
curl -X POST "http://localhost:8000/api/v1/search/reindex?index_type=all" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Bulk Indexing

For large datasets:

```python
from app.services.search_service import get_search_service

search_service = get_search_service()

# Bulk index intelligence items
intelligence_items = [
    {'id': 1, 'title': 'Item 1', 'content': '...'},
    {'id': 2, 'title': 'Item 2', 'content': '...'},
    # ... more items
]

search_service.bulk_index_intelligence(intelligence_items)
```

## Search Integration in Application

### Python Service Usage

```python
from app.services.search_service import get_search_service

search_service = get_search_service()

# Search intelligence
results = search_service.search_intelligence(
    query="security threat",
    filters={
        'region': 'Middle East',
        'min_threat_level': 7,
        'date_from': '2024-10-01'
    },
    from_=0,
    size=20
)

# Process results
for item in results['results']:
    print(f"Title: {item['title']}")
    print(f"Score: {item['score']}")
    print(f"Highlights: {item.get('highlights', {})}")
```

### Index New Intelligence

```python
# After creating intelligence item
intelligence_data = {
    'id': intelligence.id,
    'title': intelligence.title,
    'content': intelligence.content,
    'source': intelligence.source,
    'region': intelligence.region,
    'threat_level': intelligence.threat_level,
    'created_at': intelligence.created_at.isoformat()
}

search_service.index_intelligence(intelligence_data)
```

## Frontend Integration

### Search Component Example

```typescript
// React search component
const SearchResults = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const response = await fetch(
      `/api/v1/search/intelligence?q=${encodeURIComponent(query)}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    const data = await response.json();
    setResults(data.results);
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      {results.map(result => (
        <SearchResult key={result.id} data={result} />
      ))}
    </div>
  );
};
```

### Autocomplete Example

```typescript
const SearchAutocomplete = () => {
  const [prefix, setPrefix] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    if (prefix.length >= 2) {
      fetch(`/api/v1/search/suggestions?prefix=${prefix}`)
        .then(res => res.json())
        .then(data => setSuggestions(data.suggestions));
    }
  }, [prefix]);

  return (
    <div>
      <input value={prefix} onChange={(e) => setPrefix(e.target.value)} />
      <ul>
        {suggestions.map(s => <li key={s}>{s}</li>)}
      </ul>
    </div>
  );
};
```

## Performance Optimization

### Index Settings

Adjust in `app/services/search_service.py`:

```python
'settings': {
    'number_of_shards': 3,      # Distribute data
    'number_of_replicas': 1,    # Data redundancy
    'refresh_interval': '5s'    # Index refresh rate
}
```

### Query Optimization

1. **Use filters instead of queries for exact matches:**
   ```python
   filters = {'source': 'reuters'}  # Fast
   # vs
   query = 'source:reuters'  # Slower
   ```

2. **Limit result size:**
   ```python
   size=20  # Return only what's needed
   ```

3. **Use pagination:**
   ```python
   from_=0, size=20  # First page
   from_=20, size=20  # Second page
   ```

4. **Disable highlighting when not needed:**
   Remove `highlight` section from search body

### Caching

Cache frequent searches:

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def cache_search(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"search:{args}:{kwargs}"

            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute search
            result = func(*args, **kwargs)

            # Cache result
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator
```

## Troubleshooting

### Elasticsearch Not Starting

```bash
# Check logs
docker logs watchkeeper-elasticsearch

# Common issues:
# - Insufficient memory (increase ES_JAVA_OPTS)
# - Port conflict (change 9200 port mapping)
# - Disk space (check available space)
```

### Index Not Found

```bash
# Initialize indices
curl -X POST http://localhost:8000/api/v1/search/reindex?index_type=all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search Returns No Results

1. Check if data is indexed:
   ```bash
   curl http://localhost:9200/watchkeeper_intelligence/_count
   ```

2. Verify search query:
   ```bash
   # Test direct Elasticsearch query
   curl -X GET "http://localhost:9200/watchkeeper_intelligence/_search" \
     -H 'Content-Type: application/json' \
     -d '{"query": {"match": {"title": "security"}}}'
   ```

3. Check index mapping:
   ```bash
   curl http://localhost:9200/watchkeeper_intelligence/_mapping
   ```

### Slow Searches

1. Check query execution:
   ```bash
   # Use explain API
   curl -X GET "http://localhost:9200/watchkeeper_intelligence/_search" \
     -H 'Content-Type: application/json' \
     -d '{"query": {...}, "explain": true}'
   ```

2. Monitor Elasticsearch performance:
   ```bash
   # Check cluster health
   curl http://localhost:9200/_cluster/health

   # Check node stats
   curl http://localhost:9200/_nodes/stats
   ```

3. Optimize indices:
   ```bash
   # Force merge (consolidate segments)
   curl -X POST "http://localhost:9200/watchkeeper_intelligence/_forcemerge"
   ```

## Production Considerations

### High Availability

1. **Multiple Elasticsearch Nodes:**
   ```yaml
   # docker-compose.yml
   elasticsearch-node1:
     ...
   elasticsearch-node2:
     ...
   elasticsearch-node3:
     ...
   ```

2. **Increase Replicas:**
   ```python
   'number_of_replicas': 2  # For 3-node cluster
   ```

### Backup and Restore

```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/watchkeeper_backup" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/backup"
    }
  }'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/watchkeeper_backup/snapshot_1"

# Restore snapshot
curl -X POST "http://localhost:9200/_snapshot/watchkeeper_backup/snapshot_1/_restore"
```

### Security

1. **Enable Elasticsearch Security:**
   ```yaml
   environment:
     - xpack.security.enabled=true
     - ELASTIC_PASSWORD=your_secure_password
   ```

2. **Use API Key Authentication:**
   ```python
   es = Elasticsearch(
       ['https://localhost:9200'],
       api_key=('id', 'api_key'),
       verify_certs=True
   )
   ```

## Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [Query DSL Reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
