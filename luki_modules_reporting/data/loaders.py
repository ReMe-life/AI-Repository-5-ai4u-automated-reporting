"""Data loaders and adapters for LUKi Reporting

Handles loading metrics from various sources including demo data,
memory service APIs, and external data stores.
"""

import asyncio
import httpx
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
import random
import logging

from ..config import settings
from .schemas import (
    ActivityLog,
    MoodEntry,
    EngagementMetric,
    WellbeingMetrics,
    ActivityType,
    MoodLevel,
    EngagementLevel,
)


logger = logging.getLogger(__name__)


class MetricsLoader:
    """Base class for loading metrics from various sources"""
    
    def __init__(self, memory_service_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.memory_service_url = memory_service_url or settings.memory_service_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self._service_token: Optional[str] = auth_token
    
    async def _ensure_service_token(self) -> None:
        """Acquire a service token from the memory service if not already set.

        This mirrors the /auth/service-token flow used by the core agent,
        allowing the reporting service to call metrics endpoints in a
        production-like way while remaining optional in local/dev setups.
        """
        if self._service_token is not None:
            return

        try:
            response = await self.client.post(f"{self.memory_service_url}/auth/service-token")
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            if token:
                self._service_token = token
                logger.info("Obtained memory-service service token for reporting module")
            else:
                logger.warning("Service-token response from memory-service did not contain access_token")
        except Exception as exc:
            # Do not hard-fail: calls will proceed without Authorization header.
            logger.warning("Failed to obtain service token from memory-service: %s", exc)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def fetch_activity_logs(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[ActivityLog]:
        """Fetch activity logs from memory service"""
        try:
            await self._ensure_service_token()
            headers: Dict[str, str] = {}
            if self._service_token:
                headers["Authorization"] = f"Bearer {self._service_token}"

            response = await self.client.get(
                f"{self.memory_service_url}/v1/metrics/activities",
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return [ActivityLog(**item) for item in data.get("activities", [])]
        except Exception as e:
            logger.error("Error fetching activity logs from memory-service: %s", e)
            return []
    
    async def fetch_mood_entries(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[MoodEntry]:
        """Fetch mood entries from memory service"""
        try:
            await self._ensure_service_token()
            headers: Dict[str, str] = {}
            if self._service_token:
                headers["Authorization"] = f"Bearer {self._service_token}"

            response = await self.client.get(
                f"{self.memory_service_url}/v1/metrics/mood",
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return [MoodEntry(**item) for item in data.get("mood_entries", [])]
        except Exception as e:
            logger.error("Error fetching mood entries from memory-service: %s", e)
            return []
    
    async def fetch_engagement_metrics(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[EngagementMetric]:
        """Fetch daily engagement metrics from memory service"""
        try:
            await self._ensure_service_token()
            headers: Dict[str, str] = {}
            if self._service_token:
                headers["Authorization"] = f"Bearer {self._service_token}"

            response = await self.client.get(
                f"{self.memory_service_url}/v1/metrics/engagement",
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return [EngagementMetric(**item) for item in data.get("metrics", [])]
        except Exception as e:
            logger.error("Error fetching engagement metrics from memory-service: %s", e)
            return []


def generate_demo_activity_logs(
    user_id: str, 
    start_date: date, 
    end_date: date,
    activities_per_day: int = 3
) -> List[ActivityLog]:
    """Generate demo activity logs for testing"""
    
    activities = [
        ("Morning Walk", ActivityType.PHYSICAL),
        ("Crossword Puzzle", ActivityType.COGNITIVE),
        ("Family Video Call", ActivityType.SOCIAL),
        ("Painting", ActivityType.CREATIVE),
        ("Music Listening", ActivityType.RECREATIONAL),
        ("Physiotherapy", ActivityType.THERAPEUTIC),
        ("Meal Preparation", ActivityType.DAILY_LIVING),
        ("Garden Visit", ActivityType.PHYSICAL),
        ("Memory Games", ActivityType.COGNITIVE),
        ("Tea with Friends", ActivityType.SOCIAL),
    ]
    
    logs = []
    current_date = start_date
    
    while current_date <= end_date:
        # Generate activities for this day
        daily_activities = random.sample(activities, min(activities_per_day, len(activities)))
        
        for i, (activity_name, activity_type) in enumerate(daily_activities):
            # Spread activities throughout the day
            hour = 9 + (i * 3)  # Start at 9 AM, space 3 hours apart
            timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
            
            log = ActivityLog(
                id=str(uuid4()),
                user_id=user_id,
                timestamp=timestamp,
                activity_type=activity_type,
                activity_name=activity_name,
                duration_minutes=random.randint(15, 90),
                engagement_level=random.choice(list(EngagementLevel)),
                completion_rate=random.uniform(0.6, 1.0),
                notes=f"Demo activity: {activity_name}",
                carer_present=random.choice([True, False])
            )
            logs.append(log)
        
        current_date += timedelta(days=1)
    
    return logs


def generate_demo_mood_entries(
    user_id: str, 
    start_date: date, 
    end_date: date,
    entries_per_day: int = 2
) -> List[MoodEntry]:
    """Generate demo mood entries for testing"""
    
    entries = []
    current_date = start_date
    
    while current_date <= end_date:
        # Generate mood entries for this day
        for i in range(entries_per_day):
            # Morning and evening entries
            hour = 9 if i == 0 else 18
            timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
            
            entry = MoodEntry(
                id=str(uuid4()),
                user_id=user_id,
                timestamp=timestamp,
                mood_level=random.choice(list(MoodLevel)),
                energy_level=random.randint(3, 8),
                anxiety_level=random.randint(2, 6),
                pain_level=random.randint(1, 4),
                sleep_quality=random.randint(5, 9),
                notes=f"Demo mood entry - {'morning' if i == 0 else 'evening'}",
                source="demo_data"
            )
            entries.append(entry)
        
        current_date += timedelta(days=1)
    
    return entries


def generate_demo_engagement_metrics(
    user_id: str, 
    start_date: date, 
    end_date: date
) -> List[EngagementMetric]:
    """Generate demo daily engagement metrics"""
    
    metrics = []
    current_date = start_date
    
    while current_date <= end_date:
        metric = EngagementMetric(
            id=str(uuid4()),
            user_id=user_id,
            date=current_date,
            total_activities=random.randint(2, 6),
            total_duration_minutes=random.randint(60, 240),
            avg_engagement_score=random.uniform(0.6, 0.95),
            social_interactions=random.randint(1, 4),
            family_engagement_minutes=random.randint(15, 90),
            cognitive_activities=random.randint(1, 3),
            physical_activities=random.randint(0, 2),
            mood_entries=random.randint(1, 3),
            avg_mood_score=random.uniform(0.5, 0.9)
        )
        metrics.append(metric)
        current_date += timedelta(days=1)
    
    return metrics


def load_demo_metrics(
    user_id: str,
    start: date,
    end: date
) -> Dict[str, List]:
    """Load demo metrics for testing - matches README example"""
    
    return {
        "activity_logs": generate_demo_activity_logs(user_id, start, end),
        "mood_entries": generate_demo_mood_entries(user_id, start, end),
        "engagement_metrics": generate_demo_engagement_metrics(user_id, start, end)
    }


async def fetch_metrics_window(
    user_id: str,
    days: int = 7
) -> Dict[str, List]:
    """Fetch metrics for a time window - matches README example"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    loader = MetricsLoader()
    
    try:
        # Try to fetch from real services first
        activity_logs = await loader.fetch_activity_logs(user_id, start_date, end_date)
        mood_entries = await loader.fetch_mood_entries(user_id, start_date, end_date)
        engagement_metrics = await loader.fetch_engagement_metrics(user_id, start_date, end_date)
        
        # If no real data, fall back to demo data
        if not activity_logs and not mood_entries and not engagement_metrics:
            logger.info("No real metrics data found for user %s, using demo data", user_id)
            return load_demo_metrics(user_id, start_date, end_date)
        
        return {
            "activity_logs": activity_logs,
            "mood_entries": mood_entries,
            "engagement_metrics": engagement_metrics
        }
    
    except Exception as e:
        logger.error("Error fetching metrics window for user %s, falling back to demo data: %s", user_id, e)
        return load_demo_metrics(user_id, start_date, end_date)
    
    finally:
        await loader.close()
