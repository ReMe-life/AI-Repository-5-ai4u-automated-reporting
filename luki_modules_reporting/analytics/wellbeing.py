"""High-level wellbeing analysis orchestration for LUKi Reporting.

Combines metrics loading, aggregation, and trend/forecast analysis into
simple async methods used by the FastAPI service.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List

from ..data.loaders import fetch_metrics_window
from ..analytics.aggregate import aggregate_metrics
from ..analytics.trends import detect_trends, forecast_next_week, TrendResult


class WellbeingAnalyzer:
    """Analyze user wellbeing over a recent time window.

    This class provides the concrete implementation used by
    `luki_modules_reporting.main` for:
    - generating a structured wellbeing report payload, and
    - returning trend summaries for a user.
    """

    async def generate_report(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate a structured wellbeing report for a user.

        Returns a dict that the FastAPI layer can JSON-encode directly,
        containing aggregated metrics, trends, and a simple forecast.
        """
        # Load raw metrics for the window
        metrics_data = await fetch_metrics_window(user_id=user_id, days=days)

        # Aggregate into WellbeingMetrics (activities, mood, social, trends)
        wellbeing_metrics = aggregate_metrics(metrics_data)

        # Run advanced trend analysis where enough data exists
        trends = detect_trends(metrics_data)
        trend_dict: Dict[str, Dict[str, Any]] = {}
        for name, result in trends.items():
            if isinstance(result, TrendResult):
                trend_dict[name] = {
                    "trend_direction": result.trend_direction,
                    "trend_strength": result.trend_strength,
                    "p_value": result.p_value,
                    "slope": result.slope,
                    "confidence": result.confidence,
                    "description": result.description,
                }

        # Simple forecast for the next week based on engagement metrics
        engagement_metrics: List[Any] = metrics_data.get("engagement_metrics", [])
        forecast = forecast_next_week(engagement_metrics)

        return {
            "user_id": user_id,
            "period": {
                "start_date": wellbeing_metrics.start_date.isoformat(),
                "end_date": wellbeing_metrics.end_date.isoformat(),
            },
            "generated_at": datetime.utcnow().isoformat(),
            "wellbeing_metrics": wellbeing_metrics.dict(),
            "trends": trend_dict,
            "forecast": forecast,
        }

    async def get_trends(self, user_id: str, days: int = 14) -> Dict[str, Any]:
        """Return trend summaries (and simple forecast) for a user.

        Used by `/reports/{user_id}/trends` in `main.py`.
        """
        metrics_data = await fetch_metrics_window(user_id=user_id, days=days)
        trends = detect_trends(metrics_data)

        trend_dict: Dict[str, Dict[str, Any]] = {}
        for name, result in trends.items():
            if isinstance(result, TrendResult):
                trend_dict[name] = {
                    "trend_direction": result.trend_direction,
                    "trend_strength": result.trend_strength,
                    "p_value": result.p_value,
                    "slope": result.slope,
                    "confidence": result.confidence,
                    "description": result.description,
                }

        engagement_metrics: List[Any] = metrics_data.get("engagement_metrics", [])
        forecast = forecast_next_week(engagement_metrics)

        return {
            "analysis_period_days": days,
            "trends": trend_dict,
            "forecast": forecast,
        }
