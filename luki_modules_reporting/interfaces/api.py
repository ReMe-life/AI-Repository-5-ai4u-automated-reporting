"""Optional FastAPI endpoints for LUKi Reporting

Provides HTTP API endpoints for report generation and analytics.
Can be used independently or integrated with the main API gateway.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os

from ..data.loaders import fetch_metrics_window
from ..analytics.aggregate import aggregate_metrics
from ..analytics.trends import detect_trends
from ..analytics.viz import ChartGenerator
from ..nlg.builder import ReportBuilder
from ..data.schemas import WellbeingMetrics, ReportData
from ..config import settings


# Request/Response models
class ReportRequest(BaseModel):
    user_id: str
    days: int = 7
    audience: str = "family"
    user_name: Optional[str] = None
    include_charts: bool = True


class ReportResponse(BaseModel):
    report_id: str
    user_id: str
    narrative: Optional[str]
    chart_paths: Dict[str, str]
    generated_at: str
    metadata: Dict[str, Any]


class TrendResponse(BaseModel):
    user_id: str
    analysis_period_days: int
    trends: Dict[str, Dict[str, Any]]
    generated_at: str


# Initialize FastAPI app
app = FastAPI(
    title="LUKi Reporting API",
    description="Automated wellbeing reports and analytics",
    version=settings.service_version
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version
    }


@app.post("/v1/reports/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a wellbeing report"""
    try:
        # Fetch metrics data
        metrics_data = await fetch_metrics_window(
            user_id=request.user_id,
            days=request.days
        )
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        # Generate charts if requested
        chart_paths = {}
        if request.include_charts:
            chart_generator = ChartGenerator()
            
            # Generate activity chart
            activity_path = chart_generator.activity_timeline_chart(
                metrics_data.get("activity_logs", []),
                f"outputs/{request.user_id}_activity_{request.days}d.png"
            )
            chart_paths["activity"] = activity_path
            
            # Generate mood chart
            mood_path = chart_generator.mood_trend_chart(
                metrics_data.get("mood_entries", []),
                f"outputs/{request.user_id}_mood_{request.days}d.png"
            )
            chart_paths["mood"] = mood_path
            
            # Generate engagement chart
            engagement_path = chart_generator.engagement_overview_chart(
                metrics_data.get("engagement_metrics", []),
                f"outputs/{request.user_id}_engagement_{request.days}d.png"
            )
            chart_paths["engagement"] = engagement_path
        
        # Build report
        report_builder = ReportBuilder()
        report_data = report_builder.build_complete_report_data(
            wellbeing_metrics=wellbeing_metrics,
            audience=request.audience,
            user_name=request.user_name,
            chart_paths=chart_paths,
            activity_logs=metrics_data.get("activity_logs", []),
            mood_entries=metrics_data.get("mood_entries", []),
            daily_metrics=metrics_data.get("engagement_metrics", [])
        )
        
        return ReportResponse(
            report_id=report_data.report_id,
            user_id=report_data.user_id,
            narrative=report_data.narrative_summary,
            chart_paths=report_data.chart_paths,
            generated_at=report_data.generated_at.isoformat(),
            metadata=report_data.generation_metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/v1/trends/{user_id}", response_model=TrendResponse)
async def get_trends(
    user_id: str,
    days: int = Query(14, description="Number of days for trend analysis")
):
    """Get trend analysis for a user"""
    try:
        # Fetch metrics data
        metrics_data = await fetch_metrics_window(user_id=user_id, days=days)
        
        # Detect trends
        trends = detect_trends(metrics_data)
        
        # Convert trend results to dict format
        trend_dict = {}
        for trend_type, trend_result in trends.items():
            trend_dict[trend_type] = {
                "direction": trend_result.trend_direction,
                "strength": trend_result.trend_strength,
                "confidence": trend_result.confidence,
                "p_value": trend_result.p_value,
                "slope": trend_result.slope,
                "description": trend_result.description
            }
        
        return TrendResponse(
            user_id=user_id,
            analysis_period_days=days,
            trends=trend_dict,
            generated_at=date.today().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@app.get("/v1/charts/{user_id}")
async def generate_charts(
    user_id: str,
    days: int = Query(7, description="Number of days to visualize"),
    chart_type: str = Query("summary", description="Chart type: activity, mood, engagement, or summary")
):
    """Generate and return chart image"""
    try:
        # Fetch metrics data
        metrics_data = await fetch_metrics_window(user_id=user_id, days=days)
        
        chart_generator = ChartGenerator()
        
        # Generate requested chart
        if chart_type == "activity":
            chart_path = chart_generator.activity_timeline_chart(
                metrics_data.get("activity_logs", []),
                f"outputs/{user_id}_activity_{days}d.png"
            )
        elif chart_type == "mood":
            chart_path = chart_generator.mood_trend_chart(
                metrics_data.get("mood_entries", []),
                f"outputs/{user_id}_mood_{days}d.png"
            )
        elif chart_type == "engagement":
            wellbeing_metrics = aggregate_metrics(metrics_data)
            summary_path = chart_generator.weekly_summary_chart(
                wellbeing_metrics,
                f"outputs/{user_id}_summary_{days}d.png"
            )
            chart_path = chart_generator.engagement_overview_chart(
                metrics_data.get("engagement_metrics", []),
                f"outputs/{user_id}_engagement_{days}d.png"
            )
        else:  # summary
            wellbeing_metrics = aggregate_metrics(metrics_data)
            chart_path = chart_generator.weekly_summary_chart(
                wellbeing_metrics,
                f"outputs/{user_id}_summary_{days}d.png"
            )
        
        # Return chart file
        if os.path.exists(chart_path):
            return FileResponse(
                chart_path,
                media_type="image/png",
                filename=os.path.basename(chart_path)
            )
        else:
            raise HTTPException(status_code=404, detail="Chart not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.get("/v1/metrics/{user_id}")
async def get_metrics(
    user_id: str,
    days: int = Query(7, description="Number of days to retrieve")
):
    """Get raw metrics data for a user"""
    try:
        # Fetch metrics data
        metrics_data = await fetch_metrics_window(user_id=user_id, days=days)
        
        # Aggregate for summary
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "raw_data": {
                "activity_logs": len(metrics_data.get("activity_logs", [])),
                "mood_entries": len(metrics_data.get("mood_entries", [])),
                "engagement_metrics": len(metrics_data.get("engagement_metrics", []))
            },
            "summary": {
                "total_activities": wellbeing_metrics.total_activities,
                "avg_daily_activities": wellbeing_metrics.avg_daily_activities,
                "avg_engagement_score": wellbeing_metrics.avg_engagement_score,
                "avg_mood_score": wellbeing_metrics.avg_mood_score,
                "activity_breakdown": wellbeing_metrics.activity_breakdown
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@app.delete("/v1/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a generated report and associated files"""
    # This would typically interact with a database
    # For now, just return success
    return {"message": f"Report {report_id} deletion requested"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
