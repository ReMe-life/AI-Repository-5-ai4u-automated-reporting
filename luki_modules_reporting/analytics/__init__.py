"""Analytics module for LUKi Reporting

Contains aggregation, trend analysis, and visualization utilities.
"""

from .aggregate import aggregate_metrics, WellbeingAggregator
from .trends import TrendAnalyzer, detect_trends
from .viz import activity_chart, mood_chart, engagement_chart, ChartGenerator

__all__ = [
    "aggregate_metrics",
    "WellbeingAggregator", 
    "TrendAnalyzer",
    "detect_trends",
    "activity_chart",
    "mood_chart", 
    "engagement_chart",
    "ChartGenerator",
]
