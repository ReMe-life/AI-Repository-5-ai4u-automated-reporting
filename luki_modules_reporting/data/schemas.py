"""Pydantic schemas for LUKi Reporting data models

Defines data structures for activity logs, mood entries, engagement metrics,
and aggregated wellbeing data used in report generation.
"""

from datetime import datetime, date as date_type
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class MoodLevel(str, Enum):
    """Mood level enumeration"""
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ActivityType(str, Enum):
    """Activity type enumeration"""
    PHYSICAL = "physical"
    COGNITIVE = "cognitive"
    SOCIAL = "social"
    CREATIVE = "creative"
    RECREATIONAL = "recreational"
    THERAPEUTIC = "therapeutic"
    DAILY_LIVING = "daily_living"


class EngagementLevel(str, Enum):
    """Engagement level enumeration"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ActivityLog(BaseModel):
    """Activity log entry schema"""
    
    id: str = Field(..., description="Unique activity log ID")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="Activity timestamp")
    activity_type: ActivityType = Field(..., description="Type of activity")
    activity_name: str = Field(..., description="Name of the activity")
    duration_minutes: Optional[int] = Field(None, description="Activity duration in minutes")
    engagement_level: EngagementLevel = Field(..., description="User engagement level")
    completion_rate: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Activity completion rate (0-1)"
    )
    notes: Optional[str] = Field(None, description="Additional notes about the activity")
    carer_present: bool = Field(default=False, description="Whether a carer was present")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MoodEntry(BaseModel):
    """Mood entry schema"""
    
    id: str = Field(..., description="Unique mood entry ID")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="Mood entry timestamp")
    mood_level: MoodLevel = Field(..., description="Reported mood level")
    energy_level: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Energy level (1-10 scale)"
    )
    anxiety_level: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Anxiety level (1-10 scale)"
    )
    pain_level: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Pain level (1-10 scale)"
    )
    sleep_quality: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Sleep quality (1-10 scale)"
    )
    notes: Optional[str] = Field(None, description="Additional mood notes")
    source: str = Field(default="user_report", description="Source of mood data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EngagementMetric(BaseModel):
    """Engagement metric schema"""
    
    id: str = Field(..., description="Unique engagement metric ID")
    user_id: str = Field(..., description="User identifier")
    date: date_type = Field(..., description="Metric date")
    total_activities: int = Field(default=0, description="Total activities completed")
    total_duration_minutes: int = Field(default=0, description="Total activity duration")
    avg_engagement_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Average engagement score (0-1)"
    )
    social_interactions: int = Field(default=0, description="Number of social interactions")
    family_engagement_minutes: int = Field(default=0, description="Family engagement time")
    cognitive_activities: int = Field(default=0, description="Number of cognitive activities")
    physical_activities: int = Field(default=0, description="Number of physical activities")
    mood_entries: int = Field(default=0, description="Number of mood entries")
    avg_mood_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Average mood score (0-1)"
    )
    
    class Config:
        json_encoders = {
            date_type: lambda v: v.isoformat()
        }


class WellbeingMetrics(BaseModel):
    """Aggregated wellbeing metrics for a time period"""
    
    user_id: str = Field(..., description="User identifier")
    start_date: date_type = Field(..., description="Period start date")
    end_date: date_type = Field(..., description="Period end date")
    
    # Activity metrics
    total_activities: int = Field(default=0)
    avg_daily_activities: float = Field(default=0.0)
    total_activity_minutes: int = Field(default=0)
    avg_daily_activity_minutes: float = Field(default=0.0)
    avg_engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Activity breakdown by type
    activity_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    # Mood metrics
    total_mood_entries: int = Field(default=0)
    avg_mood_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    mood_trend: Optional[str] = Field(None, description="improving, declining, stable")
    
    # Social metrics
    total_social_interactions: int = Field(default=0)
    family_engagement_minutes: int = Field(default=0)
    avg_daily_social_time: float = Field(default=0.0)
    
    # Health indicators
    avg_energy_level: Optional[float] = Field(None, ge=1.0, le=10.0)
    avg_sleep_quality: Optional[float] = Field(None, ge=1.0, le=10.0)
    avg_anxiety_level: Optional[float] = Field(None, ge=1.0, le=10.0)
    avg_pain_level: Optional[float] = Field(None, ge=1.0, le=10.0)
    
    # Trends and insights
    activity_trend: Optional[str] = Field(None, description="increasing, decreasing, stable")
    engagement_trend: Optional[str] = Field(None, description="improving, declining, stable")
    key_insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            date_type: lambda v: v.isoformat()
        }


class ReportData(BaseModel):
    """Complete report data structure"""
    
    user_id: str = Field(..., description="User identifier")
    report_id: str = Field(..., description="Unique report identifier")
    generated_at: datetime = Field(default_factory=datetime.now)
    report_period_start: date_type = Field(..., description="Report period start")
    report_period_end: date_type = Field(..., description="Report period end")
    audience: str = Field(..., description="Target audience (family, clinician)")
    
    # Core data
    wellbeing_metrics: WellbeingMetrics = Field(..., description="Aggregated wellbeing metrics")
    activity_logs: List[ActivityLog] = Field(default_factory=list)
    mood_entries: List[MoodEntry] = Field(default_factory=list)
    daily_metrics: List[EngagementMetric] = Field(default_factory=list)
    
    # Generated content
    narrative_summary: Optional[str] = Field(None, description="Generated narrative summary")
    chart_paths: Dict[str, str] = Field(default_factory=dict, description="Paths to generated charts")
    
    # Metadata
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date_type: lambda v: v.isoformat()
        }
