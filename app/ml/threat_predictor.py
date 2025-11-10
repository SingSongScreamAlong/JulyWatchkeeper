"""ML-Based Threat Prediction

Uses machine learning to predict threat escalation and identify patterns.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ThreatPredictor:
    """ML-based threat prediction and analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.model = None

    def train_model(self, region: Optional[str] = None):
        """Train threat prediction model on historical data"""
        from ..models.intelligence import IntelligenceItem

        logger.info(f"Training threat prediction model for region: {region or 'global'}")

        # Get historical intelligence data
        query = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.threat_level > 0
        )

        if region:
            query = query.filter(IntelligenceItem.region == region)

        intelligence_items = query.order_by(IntelligenceItem.collection_date).all()

        if len(intelligence_items) < 50:
            logger.warning("Insufficient data for training (<50 items)")
            return {
                'success': False,
                'error': 'Insufficient training data',
                'items_found': len(intelligence_items)
            }

        # Prepare training data
        X, y = self._prepare_training_data(intelligence_items)

        # Train simple model (in production, use more sophisticated models)
        try:
            from sklearn.ensemble import RandomForestRegressor

            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

            self.model.fit(X, y)

            logger.info(f"Model trained on {len(X)} samples")

            return {
                'success': True,
                'samples': len(X),
                'region': region,
                'model_type': 'RandomForestRegressor'
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _prepare_training_data(self, intelligence_items: List) -> tuple:
        """Prepare data for ML training"""
        X = []
        y = []

        for item in intelligence_items:
            features = self._extract_features(item)
            X.append(features)
            y.append(item.threat_level)

        return np.array(X), np.array(y)

    def _extract_features(self, intel) -> List[float]:
        """Extract features from intelligence item"""
        features = []

        # Feature 1-2: Time-based features
        if intel.collection_date:
            dt = datetime.fromisoformat(intel.collection_date) if isinstance(intel.collection_date, str) else intel.collection_date
            features.append(dt.hour)  # Hour of day
            features.append(dt.weekday())  # Day of week
        else:
            features.extend([0, 0])

        # Feature 3: Missionary relevance
        features.append(intel.missionary_relevance)

        # Feature 4: Sentiment
        features.append(intel.sentiment if intel.sentiment else 0)

        # Feature 5: Confidence
        features.append(intel.confidence if intel.confidence else 0.5)

        # Feature 6-10: Keyword-based features
        content_lower = (intel.title + ' ' + intel.content).lower()
        features.append(1 if 'violence' in content_lower else 0)
        features.append(1 if 'attack' in content_lower else 0)
        features.append(1 if 'protest' in content_lower else 0)
        features.append(1 if 'arrest' in content_lower else 0)
        features.append(1 if 'killed' in content_lower else 0)

        return features

    def predict_threat_escalation(
        self,
        region: str,
        timeframe_days: int = 7
    ) -> Dict[str, Any]:
        """Predict threat escalation for a region"""
        from ..models.intelligence import IntelligenceItem

        # Get recent intelligence for the region
        recent_cutoff = datetime.utcnow() - timedelta(days=30)

        recent_intel = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.region == region,
            IntelligenceItem.created_at >= recent_cutoff
        ).all()

        if not recent_intel:
            return {
                'region': region,
                'prediction': 'insufficient_data',
                'confidence': 0.0
            }

        # Calculate trend
        threat_levels = [intel.threat_level for intel in recent_intel]
        avg_threat = sum(threat_levels) / len(threat_levels)

        # Simple trend analysis
        recent_5 = threat_levels[-5:] if len(threat_levels) >= 5 else threat_levels
        older_5 = threat_levels[-10:-5] if len(threat_levels) >= 10 else threat_levels[:5]

        recent_avg = sum(recent_5) / len(recent_5) if recent_5 else 0
        older_avg = sum(older_5) / len(older_5) if older_5 else 0

        trend = recent_avg - older_avg

        # Predict
        if trend > 1.0:
            prediction = 'escalating'
            predicted_level = min(10.0, avg_threat + trend)
        elif trend < -1.0:
            prediction = 'de-escalating'
            predicted_level = max(1.0, avg_threat + trend)
        else:
            prediction = 'stable'
            predicted_level = avg_threat

        return {
            'region': region,
            'current_avg_threat': round(avg_threat, 2),
            'trend': round(trend, 2),
            'prediction': prediction,
            'predicted_threat_level': round(predicted_level, 2),
            'timeframe_days': timeframe_days,
            'confidence': 0.7,  # Simplified confidence
            'sample_size': len(recent_intel),
            'timestamp': datetime.utcnow().isoformat()
        }

    def detect_anomalies(
        self,
        region: Optional[str] = None,
        threshold: float = 2.0
    ) -> List[Dict]:
        """Detect anomalous intelligence items"""
        from ..models.intelligence import IntelligenceItem

        recent_cutoff = datetime.utcnow() - timedelta(days=14)

        query = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.created_at >= recent_cutoff
        )

        if region:
            query = query.filter(IntelligenceItem.region == region)

        intelligence_items = query.all()

        if len(intelligence_items) < 10:
            return []

        # Calculate statistics
        threat_levels = [intel.threat_level for intel in intelligence_items]
        mean = np.mean(threat_levels)
        std = np.std(threat_levels)

        # Find anomalies (items beyond threshold standard deviations)
        anomalies = []

        for intel in intelligence_items:
            z_score = (intel.threat_level - mean) / std if std > 0 else 0

            if abs(z_score) > threshold:
                anomalies.append({
                    'intelligence_id': intel.id,
                    'title': intel.title,
                    'threat_level': intel.threat_level,
                    'z_score': round(z_score, 2),
                    'region': intel.region,
                    'anomaly_type': 'high' if z_score > 0 else 'low',
                    'date': intel.collection_date
                })

        # Sort by z_score
        anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)

        return anomalies

    def forecast_regional_risk(
        self,
        region: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Forecast regional risk over time"""
        from ..models.intelligence import IntelligenceItem

        # Get historical data
        historical_cutoff = datetime.utcnow() - timedelta(days=90)

        historical_intel = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.region == region,
            IntelligenceItem.created_at >= historical_cutoff
        ).order_by(IntelligenceItem.created_at).all()

        if len(historical_intel) < 20:
            return {
                'region': region,
                'forecast': 'insufficient_data',
                'confidence': 0.0
            }

        # Group by week and calculate average threat
        weekly_threats = {}

        for intel in historical_intel:
            if isinstance(intel.created_at, str):
                dt = datetime.fromisoformat(intel.created_at)
            else:
                dt = intel.created_at

            week = dt.strftime('%Y-W%W')

            if week not in weekly_threats:
                weekly_threats[week] = []

            weekly_threats[week].append(intel.threat_level)

        # Calculate weekly averages
        weekly_avgs = {
            week: sum(threats) / len(threats)
            for week, threats in weekly_threats.items()
        }

        # Simple linear trend
        weeks = list(weekly_avgs.keys())
        values = list(weekly_avgs.values())

        if len(values) >= 3:
            # Calculate trend
            recent_avg = sum(values[-3:]) / 3
            earlier_avg = sum(values[:3]) / 3
            trend = (recent_avg - earlier_avg) / len(values)

            # Forecast
            current_level = values[-1]
            forecasted_levels = []

            for i in range(1, days + 1):
                forecasted_level = current_level + (trend * i / 7)  # Weekly trend
                forecasted_levels.append({
                    'day': i,
                    'forecasted_threat': round(max(0, min(10, forecasted_level)), 2)
                })

            return {
                'region': region,
                'current_threat_level': round(current_level, 2),
                'trend': 'increasing' if trend > 0 else 'decreasing',
                'forecast_days': days,
                'forecast': forecasted_levels,
                'confidence': 0.6,
                'based_on_weeks': len(weekly_avgs)
            }

        return {
            'region': region,
            'forecast': 'insufficient_historical_data',
            'confidence': 0.0
        }
