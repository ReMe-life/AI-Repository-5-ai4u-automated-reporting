"""Basic functionality tests for LUKi Modules Reporting

Tests core functionality including data loading, aggregation, 
report generation, and chart creation.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from luki_modules_reporting.data.loaders import load_demo_metrics, generate_demo_activity_logs
from luki_modules_reporting.analytics.aggregate import aggregate_metrics
from luki_modules_reporting.nlg.builder import build_report
from luki_modules_reporting.analytics.viz import activity_chart
from luki_modules_reporting.interfaces.agent_tools import generate_wellbeing_report


class TestDataLoading:
    """Test data loading functionality"""
    
    def test_load_demo_metrics(self):
        """Test demo metrics loading"""
        user_id = "test_user_123"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        metrics = load_demo_metrics(user_id, start_date, end_date)
        
        assert "activity_logs" in metrics
        assert "mood_entries" in metrics
        assert "engagement_metrics" in metrics
        
        # Check data is generated for the right period
        activity_logs = metrics["activity_logs"]
        assert len(activity_logs) > 0
        assert all(log.user_id == user_id for log in activity_logs)
    
    def test_generate_demo_activity_logs(self):
        """Test activity log generation"""
        user_id = "test_user_456"
        start_date = date.today() - timedelta(days=3)
        end_date = date.today()
        
        logs = generate_demo_activity_logs(user_id, start_date, end_date, activities_per_day=2)
        
        assert len(logs) > 0
        assert all(log.user_id == user_id for log in logs)
        assert all(start_date <= log.timestamp.date() <= end_date for log in logs)


class TestAnalytics:
    """Test analytics functionality"""
    
    def test_aggregate_metrics(self):
        """Test metrics aggregation"""
        # Generate test data
        user_id = "test_user_789"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        metrics_data = load_demo_metrics(user_id, start_date, end_date)
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        assert wellbeing_metrics.user_id == user_id
        assert wellbeing_metrics.total_activities >= 0
        assert 0 <= wellbeing_metrics.avg_engagement_score <= 1
        assert wellbeing_metrics.start_date == start_date
        assert wellbeing_metrics.end_date == end_date
    
    def test_empty_metrics_aggregation(self):
        """Test aggregation with empty data"""
        empty_data = {
            "activity_logs": [],
            "mood_entries": [],
            "engagement_metrics": []
        }
        
        wellbeing_metrics = aggregate_metrics(empty_data)
        
        assert wellbeing_metrics.total_activities == 0
        assert wellbeing_metrics.avg_engagement_score == 0.0


class TestReportGeneration:
    """Test report generation functionality"""
    
    def test_build_family_report(self):
        """Test family report generation"""
        # Generate test data
        user_id = "test_family_user"
        metrics_data = load_demo_metrics(
            user_id, 
            date.today() - timedelta(days=7), 
            date.today()
        )
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        # Build report
        report_text = build_report(wellbeing_metrics, audience="family")
        
        assert isinstance(report_text, str)
        assert len(report_text) > 100  # Should be substantial
        assert "Weekly Wellbeing Report" in report_text
        assert user_id in report_text or "loved one" in report_text.lower()
    
    def test_build_clinician_report(self):
        """Test clinician report generation"""
        # Generate test data
        user_id = "test_clinical_user"
        metrics_data = load_demo_metrics(
            user_id,
            date.today() - timedelta(days=7),
            date.today()
        )
        
        # Aggregate metrics
        wellbeing_metrics = aggregate_metrics(metrics_data)
        
        # Build report
        report_text = build_report(wellbeing_metrics, audience="clinician")
        
        assert isinstance(report_text, str)
        assert len(report_text) > 100
        assert "Clinical Wellbeing Report" in report_text
        assert "Patient ID" in report_text


class TestVisualization:
    """Test chart generation functionality"""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_activity_chart_generation(self, mock_close, mock_savefig):
        """Test activity chart generation"""
        # Generate test data
        metrics_data = load_demo_metrics(
            "test_viz_user",
            date.today() - timedelta(days=7),
            date.today()
        )
        
        # Generate chart
        chart_path = activity_chart(metrics_data, "test_activity.png")
        
        assert isinstance(chart_path, str)
        assert "test_activity.png" in chart_path
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()


class TestAgentTools:
    """Test LangChain agent tools"""
    
    @patch('luki_modules_reporting.interfaces.agent_tools.fetch_metrics_window')
    def test_generate_wellbeing_report_tool(self, mock_fetch):
        """Test wellbeing report generation tool"""
        # Mock data
        mock_metrics_data = load_demo_metrics(
            "test_agent_user",
            date.today() - timedelta(days=7),
            date.today()
        )
        
        # Mock the async function
        async def mock_fetch_metrics(*args, **kwargs):
            return mock_metrics_data
        
        mock_fetch.return_value = mock_fetch_metrics()
        
        # Test tool
        result = generate_wellbeing_report(
            user_id="test_agent_user",
            days=7,
            audience="family"
        )
        
        assert isinstance(result, str)
        assert len(result) > 50  # Should have substantial content


class TestConfiguration:
    """Test configuration management"""
    
    def test_settings_import(self):
        """Test that settings can be imported and have expected values"""
        from luki_modules_reporting.config import settings
        
        assert settings.service_name == "luki-modules-reporting"
        assert settings.service_version == "0.1.0"
        assert settings.default_report_days == 7
        assert settings.chart_format in ["png", "svg", "pdf"]


if __name__ == "__main__":
    pytest.main([__file__])
