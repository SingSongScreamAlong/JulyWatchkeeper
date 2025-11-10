"""Elasticsearch Search Service

Provides advanced full-text search across all WATCHKEEPER data.
"""

from elasticsearch import Elasticsearch, helpers
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search using Elasticsearch"""

    def __init__(self):
        es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        es_port = int(os.getenv('ELASTICSEARCH_PORT', 9200))

        self.es = Elasticsearch(
            [{'host': es_host, 'port': es_port, 'scheme': 'http'}],
            timeout=30
        )

        self.indices = {
            'intelligence': 'watchkeeper_intelligence',
            'incidents': 'watchkeeper_incidents',
            'personnel': 'watchkeeper_personnel',
            'alerts': 'watchkeeper_alerts',
            'briefings': 'watchkeeper_briefings'
        }

    def initialize_indices(self):
        """Create Elasticsearch indices with mappings"""

        # Intelligence items index
        if not self.es.indices.exists(index=self.indices['intelligence']):
            self.es.indices.create(
                index=self.indices['intelligence'],
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'title': {
                                'type': 'text',
                                'fields': {'keyword': {'type': 'keyword'}}
                            },
                            'content': {'type': 'text'},
                            'source': {'type': 'keyword'},
                            'category': {'type': 'keyword'},
                            'region': {'type': 'keyword'},
                            'threat_level': {'type': 'integer'},
                            'missionary_relevance': {'type': 'integer'},
                            'sentiment': {'type': 'float'},
                            'collection_date': {'type': 'date'},
                            'created_at': {'type': 'date'},
                            'tags': {'type': 'keyword'},
                            'entities': {
                                'type': 'nested',
                                'properties': {
                                    'type': {'type': 'keyword'},
                                    'name': {'type': 'keyword'}
                                }
                            },
                            'location': {'type': 'geo_point'},
                            'keywords': {'type': 'keyword'}
                        }
                    },
                    'settings': {
                        'number_of_shards': 3,
                        'number_of_replicas': 1
                    }
                }
            )
            logger.info("Created intelligence index")

        # Incidents index
        if not self.es.indices.exists(index=self.indices['incidents']):
            self.es.indices.create(
                index=self.indices['incidents'],
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'title': {'type': 'text'},
                            'description': {'type': 'text'},
                            'incident_type': {'type': 'keyword'},
                            'severity': {'type': 'keyword'},
                            'status': {'type': 'keyword'},
                            'location': {'type': 'geo_point'},
                            'location_name': {'type': 'text'},
                            'reported_by': {'type': 'keyword'},
                            'affected_personnel': {'type': 'keyword'},
                            'incident_date': {'type': 'date'},
                            'created_at': {'type': 'date'},
                            'resolved_at': {'type': 'date'}
                        }
                    }
                }
            )
            logger.info("Created incidents index")

        # Personnel index
        if not self.es.indices.exists(index=self.indices['personnel']):
            self.es.indices.create(
                index=self.indices['personnel'],
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'text'},
                            'organization': {'type': 'keyword'},
                            'region': {'type': 'keyword'},
                            'status': {'type': 'keyword'},
                            'current_location': {'type': 'geo_point'},
                            'last_checkin': {'type': 'date'},
                            'emergency_contact': {'type': 'text'},
                            'skills': {'type': 'keyword'},
                            'languages': {'type': 'keyword'}
                        }
                    }
                }
            )
            logger.info("Created personnel index")

        # Alerts index
        if not self.es.indices.exists(index=self.indices['alerts']):
            self.es.indices.create(
                index=self.indices['alerts'],
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'title': {'type': 'text'},
                            'message': {'type': 'text'},
                            'severity': {'type': 'keyword'},
                            'type': {'type': 'keyword'},
                            'status': {'type': 'keyword'},
                            'target_personnel': {'type': 'keyword'},
                            'target_groups': {'type': 'keyword'},
                            'created_at': {'type': 'date'},
                            'acknowledged_at': {'type': 'date'}
                        }
                    }
                }
            )
            logger.info("Created alerts index")

        # Briefings index
        if not self.es.indices.exists(index=self.indices['briefings']):
            self.es.indices.create(
                index=self.indices['briefings'],
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'title': {'type': 'text'},
                            'content': {'type': 'text'},
                            'region': {'type': 'keyword'},
                            'date': {'type': 'date'},
                            'threat_summary': {'type': 'text'},
                            'recommendations': {'type': 'text'}
                        }
                    }
                }
            )
            logger.info("Created briefings index")

    def index_intelligence(self, intelligence: Dict[str, Any]):
        """Index intelligence item"""
        try:
            doc = {
                'id': intelligence['id'],
                'title': intelligence['title'],
                'content': intelligence['content'],
                'source': intelligence.get('source', 'unknown'),
                'category': intelligence.get('category', 'general'),
                'region': intelligence.get('region'),
                'threat_level': intelligence.get('threat_level', 0),
                'missionary_relevance': intelligence.get('missionary_relevance', 0),
                'sentiment': intelligence.get('sentiment'),
                'collection_date': intelligence.get('collection_date'),
                'created_at': intelligence.get('created_at'),
                'tags': intelligence.get('tags', []),
                'keywords': intelligence.get('keywords', [])
            }

            # Add location if available
            if intelligence.get('latitude') and intelligence.get('longitude'):
                doc['location'] = {
                    'lat': intelligence['latitude'],
                    'lon': intelligence['longitude']
                }

            self.es.index(
                index=self.indices['intelligence'],
                id=intelligence['id'],
                body=doc
            )

            logger.debug(f"Indexed intelligence item {intelligence['id']}")

        except Exception as e:
            logger.error(f"Error indexing intelligence: {e}")

    def bulk_index_intelligence(self, intelligence_items: List[Dict]):
        """Bulk index multiple intelligence items"""
        actions = []

        for item in intelligence_items:
            doc = {
                '_index': self.indices['intelligence'],
                '_id': item['id'],
                '_source': {
                    'id': item['id'],
                    'title': item['title'],
                    'content': item['content'],
                    'source': item.get('source', 'unknown'),
                    'category': item.get('category', 'general'),
                    'region': item.get('region'),
                    'threat_level': item.get('threat_level', 0),
                    'missionary_relevance': item.get('missionary_relevance', 0),
                    'created_at': item.get('created_at')
                }
            }

            if item.get('latitude') and item.get('longitude'):
                doc['_source']['location'] = {
                    'lat': item['latitude'],
                    'lon': item['longitude']
                }

            actions.append(doc)

        try:
            helpers.bulk(self.es, actions)
            logger.info(f"Bulk indexed {len(actions)} intelligence items")
        except Exception as e:
            logger.error(f"Error bulk indexing: {e}")

    def search_intelligence(
        self,
        query: str,
        filters: Optional[Dict] = None,
        from_: int = 0,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search intelligence items"""

        must_clauses = []

        # Full-text search across title and content
        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': ['title^3', 'content', 'keywords^2'],
                    'type': 'best_fields',
                    'fuzziness': 'AUTO'
                }
            })

        # Apply filters
        filter_clauses = []

        if filters:
            if filters.get('source'):
                filter_clauses.append({'term': {'source': filters['source']}})

            if filters.get('category'):
                filter_clauses.append({'term': {'category': filters['category']}})

            if filters.get('region'):
                filter_clauses.append({'term': {'region': filters['region']}})

            if filters.get('min_threat_level'):
                filter_clauses.append({
                    'range': {'threat_level': {'gte': filters['min_threat_level']}}
                })

            if filters.get('date_from'):
                filter_clauses.append({
                    'range': {'collection_date': {'gte': filters['date_from']}}
                })

            if filters.get('date_to'):
                filter_clauses.append({
                    'range': {'collection_date': {'lte': filters['date_to']}}
                })

            # Geospatial search
            if filters.get('near_location'):
                lat = filters['near_location']['lat']
                lon = filters['near_location']['lon']
                distance = filters['near_location'].get('distance', '50km')

                filter_clauses.append({
                    'geo_distance': {
                        'distance': distance,
                        'location': {'lat': lat, 'lon': lon}
                    }
                })

        search_body = {
            'query': {
                'bool': {
                    'must': must_clauses if must_clauses else [{'match_all': {}}],
                    'filter': filter_clauses
                }
            },
            'from': from_,
            'size': size,
            'sort': [
                {'_score': {'order': 'desc'}},
                {'created_at': {'order': 'desc'}}
            ],
            'highlight': {
                'fields': {
                    'title': {},
                    'content': {'fragment_size': 150, 'number_of_fragments': 3}
                }
            }
        }

        try:
            response = self.es.search(
                index=self.indices['intelligence'],
                body=search_body
            )

            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']

                if 'highlight' in hit:
                    result['highlights'] = hit['highlight']

                results.append(result)

            return {
                'total': response['hits']['total']['value'],
                'results': results,
                'took_ms': response['took']
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'total': 0, 'results': [], 'error': str(e)}

    def search_all(
        self,
        query: str,
        from_: int = 0,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search across all indices"""

        indices_list = ','.join(self.indices.values())

        search_body = {
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^3', 'content', 'description', 'message'],
                    'type': 'best_fields',
                    'fuzziness': 'AUTO'
                }
            },
            'from': from_,
            'size': size,
            'sort': [
                {'_score': {'order': 'desc'}},
                {'created_at': {'order': 'desc', 'unmapped_type': 'date'}}
            ]
        }

        try:
            response = self.es.search(index=indices_list, body=search_body)

            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                result['index_type'] = hit['_index'].replace('watchkeeper_', '')
                results.append(result)

            return {
                'total': response['hits']['total']['value'],
                'results': results,
                'took_ms': response['took']
            }

        except Exception as e:
            logger.error(f"Multi-index search error: {e}")
            return {'total': 0, 'results': [], 'error': str(e)}

    def get_suggestions(self, prefix: str, field: str = 'title') -> List[str]:
        """Get search suggestions"""

        search_body = {
            'suggest': {
                'suggestions': {
                    'prefix': prefix,
                    'completion': {
                        'field': f'{field}.suggest',
                        'size': 10,
                        'skip_duplicates': True
                    }
                }
            }
        }

        try:
            response = self.es.search(
                index=self.indices['intelligence'],
                body=search_body
            )

            suggestions = []
            for option in response['suggest']['suggestions'][0]['options']:
                suggestions.append(option['text'])

            return suggestions

        except Exception as e:
            logger.error(f"Suggestions error: {e}")
            return []

    def aggregate_by_field(
        self,
        index_name: str,
        field: str,
        size: int = 10
    ) -> Dict[str, int]:
        """Get aggregation counts for a field"""

        search_body = {
            'size': 0,
            'aggs': {
                'field_counts': {
                    'terms': {
                        'field': field,
                        'size': size
                    }
                }
            }
        }

        try:
            response = self.es.search(
                index=self.indices[index_name],
                body=search_body
            )

            buckets = response['aggregations']['field_counts']['buckets']
            return {bucket['key']: bucket['doc_count'] for bucket in buckets}

        except Exception as e:
            logger.error(f"Aggregation error: {e}")
            return {}

    def get_trending_terms(self, days: int = 7, size: int = 10) -> List[Dict]:
        """Get trending search terms from recent intelligence"""

        search_body = {
            'size': 0,
            'query': {
                'range': {
                    'created_at': {
                        'gte': f'now-{days}d'
                    }
                }
            },
            'aggs': {
                'trending_terms': {
                    'significant_text': {
                        'field': 'content',
                        'size': size
                    }
                }
            }
        }

        try:
            response = self.es.search(
                index=self.indices['intelligence'],
                body=search_body
            )

            terms = []
            for bucket in response['aggregations']['trending_terms']['buckets']:
                terms.append({
                    'term': bucket['key'],
                    'score': bucket['score'],
                    'doc_count': bucket['doc_count']
                })

            return terms

        except Exception as e:
            logger.error(f"Trending terms error: {e}")
            return []

    def delete_document(self, index_type: str, doc_id: int):
        """Delete document from index"""
        try:
            self.es.delete(index=self.indices[index_type], id=doc_id)
            logger.info(f"Deleted document {doc_id} from {index_type}")
        except Exception as e:
            logger.error(f"Delete error: {e}")


# Singleton instance
_search_service = None


def get_search_service() -> SearchService:
    """Get singleton search service instance"""
    global _search_service

    if _search_service is None:
        _search_service = SearchService()

    return _search_service
