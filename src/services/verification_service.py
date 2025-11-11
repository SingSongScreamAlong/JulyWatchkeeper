"""
Source Verification and Consensus Service for WATCHKEEPER

This service handles multi-source verification and consensus analysis.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging

from src.models.intelligence import Intelligence
from src.models.source import Source
from src.models.threat import Threat

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for source verification and consensus analysis."""

    @staticmethod
    async def calculate_source_reliability(
        db: AsyncSession,
        source_id: int
    ) -> float:
        """
        Calculate reliability score for a source based on its history.

        Args:
            db: Database session
            source_id: ID of the source

        Returns:
            Reliability score (0.0 to 1.0)
        """
        # Get intelligence items from this source
        result = await db.execute(
            select(Intelligence).where(
                and_(
                    Intelligence.source_id == source_id,
                    Intelligence.processed_at.isnot(None)
                )
            ).limit(100)
        )
        items = result.scalars().all()

        if not items:
            return 0.5  # Default neutral score

        # Calculate metrics
        total_items = len(items)
        high_confidence_items = sum(1 for item in items if item.confidence_score and item.confidence_score >= 0.7)
        avg_confidence = sum(item.confidence_score or 0 for item in items) / total_items

        # Weight: 60% from average confidence, 40% from proportion of high-confidence items
        reliability = (avg_confidence * 0.6) + ((high_confidence_items / total_items) * 0.4)

        return round(reliability, 3)

    @staticmethod
    async def find_consensus(
        db: AsyncSession,
        intelligence_id: int,
        similarity_threshold: float = 0.7,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Find consensus among multiple sources for an intelligence item.

        Args:
            db: Database session
            intelligence_id: ID of the intelligence item to verify
            similarity_threshold: Threshold for considering items similar
            time_window_hours: Time window to look for similar items

        Returns:
            Dict with consensus information
        """
        # Get the target intelligence item
        result = await db.execute(
            select(Intelligence).where(Intelligence.id == intelligence_id)
        )
        target_item = result.scalar_one_or_none()

        if not target_item:
            return {"error": "Intelligence item not found"}

        # Get similar items within time window
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)

        result = await db.execute(
            select(Intelligence).where(
                and_(
                    Intelligence.id != intelligence_id,
                    Intelligence.created_at >= time_threshold,
                    Intelligence.source_id != target_item.source_id  # Different source
                )
            )
        )
        potential_matches = result.scalars().all()

        # Simple similarity check (could be enhanced with NLP)
        similar_items = []
        for item in potential_matches:
            similarity = VerificationService._calculate_text_similarity(
                target_item.processed_content or target_item.raw_content,
                item.processed_content or item.raw_content
            )

            if similarity >= similarity_threshold:
                similar_items.append({
                    "intelligence_id": item.id,
                    "source_id": item.source_id,
                    "similarity": similarity,
                    "created_at": item.created_at
                })

        # Calculate consensus metrics
        source_count = len(set(item["source_id"] for item in similar_items)) + 1  # +1 for original
        avg_similarity = sum(item["similarity"] for item in similar_items) / len(similar_items) if similar_items else 0

        # Consensus strength based on number of sources and similarity
        consensus_strength = min(1.0, (source_count / 3) * 0.5 + avg_similarity * 0.5)

        return {
            "intelligence_id": intelligence_id,
            "confirming_sources": source_count,
            "similar_items": similar_items,
            "average_similarity": round(avg_similarity, 3),
            "consensus_strength": round(consensus_strength, 3),
            "verified": consensus_strength >= 0.7
        }

    @staticmethod
    def _calculate_text_similarity(text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using word overlap.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Simple word-based similarity (Jaccard index)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    async def verify_threat_with_multiple_sources(
        db: AsyncSession,
        threat_id: int
    ) -> Dict[str, Any]:
        """
        Verify a threat using multiple intelligence sources.

        Args:
            db: Database session
            threat_id: ID of the threat to verify

        Returns:
            Verification result with confidence and source count
        """
        # Get all intelligence items related to this threat
        result = await db.execute(
            select(Intelligence).where(Intelligence.threat_id == threat_id)
        )
        intelligence_items = result.scalars().all()

        if not intelligence_items:
            return {
                "threat_id": threat_id,
                "verified": False,
                "reason": "No intelligence items found"
            }

        # Get unique sources
        source_ids = set(item.source_id for item in intelligence_items)

        # Get source reliability scores
        source_scores = []
        for source_id in source_ids:
            result = await db.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            if source:
                source_scores.append(source.reliability_score or 0.5)

        # Calculate overall verification score
        avg_source_reliability = sum(source_scores) / len(source_scores) if source_scores else 0.5
        source_diversity_score = min(1.0, len(source_ids) / 3)  # Normalize to 3 sources

        verification_score = (avg_source_reliability * 0.6) + (source_diversity_score * 0.4)

        return {
            "threat_id": threat_id,
            "verified": verification_score >= 0.7,
            "verification_score": round(verification_score, 3),
            "source_count": len(source_ids),
            "intelligence_count": len(intelligence_items),
            "avg_source_reliability": round(avg_source_reliability, 3)
        }

    @staticmethod
    async def update_all_source_reliabilities(db: AsyncSession) -> Dict[str, int]:
        """
        Update reliability scores for all sources.

        Args:
            db: Database session

        Returns:
            Dict with update statistics
        """
        result = await db.execute(select(Source))
        sources = result.scalars().all()

        updated_count = 0

        for source in sources:
            new_reliability = await VerificationService.calculate_source_reliability(
                db, source.id
            )

            if abs(new_reliability - (source.reliability_score or 0.5)) > 0.01:
                source.reliability_score = new_reliability
                updated_count += 1

        await db.commit()

        logger.info(f"Updated reliability scores for {updated_count} sources")

        return {
            "total_sources": len(sources),
            "updated_count": updated_count
        }
