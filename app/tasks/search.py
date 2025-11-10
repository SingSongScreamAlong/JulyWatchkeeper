"""Search Indexing Tasks

Background tasks for maintaining Elasticsearch indices.
"""

from celery import Task
from ..celery_app import celery_app
from ..services.search_service import get_search_service
from ..database import SessionLocal
from ..models.intelligence import IntelligenceItem
from ..models.incident import FieldIncident
from ..models.alert import Alert
from ..models.personnel import Personnel
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.search.reindex_intelligence')
def reindex_intelligence():
    """Reindex all intelligence items"""
    logger.info("Starting intelligence reindexing")

    db = SessionLocal()
    search_service = get_search_service()

    try:
        # Get all intelligence items
        intelligence_items = db.query(IntelligenceItem).all()

        # Convert to dicts
        items_data = []
        for item in intelligence_items:
            items_data.append({
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'source': item.source,
                'category': item.category,
                'region': item.region,
                'threat_level': item.threat_level,
                'missionary_relevance': item.missionary_relevance,
                'sentiment': item.sentiment,
                'collection_date': item.collection_date.isoformat() if item.collection_date else None,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'latitude': item.latitude,
                'longitude': item.longitude,
                'tags': item.tags or [],
                'keywords': []
            })

        # Bulk index
        search_service.bulk_index_intelligence(items_data)

        logger.info(f"Reindexed {len(items_data)} intelligence items")

        return {
            'status': 'success',
            'items_indexed': len(items_data)
        }

    except Exception as e:
        logger.error(f"Error reindexing intelligence: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.search.reindex_incidents')
def reindex_incidents():
    """Reindex all incidents"""
    logger.info("Starting incidents reindexing")

    db = SessionLocal()
    search_service = get_search_service()

    try:
        incidents = db.query(FieldIncident).all()

        for incident in incidents:
            doc = {
                'id': incident.id,
                'title': incident.title,
                'description': incident.description,
                'incident_type': incident.incident_type,
                'severity': incident.severity,
                'status': incident.status,
                'location_name': incident.location_name,
                'reported_by': incident.reported_by,
                'incident_date': incident.incident_date.isoformat() if incident.incident_date else None,
                'created_at': incident.created_at.isoformat() if incident.created_at else None,
                'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None
            }

            if incident.latitude and incident.longitude:
                doc['location'] = {
                    'lat': incident.latitude,
                    'lon': incident.longitude
                }

            search_service.es.index(
                index=search_service.indices['incidents'],
                id=incident.id,
                body=doc
            )

        logger.info(f"Reindexed {len(incidents)} incidents")

        return {
            'status': 'success',
            'items_indexed': len(incidents)
        }

    except Exception as e:
        logger.error(f"Error reindexing incidents: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.search.reindex_alerts')
def reindex_alerts():
    """Reindex all alerts"""
    logger.info("Starting alerts reindexing")

    db = SessionLocal()
    search_service = get_search_service()

    try:
        alerts = db.query(Alert).all()

        for alert in alerts:
            doc = {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity,
                'type': alert.type,
                'status': alert.status,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            }

            search_service.es.index(
                index=search_service.indices['alerts'],
                id=alert.id,
                body=doc
            )

        logger.info(f"Reindexed {len(alerts)} alerts")

        return {
            'status': 'success',
            'items_indexed': len(alerts)
        }

    except Exception as e:
        logger.error(f"Error reindexing alerts: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.search.reindex_personnel')
def reindex_personnel():
    """Reindex all personnel"""
    logger.info("Starting personnel reindexing")

    db = SessionLocal()
    search_service = get_search_service()

    try:
        personnel = db.query(Personnel).all()

        for person in personnel:
            doc = {
                'id': person.id,
                'name': person.name,
                'organization': person.organization,
                'region': person.region,
                'status': person.status,
                'last_checkin': person.last_checkin.isoformat() if person.last_checkin else None
            }

            if person.current_latitude and person.current_longitude:
                doc['current_location'] = {
                    'lat': person.current_latitude,
                    'lon': person.current_longitude
                }

            search_service.es.index(
                index=search_service.indices['personnel'],
                id=person.id,
                body=doc
            )

        logger.info(f"Reindexed {len(personnel)} personnel")

        return {
            'status': 'success',
            'items_indexed': len(personnel)
        }

    except Exception as e:
        logger.error(f"Error reindexing personnel: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.search.reindex_all')
def reindex_all():
    """Reindex all data types"""
    logger.info("Starting full reindex")

    results = {}

    # Reindex each type
    results['intelligence'] = reindex_intelligence()
    results['incidents'] = reindex_incidents()
    results['alerts'] = reindex_alerts()
    results['personnel'] = reindex_personnel()

    # Calculate totals
    total_indexed = sum(
        r.get('items_indexed', 0)
        for r in results.values()
        if r.get('status') == 'success'
    )

    errors = [
        f"{k}: {v.get('error')}"
        for k, v in results.items()
        if v.get('status') == 'error'
    ]

    logger.info(f"Full reindex completed. Total indexed: {total_indexed}")

    return {
        'status': 'completed',
        'total_indexed': total_indexed,
        'details': results,
        'errors': errors if errors else None
    }


@celery_app.task(name='app.tasks.search.index_new_intelligence')
def index_new_intelligence(intelligence_id: int):
    """Index a single new intelligence item"""
    db = SessionLocal()
    search_service = get_search_service()

    try:
        item = db.query(IntelligenceItem).filter_by(id=intelligence_id).first()

        if not item:
            logger.warning(f"Intelligence item {intelligence_id} not found")
            return {'status': 'not_found'}

        item_data = {
            'id': item.id,
            'title': item.title,
            'content': item.content,
            'source': item.source,
            'category': item.category,
            'region': item.region,
            'threat_level': item.threat_level,
            'missionary_relevance': item.missionary_relevance,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'latitude': item.latitude,
            'longitude': item.longitude
        }

        search_service.index_intelligence(item_data)

        logger.info(f"Indexed new intelligence item {intelligence_id}")

        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error indexing intelligence {intelligence_id}: {e}")
        return {'status': 'error', 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.search.initialize_indices')
def initialize_indices():
    """Initialize all Elasticsearch indices"""
    logger.info("Initializing Elasticsearch indices")

    search_service = get_search_service()

    try:
        search_service.initialize_indices()

        logger.info("Elasticsearch indices initialized")

        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error initializing indices: {e}")
        return {'status': 'error', 'error': str(e)}
