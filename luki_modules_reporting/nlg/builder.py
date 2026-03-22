"""Report builder for natural language generation

Assembles narrative reports from aggregated statistics using Jinja2 templates.
Supports different audiences (family, clinician) with appropriate tone and detail.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from ..data.schemas import WellbeingMetrics, ReportData
from ..config import settings


class ReportBuilder:
    """Builds narrative reports from wellbeing metrics"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or settings.template_dir
        
        # Initialize Jinja2 environment
        if os.path.exists(self.template_dir):
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            # Fallback to package templates
            package_template_dir = os.path.join(
                os.path.dirname(__file__), 
                "templates"
            )
            self.env = Environment(
                loader=FileSystemLoader(package_template_dir),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
        
        # Add custom filters
        self.env.filters['title'] = str.title
        self.env.filters['format'] = lambda value, fmt: fmt % value
    
    def build_family_report(
        self, 
        wellbeing_metrics: WellbeingMetrics,
        user_name: str = "Your loved one",
        chart_paths: Optional[Dict[str, str]] = None
    ) -> str:
        """Build family-friendly report"""
        
        template = self.env.get_template("family.j2")
        
        context = {
            "user_name": user_name,
            "user_id": wellbeing_metrics.user_id,
            "start_date": wellbeing_metrics.start_date.strftime("%B %d, %Y"),
            "end_date": wellbeing_metrics.end_date.strftime("%B %d, %Y"),
            "wellbeing_metrics": wellbeing_metrics,
            "chart_paths": chart_paths or {},
            "generated_at": datetime.now(),
            "service_version": settings.service_version
        }
        
        return template.render(**context)
    
    def build_clinician_report(
        self,
        wellbeing_metrics: WellbeingMetrics,
        user_name: str = "Patient",
        chart_paths: Optional[Dict[str, str]] = None
    ) -> str:
        """Build clinical report"""
        
        template = self.env.get_template("clinician.j2")
        
        context = {
            "user_name": user_name,
            "user_id": wellbeing_metrics.user_id,
            "start_date": wellbeing_metrics.start_date.strftime("%Y-%m-%d"),
            "end_date": wellbeing_metrics.end_date.strftime("%Y-%m-%d"),
            "wellbeing_metrics": wellbeing_metrics,
            "chart_paths": chart_paths or {},
            "generated_at": datetime.now(),
            "service_version": settings.service_version,
            "timedelta": timedelta  # Make timedelta available in template
        }
        
        return template.render(**context)
    
    def build_custom_report(
        self,
        template_name: str,
        wellbeing_metrics: WellbeingMetrics,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build report using custom template"""
        
        template = self.env.get_template(template_name)
        
        context = {
            "wellbeing_metrics": wellbeing_metrics,
            "user_id": wellbeing_metrics.user_id,
            "start_date": wellbeing_metrics.start_date,
            "end_date": wellbeing_metrics.end_date,
            "generated_at": datetime.now(),
            "service_version": settings.service_version
        }
        
        if additional_context:
            context.update(additional_context)
        
        return template.render(**context)
    
    def build_complete_report_data(
        self,
        wellbeing_metrics: WellbeingMetrics,
        audience: str = "family",
        user_name: Optional[str] = None,
        chart_paths: Optional[Dict[str, str]] = None,
        activity_logs: Optional[list] = None,
        mood_entries: Optional[list] = None,
        daily_metrics: Optional[list] = None
    ) -> ReportData:
        """Build complete report data structure"""
        
        # Generate narrative based on audience
        if audience == "clinician":
            narrative = self.build_clinician_report(
                wellbeing_metrics, 
                user_name or "Patient",
                chart_paths
            )
        else:
            narrative = self.build_family_report(
                wellbeing_metrics,
                user_name or "Your loved one", 
                chart_paths
            )
        
        # Create report data
        report_data = ReportData(
            user_id=wellbeing_metrics.user_id,
            report_id=f"report_{wellbeing_metrics.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            report_period_start=wellbeing_metrics.start_date,
            report_period_end=wellbeing_metrics.end_date,
            audience=audience,
            wellbeing_metrics=wellbeing_metrics,
            activity_logs=activity_logs or [],
            mood_entries=mood_entries or [],
            daily_metrics=daily_metrics or [],
            narrative_summary=narrative,
            chart_paths=chart_paths or {},
            generation_metadata={
                "template_used": f"{audience}.j2",
                "generation_time": datetime.now().isoformat(),
                "user_name": user_name,
                "charts_included": len(chart_paths or {}),
                "service_version": settings.service_version
            }
        )
        
        return report_data


def build_report(stats: WellbeingMetrics, audience: str = "family", **kwargs) -> str:
    """Main report building function - matches README example"""
    
    builder = ReportBuilder()
    
    # Extract additional parameters
    user_name = kwargs.get("user_name")
    chart_paths = kwargs.get("chart_paths")
    
    if audience == "clinician":
        return builder.build_clinician_report(
            stats, 
            user_name or "Patient",
            chart_paths
        )
    else:
        return builder.build_family_report(
            stats,
            user_name or "Your loved one",
            chart_paths
        )
