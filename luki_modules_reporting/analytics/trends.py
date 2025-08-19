"""Trend analysis utilities for wellbeing metrics

Implements time-series analysis, statistical trend detection,
and forecasting for activity, mood, and engagement data.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import statistics
from dataclasses import dataclass

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from ..data.schemas import ActivityLog, MoodEntry, EngagementMetric
from ..config import settings


@dataclass
class TrendResult:
    """Result of trend analysis"""
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, strength of trend
    p_value: float  # statistical significance
    slope: float  # rate of change
    confidence: str  # "high", "medium", "low"
    description: str  # human-readable description


class TrendAnalyzer:
    """Advanced trend analysis for wellbeing metrics"""
    
    def __init__(self, confidence_threshold: Optional[float] = None):
        self.significance_threshold = confidence_threshold or settings.statistical_significance_threshold
    
    def analyze_activity_trend(self, engagement_metrics: List[EngagementMetric]) -> TrendResult:
        """Analyze trend in daily activity levels"""
        if len(engagement_metrics) < 3:
            return TrendResult(
                trend_direction="insufficient_data",
                trend_strength=0.0,
                p_value=1.0,
                slope=0.0,
                confidence="low",
                description="Insufficient data for trend analysis"
            )
        
        # Sort by date and extract activity counts
        sorted_metrics = sorted(engagement_metrics, key=lambda x: x.date)
        dates = [m.date for m in sorted_metrics]
        activities = [float(m.total_activities) for m in sorted_metrics]
        
        return self._calculate_linear_trend(dates, activities, "activity levels")
    
    def analyze_engagement_trend(self, engagement_metrics: List[EngagementMetric]) -> TrendResult:
        """Analyze trend in engagement scores"""
        if len(engagement_metrics) < 3:
            return TrendResult(
                trend_direction="insufficient_data",
                trend_strength=0.0,
                p_value=1.0,
                slope=0.0,
                confidence="low",
                description="Insufficient data for trend analysis"
            )
        
        sorted_metrics = sorted(engagement_metrics, key=lambda x: x.date)
        dates = [m.date for m in sorted_metrics]
        engagement_scores = [m.avg_engagement_score for m in sorted_metrics]
        
        return self._calculate_linear_trend(dates, engagement_scores, "engagement levels")
    
    def analyze_mood_trend(self, mood_entries: List[MoodEntry]) -> TrendResult:
        """Analyze trend in mood levels"""
        if len(mood_entries) < 3:
            return TrendResult(
                trend_direction="insufficient_data",
                trend_strength=0.0,
                p_value=1.0,
                slope=0.0,
                confidence="low",
                description="Insufficient data for trend analysis"
            )
        
        # Convert mood levels to numeric scores
        mood_scores = {
            "very_low": 1, "low": 2, "neutral": 3, "high": 4, "very_high": 5
        }
        
        sorted_entries = sorted(mood_entries, key=lambda x: x.timestamp)
        dates = [m.timestamp.date() for m in sorted_entries]
        moods = [mood_scores[m.mood_level.value] for m in sorted_entries]
        
        # Group by date and take daily averages
        daily_moods = {}
        for date_val, mood in zip(dates, moods):
            if date_val not in daily_moods:
                daily_moods[date_val] = []
            daily_moods[date_val].append(mood)
        
        dates = sorted(daily_moods.keys())
        avg_moods = [statistics.mean(daily_moods[d]) for d in dates]
        
        return self._calculate_linear_trend(dates, avg_moods, "mood levels")
    
    def _calculate_linear_trend(self, dates: List[date], values: List[float], metric_name: str) -> TrendResult:
        """Calculate linear trend using scipy stats"""
        if len(dates) < 3:
            return TrendResult(
                trend_direction="insufficient_data",
                trend_strength=0.0,
                p_value=1.0,
                slope=0.0,
                confidence="low",
                description="Insufficient data for trend analysis"
            )
        
        # Convert dates to numeric values (days since first date)
        first_date = dates[0]
        x = [(d - first_date).days for d in dates]
        y = values
        
        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend direction
        if p_value < self.significance_threshold:
            if slope > 0:
                trend_direction = "increasing"
            elif slope < 0:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"  # Not statistically significant
        
        # Calculate trend strength (absolute correlation coefficient)
        trend_strength = abs(r_value)
        
        # Determine confidence level
        if p_value < 0.01:
            confidence = "high"
        elif p_value < 0.05:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate description
        if trend_direction == "increasing":
            description = f"{metric_name.capitalize()} are showing a statistically significant upward trend"
        elif trend_direction == "decreasing":
            description = f"{metric_name.capitalize()} are showing a statistically significant downward trend"
        else:
            description = f"{metric_name.capitalize()} are relatively stable with no significant trend"
        
        return TrendResult(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            p_value=p_value,
            slope=slope,
            confidence=confidence,
            description=description
        )
    
    def detect_anomalies(self, values: List[float], threshold: float = 2.0) -> List[int]:
        """Detect anomalies using z-score method"""
        if len(values) < 3:
            return []
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        if std_val == 0:
            return []
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_val)
            if z_score > threshold:
                anomalies.append(i)
        
        return anomalies
    
    def seasonal_analysis(self, engagement_metrics: List[EngagementMetric]) -> Dict[str, Any]:
        """Perform seasonal decomposition if enough data points"""
        if len(engagement_metrics) < 14:  # Need at least 2 weeks
            return {"error": "Insufficient data for seasonal analysis"}
        
        try:
            # Create time series
            sorted_metrics = sorted(engagement_metrics, key=lambda x: x.date)
            dates = pd.date_range(
                start=sorted_metrics[0].date,
                end=sorted_metrics[-1].date,
                freq='D'
            )
            
            # Create DataFrame with all dates
            df = pd.DataFrame(index=dates)
            
            # Map engagement data
            engagement_data = {m.date: m.avg_engagement_score for m in sorted_metrics}
            df['engagement'] = df.index.map(lambda x: engagement_data.get(x.date(), 0))
            
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(
                df['engagement'], 
                model='additive', 
                period=7  # Weekly seasonality
            )
            
            return {
                "trend": decomposition.trend.dropna().tolist(),
                "seasonal": decomposition.seasonal.dropna().tolist(),
                "residual": decomposition.resid.dropna().tolist(),
                "has_seasonality": True
            }
        
        except Exception as e:
            return {"error": f"Seasonal analysis failed: {str(e)}"}


def detect_trends(metrics_data: Dict[str, List]) -> Dict[str, TrendResult]:
    """Main trend detection function"""
    
    activity_logs = metrics_data.get("activity_logs", [])
    mood_entries = metrics_data.get("mood_entries", [])
    engagement_metrics = metrics_data.get("engagement_metrics", [])
    
    analyzer = TrendAnalyzer()
    
    trends = {}
    
    # Analyze activity trends
    if engagement_metrics:
        trends["activity"] = analyzer.analyze_activity_trend(engagement_metrics)
        trends["engagement"] = analyzer.analyze_engagement_trend(engagement_metrics)
    
    # Analyze mood trends
    if mood_entries:
        trends["mood"] = analyzer.analyze_mood_trend(mood_entries)
    
    return trends


def forecast_next_week(engagement_metrics: List[EngagementMetric]) -> Dict[str, Any]:
    """Simple forecasting for next week's metrics"""
    if len(engagement_metrics) < 7:
        return {"error": "Insufficient data for forecasting"}
    
    try:
        # Sort by date
        sorted_metrics = sorted(engagement_metrics, key=lambda x: x.date)
        
        # Extract activity levels
        activities = [m.total_activities for m in sorted_metrics]
        engagement_scores = [m.avg_engagement_score for m in sorted_metrics]
        
        # Simple moving average forecast
        activity_forecast = statistics.mean(activities[-7:])  # Last week average
        engagement_forecast = statistics.mean(engagement_scores[-7:])
        
        # Calculate trend adjustment
        if len(activities) >= 14:
            recent_avg = statistics.mean(activities[-7:])
            older_avg = statistics.mean(activities[-14:-7])
            trend_adjustment = (recent_avg - older_avg) / 7  # Daily trend
        else:
            trend_adjustment = 0
        
        return {
            "forecasted_daily_activities": max(0, activity_forecast + trend_adjustment),
            "forecasted_engagement_score": max(0, min(1, engagement_forecast)),
            "confidence": "medium" if len(activities) >= 14 else "low",
            "based_on_days": len(activities)
        }
    
    except Exception as e:
        return {"error": f"Forecasting failed: {str(e)}"}
