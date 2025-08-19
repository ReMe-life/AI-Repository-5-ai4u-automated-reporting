"""Aggregation utilities for wellbeing metrics

Handles rollups, statistics, and aggregated insights from raw activity,
mood, and engagement data.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import statistics

from ..data.schemas import (
    ActivityLog,
    MoodEntry, 
    EngagementMetric,
    WellbeingMetrics,
    ActivityType,
    MoodLevel,
    EngagementLevel
)


class WellbeingAggregator:
    """Aggregates raw metrics into wellbeing insights"""
    
    def __init__(self):
        self.mood_level_scores = {
            MoodLevel.VERY_LOW: 0.1,
            MoodLevel.LOW: 0.3,
            MoodLevel.NEUTRAL: 0.5,
            MoodLevel.HIGH: 0.7,
            MoodLevel.VERY_HIGH: 0.9
        }
        
        self.engagement_scores = {
            EngagementLevel.NONE: 0.0,
            EngagementLevel.LOW: 0.25,
            EngagementLevel.MODERATE: 0.5,
            EngagementLevel.HIGH: 0.75,
            EngagementLevel.VERY_HIGH: 1.0
        }
    
    def aggregate_activities(self, activities: List[ActivityLog]) -> Dict[str, Any]:
        """Aggregate activity data"""
        if not activities:
            return {
                "total_activities": 0,
                "total_duration_minutes": 0,
                "avg_engagement_score": 0.0,
                "activity_breakdown": {},
                "completion_rate": 0.0
            }
        
        total_duration = sum(a.duration_minutes or 0 for a in activities)
        engagement_scores = [self.engagement_scores[a.engagement_level] for a in activities]
        completion_rates = [a.completion_rate for a in activities]
        
        # Activity type breakdown
        type_counts = Counter(a.activity_type.value for a in activities)
        
        return {
            "total_activities": len(activities),
            "total_duration_minutes": total_duration,
            "avg_engagement_score": statistics.mean(engagement_scores) if engagement_scores else 0.0,
            "activity_breakdown": dict(type_counts),
            "completion_rate": statistics.mean(completion_rates) if completion_rates else 0.0
        }
    
    def aggregate_mood(self, mood_entries: List[MoodEntry]) -> Dict[str, Any]:
        """Aggregate mood data"""
        if not mood_entries:
            return {
                "total_mood_entries": 0,
                "avg_mood_score": None,
                "avg_energy_level": None,
                "avg_sleep_quality": None,
                "avg_anxiety_level": None,
                "avg_pain_level": None
            }
        
        mood_scores = [self.mood_level_scores[m.mood_level] for m in mood_entries]
        
        # Filter out None values for optional fields
        energy_levels = [m.energy_level for m in mood_entries if m.energy_level is not None]
        sleep_qualities = [m.sleep_quality for m in mood_entries if m.sleep_quality is not None]
        anxiety_levels = [m.anxiety_level for m in mood_entries if m.anxiety_level is not None]
        pain_levels = [m.pain_level for m in mood_entries if m.pain_level is not None]
        
        return {
            "total_mood_entries": len(mood_entries),
            "avg_mood_score": statistics.mean(mood_scores) if mood_scores else None,
            "avg_energy_level": statistics.mean(energy_levels) if energy_levels else None,
            "avg_sleep_quality": statistics.mean(sleep_qualities) if sleep_qualities else None,
            "avg_anxiety_level": statistics.mean(anxiety_levels) if anxiety_levels else None,
            "avg_pain_level": statistics.mean(pain_levels) if pain_levels else None
        }
    
    def aggregate_social_metrics(self, activities: List[ActivityLog], engagement_metrics: List[EngagementMetric]) -> Dict[str, Any]:
        """Aggregate social interaction metrics"""
        social_activities = [a for a in activities if a.activity_type == ActivityType.SOCIAL]
        
        total_social_interactions = len(social_activities)
        family_engagement_minutes = sum(m.family_engagement_minutes for m in engagement_metrics)
        
        return {
            "total_social_interactions": total_social_interactions,
            "family_engagement_minutes": family_engagement_minutes,
            "avg_daily_social_time": family_engagement_minutes / len(engagement_metrics) if engagement_metrics else 0.0
        }
    
    def calculate_trends(self, daily_metrics: List[EngagementMetric]) -> Dict[str, str]:
        """Calculate basic trends from daily metrics"""
        if len(daily_metrics) < 3:
            return {
                "activity_trend": "insufficient_data",
                "engagement_trend": "insufficient_data",
                "mood_trend": "insufficient_data"
            }
        
        # Sort by date
        sorted_metrics = sorted(daily_metrics, key=lambda x: x.date)
        
        # Calculate trends using simple linear comparison
        first_half = sorted_metrics[:len(sorted_metrics)//2]
        second_half = sorted_metrics[len(sorted_metrics)//2:]
        
        # Activity trend
        first_avg_activities = statistics.mean(m.total_activities for m in first_half)
        second_avg_activities = statistics.mean(m.total_activities for m in second_half)
        
        if second_avg_activities > first_avg_activities * 1.1:
            activity_trend = "increasing"
        elif second_avg_activities < first_avg_activities * 0.9:
            activity_trend = "decreasing"
        else:
            activity_trend = "stable"
        
        # Engagement trend
        first_avg_engagement = statistics.mean(m.avg_engagement_score for m in first_half)
        second_avg_engagement = statistics.mean(m.avg_engagement_score for m in second_half)
        
        if second_avg_engagement > first_avg_engagement * 1.05:
            engagement_trend = "improving"
        elif second_avg_engagement < first_avg_engagement * 0.95:
            engagement_trend = "declining"
        else:
            engagement_trend = "stable"
        
        # Mood trend
        mood_scores = [m.avg_mood_score for m in sorted_metrics if m.avg_mood_score is not None]
        if len(mood_scores) >= 3:
            first_mood = statistics.mean(mood_scores[:len(mood_scores)//2])
            second_mood = statistics.mean(mood_scores[len(mood_scores)//2:])
            
            if second_mood > first_mood * 1.05:
                mood_trend = "improving"
            elif second_mood < first_mood * 0.95:
                mood_trend = "declining"
            else:
                mood_trend = "stable"
        else:
            mood_trend = "insufficient_data"
        
        return {
            "activity_trend": activity_trend,
            "engagement_trend": engagement_trend,
            "mood_trend": mood_trend
        }
    
    def generate_insights(self, metrics: WellbeingMetrics) -> List[str]:
        """Generate key insights from aggregated metrics"""
        insights = []
        
        # Activity insights
        if metrics.avg_daily_activities >= 3:
            insights.append("Maintaining good daily activity levels")
        elif metrics.avg_daily_activities < 2:
            insights.append("Activity levels below recommended minimum")
        
        # Engagement insights
        if metrics.avg_engagement_score >= 0.7:
            insights.append("High engagement in activities")
        elif metrics.avg_engagement_score < 0.5:
            insights.append("Low engagement - may need activity adjustments")
        
        # Mood insights
        if metrics.avg_mood_score and metrics.avg_mood_score >= 0.7:
            insights.append("Generally positive mood")
        elif metrics.avg_mood_score and metrics.avg_mood_score < 0.4:
            insights.append("Mood concerns - consider additional support")
        
        # Social insights
        if metrics.total_social_interactions >= 7:  # Assuming weekly period
            insights.append("Good social engagement")
        elif metrics.total_social_interactions < 3:
            insights.append("Limited social interaction - encourage more social activities")
        
        # Trend insights
        if metrics.activity_trend == "increasing":
            insights.append("Activity levels are improving")
        elif metrics.activity_trend == "decreasing":
            insights.append("Activity levels are declining - intervention may be needed")
        
        return insights
    
    def generate_recommendations(self, metrics: WellbeingMetrics) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        # Activity recommendations
        if metrics.avg_daily_activities < 2:
            recommendations.append("Increase daily activities to at least 2-3 per day")
        
        if metrics.avg_engagement_score < 0.5:
            recommendations.append("Try different activity types to improve engagement")
        
        # Social recommendations
        if metrics.total_social_interactions < 5:  # Weekly
            recommendations.append("Schedule more social activities and family time")
        
        # Mood recommendations
        if metrics.avg_mood_score and metrics.avg_mood_score < 0.4:
            recommendations.append("Consider mood-boosting activities like music or art")
        
        # Physical activity recommendations
        physical_activities = metrics.activity_breakdown.get("physical", 0)
        if physical_activities < 3:  # Weekly
            recommendations.append("Include more physical activities like walking or gentle exercise")
        
        return recommendations


def aggregate_metrics(metrics_data: Dict[str, List]) -> WellbeingMetrics:
    """Main aggregation function - matches README example"""
    
    activity_logs = metrics_data.get("activity_logs", [])
    mood_entries = metrics_data.get("mood_entries", [])
    engagement_metrics = metrics_data.get("engagement_metrics", [])
    
    if not activity_logs and not mood_entries and not engagement_metrics:
        # Return empty metrics for user
        user_id = "unknown"
        today = date.today()
        return WellbeingMetrics(
            user_id=user_id,
            start_date=today - timedelta(days=7),
            end_date=today,
            avg_mood_score=None,
            mood_trend=None,
            avg_energy_level=None,
            avg_sleep_quality=None,
            avg_anxiety_level=None,
            avg_pain_level=None,
            activity_trend=None,
            engagement_trend=None
        )
    
    # Extract user_id and date range
    user_id = "unknown"
    dates = []
    
    if activity_logs:
        user_id = activity_logs[0].user_id
        dates.extend([a.timestamp.date() for a in activity_logs])
    
    if mood_entries:
        if user_id == "unknown":
            user_id = mood_entries[0].user_id
        dates.extend([m.timestamp.date() for m in mood_entries])
    
    if engagement_metrics:
        if user_id == "unknown":
            user_id = engagement_metrics[0].user_id
        dates.extend([m.date for m in engagement_metrics])
    
    start_date = min(dates) if dates else date.today() - timedelta(days=7)
    end_date = max(dates) if dates else date.today()
    
    # Calculate number of days for averages
    num_days = (end_date - start_date).days + 1
    
    aggregator = WellbeingAggregator()
    
    # Aggregate activities
    activity_stats = aggregator.aggregate_activities(activity_logs)
    
    # Aggregate mood
    mood_stats = aggregator.aggregate_mood(mood_entries)
    
    # Aggregate social metrics
    social_stats = aggregator.aggregate_social_metrics(activity_logs, engagement_metrics)
    
    # Calculate trends
    trends = aggregator.calculate_trends(engagement_metrics)
    
    # Create wellbeing metrics object
    wellbeing_metrics = WellbeingMetrics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        
        # Activity metrics
        total_activities=activity_stats["total_activities"],
        avg_daily_activities=activity_stats["total_activities"] / num_days,
        total_activity_minutes=activity_stats["total_duration_minutes"],
        avg_daily_activity_minutes=activity_stats["total_duration_minutes"] / num_days,
        avg_engagement_score=activity_stats["avg_engagement_score"],
        activity_breakdown=activity_stats["activity_breakdown"],
        
        # Mood metrics
        total_mood_entries=mood_stats["total_mood_entries"],
        avg_mood_score=mood_stats["avg_mood_score"],
        
        # Social metrics
        total_social_interactions=social_stats["total_social_interactions"],
        family_engagement_minutes=social_stats["family_engagement_minutes"],
        avg_daily_social_time=social_stats["avg_daily_social_time"],
        
        # Health indicators
        avg_energy_level=mood_stats["avg_energy_level"],
        avg_sleep_quality=mood_stats["avg_sleep_quality"],
        avg_anxiety_level=mood_stats["avg_anxiety_level"],
        avg_pain_level=mood_stats["avg_pain_level"],
        
        # Trends
        activity_trend=trends["activity_trend"],
        engagement_trend=trends["engagement_trend"],
        mood_trend=trends["mood_trend"]
    )
    
    # Generate insights and recommendations
    wellbeing_metrics.key_insights = aggregator.generate_insights(wellbeing_metrics)
    wellbeing_metrics.recommendations = aggregator.generate_recommendations(wellbeing_metrics)
    
    return wellbeing_metrics
