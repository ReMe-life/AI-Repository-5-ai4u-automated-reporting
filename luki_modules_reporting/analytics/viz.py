"""Visualization utilities for wellbeing reports

Generates charts and plots for activity, mood, and engagement data
using matplotlib and plotly for static export.
"""

import os
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from ..data.schemas import ActivityLog, MoodEntry, EngagementMetric, WellbeingMetrics
from ..config import settings


class ChartGenerator:
    """Generates various charts for wellbeing reports"""
    
    def __init__(self, output_dir: Optional[str] = None, chart_format: Optional[str] = None, dpi: Optional[int] = None):
        self.output_dir = output_dir or settings.output_dir
        self.chart_format = chart_format or settings.chart_format
        self.dpi = dpi or settings.chart_dpi
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def activity_timeline_chart(self, activities: List[ActivityLog], out_path: Optional[str] = None) -> str:
        """Generate activity timeline chart"""
        if not activities:
            return self._create_empty_chart("No activity data available", out_path or "activity_timeline.png")
        
        # Prepare data
        df = pd.DataFrame([{
            'date': a.timestamp.date(),
            'activity_type': a.activity_type.value,
            'duration': a.duration_minutes or 0,
            'engagement': a.engagement_level.value
        } for a in activities])
        
        # Group by date and activity type
        daily_activities = df.groupby(['date', 'activity_type']).agg({
            'duration': 'sum',
            'engagement': 'count'
        }).reset_index()
        
        # Create stacked bar chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Duration chart
        pivot_duration = daily_activities.pivot(index='date', columns='activity_type', values='duration').fillna(0)
        pivot_duration.plot(kind='bar', stacked=True, ax=ax1, colormap='Set3')
        ax1.set_title('Daily Activity Duration by Type')
        ax1.set_ylabel('Duration (minutes)')
        ax1.legend(title='Activity Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Activity count chart
        pivot_count = daily_activities.pivot(index='date', columns='activity_type', values='engagement').fillna(0)
        pivot_count.plot(kind='bar', stacked=True, ax=ax2, colormap='Set3')
        ax2.set_title('Daily Activity Count by Type')
        ax2.set_ylabel('Number of Activities')
        ax2.legend(title='Activity Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Save chart
        output_path = out_path or os.path.join(self.output_dir, "activity_timeline.png")
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def mood_trend_chart(self, mood_entries: List[MoodEntry], out_path: Optional[str] = None) -> str:
        """Generate mood trend chart"""
        if not mood_entries:
            return self._create_empty_chart("No mood data available", out_path or "mood_trend.png")
        
        # Convert mood levels to numeric
        mood_scores = {
            "very_low": 1, "low": 2, "neutral": 3, "high": 4, "very_high": 5
        }
        
        # Prepare data
        df = pd.DataFrame([{
            'date': m.timestamp.date(),
            'mood_score': mood_scores[m.mood_level.value],
            'energy_level': m.energy_level,
            'anxiety_level': m.anxiety_level,
            'sleep_quality': m.sleep_quality
        } for m in mood_entries])
        
        # Group by date and calculate daily averages
        daily_mood = df.groupby('date').agg({
            'mood_score': 'mean',
            'energy_level': 'mean',
            'anxiety_level': 'mean',
            'sleep_quality': 'mean'
        }).reset_index()
        
        # Create multi-line chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(daily_mood['date'], daily_mood['mood_score'], marker='o', label='Mood', linewidth=2)
        
        if daily_mood['energy_level'].notna().any():
            # Normalize energy to 1-5 scale
            ax.plot(daily_mood['date'], daily_mood['energy_level'] / 2, marker='s', label='Energy', alpha=0.7)
        
        if daily_mood['sleep_quality'].notna().any():
            # Normalize sleep quality to 1-5 scale  
            ax.plot(daily_mood['date'], daily_mood['sleep_quality'] / 2, marker='^', label='Sleep Quality', alpha=0.7)
        
        ax.set_title('Mood and Wellbeing Trends')
        ax.set_ylabel('Score (1-5)')
        ax.set_ylim(0.5, 5.5)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save chart
        output_path = out_path or os.path.join(self.output_dir, "mood_trend.png")
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def engagement_overview_chart(self, metrics: List[EngagementMetric], out_path: Optional[str] = None) -> str:
        """Generate engagement overview chart"""
        if not metrics:
            return self._create_empty_chart("No engagement data available", out_path or "engagement_overview.png")
        
        # Prepare data
        df = pd.DataFrame([{
            'date': m.date,
            'total_activities': m.total_activities,
            'avg_engagement_score': m.avg_engagement_score,
            'social_interactions': m.social_interactions,
            'family_engagement_minutes': m.family_engagement_minutes
        } for m in metrics])
        
        # Create subplot layout
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Daily activities
        ax1.bar(df['date'], df['total_activities'], color='skyblue', alpha=0.7)
        ax1.set_title('Daily Activities')
        ax1.set_ylabel('Number of Activities')
        ax1.tick_params(axis='x', rotation=45)
        
        # Engagement score
        ax2.plot(df['date'], df['avg_engagement_score'], marker='o', color='green', linewidth=2)
        ax2.set_title('Average Engagement Score')
        ax2.set_ylabel('Engagement Score (0-1)')
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Social interactions
        ax3.bar(df['date'], df['social_interactions'], color='orange', alpha=0.7)
        ax3.set_title('Daily Social Interactions')
        ax3.set_ylabel('Number of Interactions')
        ax3.tick_params(axis='x', rotation=45)
        
        # Family engagement time
        ax4.bar(df['date'], df['family_engagement_minutes'], color='purple', alpha=0.7)
        ax4.set_title('Family Engagement Time')
        ax4.set_ylabel('Minutes')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save chart
        output_path = out_path or os.path.join(self.output_dir, "engagement_overview.png")
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def weekly_summary_chart(self, wellbeing_metrics: WellbeingMetrics, out_path: Optional[str] = None) -> str:
        """Generate comprehensive weekly summary chart"""
        # WellbeingMetrics contains aggregated data, not raw logs
        if wellbeing_metrics.total_activities == 0:
            return self._create_empty_chart("No data available for weekly summary", out_path or "weekly_summary.png")
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Daily Activities', 'Mood Trends', 'Engagement Score', 'Activity Types'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Use aggregated metrics data instead of undefined variables
        # Total activities bar
        fig.add_trace(
            go.Bar(x=["Total Activities"], y=[wellbeing_metrics.total_activities], 
                   name="Activities", marker_color='lightblue'),
            row=1, col=1
        )
        
        # Mood score if available
        if wellbeing_metrics.avg_mood_score is not None:
            fig.add_trace(
                go.Bar(x=["Avg Mood"], y=[wellbeing_metrics.avg_mood_score], 
                       name="Mood", marker_color='green'),
                row=1, col=2
            )
        
        # Engagement score
        fig.add_trace(
            go.Bar(x=["Avg Engagement"], y=[wellbeing_metrics.avg_engagement_score], 
                   name="Engagement", marker_color='orange'),
            row=2, col=1
        )
        
        # Activity type breakdown
        if wellbeing_metrics.activity_breakdown:
            types = list(wellbeing_metrics.activity_breakdown.keys())
            counts = list(wellbeing_metrics.activity_breakdown.values())
            
            fig.add_trace(
                go.Pie(labels=types, values=counts, name="Activity Types"),
                row=2, col=2
            )
        
        fig.update_layout(height=800, showlegend=True, title_text="Weekly Wellbeing Summary")
        
        # Save as HTML first, then convert to image
        output_path = out_path or os.path.join(self.output_dir, "weekly_summary.png")
        
        # For PNG output, we'll use matplotlib instead
        return self._create_matplotlib_summary(wellbeing_metrics, output_path)
    
    def _create_matplotlib_summary(self, wellbeing_metrics: WellbeingMetrics, output_path: str) -> str:
        """Create matplotlib version of weekly summary"""
        # Use aggregated metrics data
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Create summary charts using aggregated metrics
        # Total activities bar
        ax1.bar(['Total Activities'], [wellbeing_metrics.total_activities], color='lightblue', alpha=0.7)
        ax1.set_title('Total Activities')
        ax1.set_ylabel('Number of Activities')
        
        # Engagement score gauge
        ax2.bar(['Avg Engagement'], [wellbeing_metrics.avg_engagement_score], color='green', alpha=0.7)
        ax2.set_title('Average Engagement Score')
        ax2.set_ylabel('Engagement Score')
        ax2.set_ylim(0, 1)
        
        # Activity type breakdown
        if wellbeing_metrics.activity_breakdown:
            types = list(wellbeing_metrics.activity_breakdown.keys())
            counts = list(wellbeing_metrics.activity_breakdown.values())
            
            ax3.pie(counts, labels=types, autopct='%1.1f%%')
            ax3.set_title('Activity Types Distribution')
        else:
            ax3.text(0.5, 0.5, 'No activity breakdown', ha='center', va='center', transform=ax3.transAxes)
        
        # Mood score if available
        if wellbeing_metrics.avg_mood_score is not None:
            ax4.bar(['Avg Mood'], [wellbeing_metrics.avg_mood_score], color='orange', alpha=0.7)
            ax4.set_title('Average Mood Score')
            ax4.set_ylabel('Mood Score')
            ax4.set_ylim(0, 1)
        else:
            ax4.text(0.5, 0.5, 'No mood data', ha='center', va='center', transform=ax4.transAxes)
            ax4.axis('off')
        
        plt.suptitle('Weekly Wellbeing Summary', fontsize=16, y=0.98)
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _create_empty_chart(self, message: str, out_path: str) -> str:
        """Create an empty chart with a message"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=16, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        full_path = os.path.join(self.output_dir, out_path)
        plt.savefig(full_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return full_path


# Convenience functions matching README examples
def activity_chart(metrics: Dict[str, List], out_path: str = "outputs/activity.png") -> str:
    """Generate activity chart - matches README example"""
    generator = ChartGenerator()
    activities = metrics.get("activity_logs", [])
    
    if not activities:
        return generator._create_empty_chart("No activity data", out_path)
    
    return generator.activity_timeline_chart(activities, out_path)


def mood_chart(metrics: Dict[str, List], out_path: str = "outputs/mood.png") -> str:
    """Generate mood chart"""
    generator = ChartGenerator()
    mood_entries = metrics.get("mood_entries", [])
    
    if not mood_entries:
        return generator._create_empty_chart("No mood data", out_path)
    
    return generator.mood_trend_chart(mood_entries, out_path)


def engagement_chart(metrics: Dict[str, List], out_path: str = "outputs/engagement.png") -> str:
    """Generate engagement chart"""
    generator = ChartGenerator()
    engagement_metrics = metrics.get("engagement_metrics", [])
    
    if not engagement_metrics:
        return generator._create_empty_chart("No engagement data", out_path)
    
    return generator.engagement_overview_chart(engagement_metrics, out_path)
