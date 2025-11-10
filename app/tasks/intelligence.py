"""Intelligence collection and processing tasks"""

from ..celery_app import celery_app
from ..database import SessionLocal
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.intelligence.collect_all_sources')
def collect_all_sources():
    """Collect intelligence from all configured sources"""
    db = SessionLocal()
    try:
        # Load sources from comprehensive_sources.json
        sources_file = Path(__file__).parent.parent.parent / 'config' / 'comprehensive_sources.json'

        with open(sources_file, 'r') as f:
            sources_config = json.load(f)

        sources = sources_config.get('sources', [])
        enabled_sources = [s for s in sources if s.get('enabled', False)]

        logger.info(f"Starting intelligence collection from {len(enabled_sources)} sources")

        collected = []
        errors = []

        for source in enabled_sources:
            try:
                # Dispatch to appropriate collector based on type
                if source['type'] == 'rss':
                    result = collect_rss_source.delay(source['id'])
                    collected.append(source['name'])
                elif source['type'] == 'api':
                    if not source.get('requires_api_key', False):
                        result = collect_api_source.delay(source['id'])
                        collected.append(source['name'])
                elif source['type'] == 'web':
                    result = collect_web_source.delay(source['id'])
                    collected.append(source['name'])

            except Exception as e:
                logger.error(f"Error collecting from {source['name']}: {e}")
                errors.append({'source': source['name'], 'error': str(e)})

        return {
            'success': True,
            'sources_processed': len(collected),
            'collected_from': collected,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Error in collect_all_sources: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.intelligence.collect_rss_source')
def collect_rss_source(source_id: int):
    """Collect intelligence from an RSS source"""
    db = SessionLocal()
    try:
        import feedparser
        from datetime import datetime

        # Load source config
        sources_file = Path(__file__).parent.parent.parent / 'config' / 'comprehensive_sources.json'
        with open(sources_file, 'r') as f:
            sources_config = json.load(f)

        source = next((s for s in sources_config['sources'] if s['id'] == source_id), None)
        if not source:
            return {'success': False, 'error': 'Source not found'}

        logger.info(f"Collecting from RSS source: {source['name']}")

        # Parse RSS feed
        feed = feedparser.parse(source['url'])

        items_collected = 0

        for entry in feed.entries[:10]:  # Limit to 10 most recent
            from ..models.intelligence import IntelligenceItem

            # Check if already exists
            existing = db.query(IntelligenceItem).filter(
                IntelligenceItem.url == entry.link
            ).first()

            if existing:
                continue

            # Create intelligence item
            intel = IntelligenceItem(
                title=entry.get('title', 'No title'),
                content=entry.get('summary', entry.get('description', '')),
                summary=entry.get('summary', '')[:500] if entry.get('summary') else '',
                source=source['name'],
                source_id=source_id,
                raw_content=str(entry),
                url=entry.get('link', ''),
                collection_date=datetime.utcnow().isoformat(),
                publication_date=entry.get('published', datetime.utcnow().isoformat()),
                threat_level=0.0,  # Will be analyzed later
                missionary_relevance=0.0,  # Will be analyzed later
                region=source.get('regions', ['global'])[0] if source.get('regions') else 'global',
                confidence=float(source.get('reliability', 5)) / 10.0
            )

            db.add(intel)
            items_collected += 1

        db.commit()

        logger.info(f"Collected {items_collected} new items from {source['name']}")

        return {
            'success': True,
            'source': source['name'],
            'items_collected': items_collected
        }

    except Exception as e:
        logger.error(f"Error collecting RSS source {source_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.intelligence.collect_api_source')
def collect_api_source(source_id: int):
    """Collect intelligence from an API source"""
    db = SessionLocal()
    try:
        # Placeholder for API collection
        logger.info(f"Collecting from API source: {source_id}")
        # TODO: Implement API-specific collection logic

        return {
            'success': True,
            'source_id': source_id,
            'items_collected': 0,
            'note': 'API collection not yet implemented'
        }

    except Exception as e:
        logger.error(f"Error collecting API source {source_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.intelligence.collect_web_source')
def collect_web_source(source_id: int):
    """Collect intelligence from a web source"""
    db = SessionLocal()
    try:
        # Placeholder for web scraping
        logger.info(f"Collecting from web source: {source_id}")
        # TODO: Implement web scraping logic

        return {
            'success': True,
            'source_id': source_id,
            'items_collected': 0,
            'note': 'Web collection not yet implemented'
        }

    except Exception as e:
        logger.error(f"Error collecting web source {source_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.intelligence.generate_daily_briefing')
def generate_daily_briefing():
    """Generate daily intelligence briefing"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from ..models.intelligence import IntelligenceItem

        logger.info("Generating daily intelligence briefing")

        # Get intelligence from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)

        recent_intel = db.query(IntelligenceItem).filter(
            IntelligenceItem.created_at >= yesterday
        ).order_by(IntelligenceItem.threat_level.desc()).limit(20).all()

        # Calculate statistics
        high_threat_count = sum(1 for i in recent_intel if i.threat_level >= 8)
        avg_threat = sum(i.threat_level for i in recent_intel) / len(recent_intel) if recent_intel else 0

        # Generate briefing content
        briefing_content = f"""
WATCHKEEPER DAILY INTELLIGENCE BRIEFING
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

SUMMARY
-------
Total Intelligence Items (24h): {len(recent_intel)}
High Threat Items (≥8): {high_threat_count}
Average Threat Level: {avg_threat:.1f}/10

TOP THREATS
-----------
"""

        for idx, intel in enumerate(recent_intel[:5], 1):
            briefing_content += f"""
{idx}. {intel.title}
   Threat: {intel.threat_level}/10 | Region: {intel.region or 'Unknown'}
   Source: {intel.source}
   {intel.summary[:200]}...

"""

        # Save briefing
        from ..models.briefings import IntelligenceBriefing

        briefing = IntelligenceBriefing(
            briefing_type='daily',
            title=f"Daily Intelligence Briefing - {datetime.utcnow().strftime('%Y-%m-%d')}",
            summary=f"{len(recent_intel)} items, {high_threat_count} high-threat",
            full_content=briefing_content,
            format='text',
            priority=7 if high_threat_count > 0 else 5,
            time_period_start=yesterday,
            time_period_end=datetime.utcnow(),
            intelligence_items_included=[i.id for i in recent_intel],
            generated_by='auto',
            published=True,
            publish_date=datetime.utcnow()
        )

        db.add(briefing)
        db.commit()

        logger.info(f"Daily briefing generated: {briefing.id}")

        return {
            'success': True,
            'briefing_id': briefing.id,
            'items_included': len(recent_intel),
            'high_threat_count': high_threat_count
        }

    except Exception as e:
        logger.error(f"Error generating daily briefing: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.intelligence.analyze_intelligence_item')
def analyze_intelligence_item(intelligence_id: int):
    """Analyze intelligence item for threat level and missionary relevance"""
    db = SessionLocal()
    try:
        from ..models.intelligence import IntelligenceItem
        import re

        intel = db.query(IntelligenceItem).filter(
            IntelligenceItem.id == intelligence_id
        ).first()

        if not intel:
            return {'success': False, 'error': 'Intelligence item not found'}

        # Simple keyword-based threat assessment
        threat_keywords = {
            'critical': ['kill', 'attack', 'bomb', 'terror', 'massacre', 'kidnap'],
            'high': ['arrest', 'detained', 'violence', 'persecution', 'raid', 'assault'],
            'medium': ['protest', 'unrest', 'warning', 'tension', 'conflict'],
            'low': ['concern', 'monitor', 'watch', 'caution']
        }

        missionary_keywords = [
            'missionary', 'christian', 'church', 'religious', 'faith',
            'evangel', 'ministry', 'pastor', 'worship', 'bible'
        ]

        content_lower = (intel.title + ' ' + intel.content).lower()

        # Calculate threat level
        threat_score = 0.0
        if any(kw in content_lower for kw in threat_keywords['critical']):
            threat_score = 9.0
        elif any(kw in content_lower for kw in threat_keywords['high']):
            threat_score = 7.5
        elif any(kw in content_lower for kw in threat_keywords['medium']):
            threat_score = 5.0
        elif any(kw in content_lower for kw in threat_keywords['low']):
            threat_score = 3.0
        else:
            threat_score = 1.0

        # Calculate missionary relevance
        relevance_score = sum(1 for kw in missionary_keywords if kw in content_lower)
        relevance_score = min(10.0, relevance_score * 2.0)

        # Update intelligence item
        intel.threat_level = threat_score
        intel.missionary_relevance = relevance_score

        db.commit()

        logger.info(
            f"Analyzed intelligence {intelligence_id}: "
            f"Threat={threat_score}, Relevance={relevance_score}"
        )

        # Trigger alert evaluation if high threat/relevance
        if threat_score >= 7.0 or relevance_score >= 7.0:
            from ..tasks.alerts import evaluate_intelligence_for_alerts
            evaluate_intelligence_for_alerts.delay(intelligence_id)

        return {
            'success': True,
            'intelligence_id': intelligence_id,
            'threat_level': threat_score,
            'missionary_relevance': relevance_score
        }

    except Exception as e:
        logger.error(f"Error analyzing intelligence {intelligence_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
