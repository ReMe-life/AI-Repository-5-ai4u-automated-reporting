"""LangChain agent tools for LUKi Reporting

Exposes reporting functionality as LangChain tools for integration
with the LUKi core agent.
"""

import asyncio
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field

from ..data.loaders import fetch_metrics_window, load_demo_metrics
from ..analytics.aggregate import aggregate_metrics
from ..analytics.trends import detect_trends
from ..analytics.viz import ChartGenerator
from ..nlg.builder import build_report, ReportBuilder
from ..config import settings


class ReportingAgentTools:
    """Collection of reporting tools for LUKi agent"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
        self.report_builder = ReportBuilder()
    
    def get_all_tools(self) -> List:
        """Get all reporting tools for agent registration"""
        return [
            generate_wellbeing_report,
            get_activity_trends,
            create_visual_report,
            generate_mood_analysis,
            get_engagement_summary
        ]


# Tool input schemas
class WellbeingReportInput(BaseModel):
    """Input schema for wellbeing report generation"""
    user_id: str = Field(description="User identifier")
    days: int = Field(default=7, description="Number of days to include in report")
    audience: str = Field(default="family", description="Report audience: 'family' or 'clinician'")
    user_name: Optional[str] = Field(default=None, description="User's name for personalization")


class TrendAnalysisInput(BaseModel):
    """Input schema for trend analysis"""
    user_id: str = Field(description="User identifier")
    days: int = Field(default=14, description="Number of days for trend analysis")
    metric_type: str = Field(default="all", description="Metric type: 'activity', 'mood', 'engagement', or 'all'")


class VisualReportInput(BaseModel):
    """Input schema for visual report generation"""
    user_id: str = Field(description="User identifier")
    days: int = Field(default=7, description="Number of days to visualize")
    chart_types: List[str] = Field(default=["activity", "mood", "engagement"], description="Types of charts to generate")


# LangChain Tools
@tool("generate_wellbeing_report", return_direct=True)
def generate_wellbeing_report(user_id: str, days: int = 7, audience: str = "family", user_name: Optional[str] = None) -> str:
    """Generate a comprehensive wellbeing report for a user.
    
    Args:
        user_id: User identifier
        days: Number of days to include in report (default: 7)
        audience: Target audience - 'family' or 'clinician' (default: 'family')
        user_name: User's name for personalization (optional)
    
    Returns:
        Complete wellbeing report as formatted text
    """
    try:
        # Fetch metrics data
        metrics_data = asyncio.run(fetch_metrics_window(user_id=user_id, days=days))
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        # Build report
        report_text = build_report(
            wellbeing_metrics, 
            audience=audience,
            user_name=user_name
        )
        
        return report_text
    
    except Exception as e:
        return f"Error generating wellbeing report: {str(e)}"


@tool("get_activity_trends")
def get_activity_trends(user_id: str, days: int = 14, metric_type: str = "all") -> str:
    """Analyze activity and engagement trends for a user.
    
    Args:
        user_id: User identifier
        days: Number of days for trend analysis (default: 14)
        metric_type: Type of metrics to analyze - 'activity', 'mood', 'engagement', or 'all'
    
    Returns:
        Trend analysis summary
    """
    try:
        # Fetch metrics data
        metrics_data = asyncio.run(fetch_metrics_window(user_id=user_id, days=days))
        
        # Detect trends
        trends = detect_trends(metrics_data)
        
        # Format results
        if metric_type != "all" and metric_type in trends:
            trend = trends[metric_type]
            return f"{metric_type.title()} Trend: {trend.description} (confidence: {trend.confidence})"
        
        # Return all trends
        result = f"Trend Analysis for {user_id} (last {days} days):\n\n"
        
        for trend_type, trend_result in trends.items():
            result += f"**{trend_type.title()}**: {trend_result.description}\n"
            result += f"  - Direction: {trend_result.trend_direction}\n"
            result += f"  - Confidence: {trend_result.confidence}\n"
            result += f"  - Statistical significance: p={trend_result.p_value:.3f}\n\n"
        
        return result
    
    except Exception as e:
        return f"Error analyzing trends: {str(e)}"


@tool("create_visual_report")
def create_visual_report(user_id: str, days: int = 7, chart_types: Optional[List[str]] = None) -> str:
    """Create visual charts for wellbeing data.
    
    Args:
        user_id: User identifier
        days: Number of days to visualize (default: 7)
        chart_types: List of chart types to generate (default: ['activity', 'mood', 'engagement'])
    
    Returns:
        Summary of generated charts with file paths
    """
    if chart_types is None:
        chart_types = ["activity", "mood", "engagement"]
    
    try:
        # Fetch metrics data
        metrics_data = asyncio.run(fetch_metrics_window(user_id=user_id, days=days))
        
        chart_generator = ChartGenerator()
        generated_charts = {}
        
        # Generate requested charts
        if "activity" in chart_types:
            activity_path = chart_generator.activity_timeline_chart(
                metrics_data.get("activity_logs", []),
                f"outputs/{user_id}_activity_{days}d.png"
            )
            generated_charts["activity"] = activity_path
        
        if "mood" in chart_types:
            mood_path = chart_generator.mood_trend_chart(
                metrics_data.get("mood_entries", []),
                f"outputs/{user_id}_mood_{days}d.png"
            )
            generated_charts["mood"] = mood_path
        
        if "engagement" in chart_types:
            engagement_path = chart_generator.engagement_overview_chart(
                metrics_data.get("engagement_metrics", []),
                f"outputs/{user_id}_engagement_{days}d.png"
            )
            generated_charts["engagement"] = engagement_path
        
        # Create summary chart using aggregated metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        summary_path = chart_generator.weekly_summary_chart(
            wellbeing_metrics,
            f"outputs/{user_id}_summary_{days}d.png"
        )
        generated_charts["summary"] = summary_path
        
        # Format response
        result = f"Visual report generated for {user_id} ({days} days):\n\n"
        for chart_type, path in generated_charts.items():
            result += f"**{chart_type.title()} Chart**: {path}\n"
        
        result += f"\nCharts saved to: {settings.output_dir}/"
        
        return result
    
    except Exception as e:
        return f"Error creating visual report: {str(e)}"


@tool("generate_mood_analysis")
def generate_mood_analysis(user_id: str, days: int = 7) -> str:
    """Generate detailed mood and wellbeing analysis.
    
    Args:
        user_id: User identifier
        days: Number of days to analyze (default: 7)
    
    Returns:
        Detailed mood analysis summary
    """
    try:
        # Fetch metrics data
        metrics_data = asyncio.run(fetch_metrics_window(user_id=user_id, days=days))
        
        mood_entries = metrics_data.get("mood_entries", [])
        
        if not mood_entries:
            return f"No mood data available for {user_id} in the last {days} days."
        
        # Aggregate mood data
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        result = f"Mood Analysis for {user_id} (last {days} days):\n\n"
        
        if wellbeing_metrics.avg_mood_score:
            result += f"**Average Mood Score**: {wellbeing_metrics.avg_mood_score:.2f}/1.0\n"
        
        if wellbeing_metrics.avg_energy_level:
            result += f"**Average Energy Level**: {wellbeing_metrics.avg_energy_level:.1f}/10\n"
        
        if wellbeing_metrics.avg_sleep_quality:
            result += f"**Average Sleep Quality**: {wellbeing_metrics.avg_sleep_quality:.1f}/10\n"
        
        if wellbeing_metrics.avg_anxiety_level:
            result += f"**Average Anxiety Level**: {wellbeing_metrics.avg_anxiety_level:.1f}/10\n"
        
        result += f"**Total Mood Entries**: {wellbeing_metrics.total_mood_entries}\n"
        result += f"**Mood Trend**: {wellbeing_metrics.mood_trend}\n\n"
        
        # Add insights
        if wellbeing_metrics.key_insights:
            result += "**Key Insights**:\n"
            for insight in wellbeing_metrics.key_insights:
                if "mood" in insight.lower():
                    result += f"- {insight}\n"
        
        return result
    
    except Exception as e:
        return f"Error analyzing mood data: {str(e)}"


@tool("get_engagement_summary")
def get_engagement_summary(user_id: str, days: int = 7) -> str:
    """Get summary of user engagement and activity levels.
    
    Args:
        user_id: User identifier
        days: Number of days to summarize (default: 7)
    
    Returns:
        Engagement summary
    """
    try:
        # Fetch metrics data
        metrics_data = asyncio.run(fetch_metrics_window(user_id=user_id, days=days))
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        result = f"Engagement Summary for {user_id} (last {days} days):\n\n"
        
        result += f"**Total Activities**: {wellbeing_metrics.total_activities}\n"
        result += f"**Daily Average**: {wellbeing_metrics.avg_daily_activities:.1f} activities/day\n"
        result += f"**Total Duration**: {wellbeing_metrics.total_activity_minutes} minutes\n"
        result += f"**Average Engagement Score**: {wellbeing_metrics.avg_engagement_score:.2f}/1.0\n"
        result += f"**Social Interactions**: {wellbeing_metrics.total_social_interactions}\n"
        result += f"**Family Engagement**: {wellbeing_metrics.family_engagement_minutes} minutes\n\n"
        
        # Activity breakdown
        if wellbeing_metrics.activity_breakdown:
            result += "**Activity Types**:\n"
            for activity_type, count in wellbeing_metrics.activity_breakdown.items():
                result += f"- {activity_type.title()}: {count} activities\n"
            result += "\n"
        
        # Trends
        result += f"**Activity Trend**: {wellbeing_metrics.activity_trend}\n"
        result += f"**Engagement Trend**: {wellbeing_metrics.engagement_trend}\n\n"
        
        # Recommendations
        if wellbeing_metrics.recommendations:
            result += "**Recommendations**:\n"
            for rec in wellbeing_metrics.recommendations:
                result += f"- {rec}\n"
        
        return result
    
    except Exception as e:
        return f"Error getting engagement summary: {str(e)}"


# Tool registration helper
def get_reporting_tools() -> List:
    """Get all reporting tools for LUKi agent registration"""
    return [
        generate_wellbeing_report,
        get_activity_trends,
        create_visual_report,
        generate_mood_analysis,
        get_engagement_summary
    ]
