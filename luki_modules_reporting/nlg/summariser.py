"""Optional LLM summarization for reports

Provides hooks for LLM-assisted summarization and narrative enhancement.
This module can integrate with the core LUKi agent for advanced NLG.
"""

from typing import Optional, Dict, Any
import asyncio
import httpx

from ..data.schemas import WellbeingMetrics, ReportData
from ..config import settings


class ReportSummariser:
    """Optional LLM-powered report summarization"""
    
    def __init__(self, agent_url: Optional[str] = None):
        self.agent_url = agent_url or settings.api_gateway_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def enhance_narrative(
        self, 
        base_narrative: str,
        wellbeing_metrics: WellbeingMetrics,
        audience: str = "family"
    ) -> str:
        """Enhance narrative using LLM"""
        
        try:
            # Create prompt for LLM enhancement
            prompt = self._create_enhancement_prompt(base_narrative, wellbeing_metrics, audience)
            
            # Call LUKi agent for enhancement
            response = await self.client.post(
                f"{self.agent_url}/v1/chat",
                json={
                    "message": prompt,
                    "user_id": wellbeing_metrics.user_id,
                    "context": {
                        "task": "report_enhancement",
                        "audience": audience
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("reply", base_narrative)
            else:
                print(f"LLM enhancement failed: {response.status_code}")
                return base_narrative
        
        except Exception as e:
            print(f"Error in LLM enhancement: {e}")
            return base_narrative
    
    def _create_enhancement_prompt(
        self, 
        base_narrative: str, 
        wellbeing_metrics: WellbeingMetrics,
        audience: str
    ) -> str:
        """Create prompt for narrative enhancement"""
        
        if audience == "clinician":
            return f"""Please enhance this clinical wellbeing report to be more professional and medically precise while maintaining all key information:

{base_narrative}

Requirements:
- Keep all numerical data and metrics exactly as provided
- Use appropriate medical terminology
- Maintain clinical objectivity
- Ensure recommendations are evidence-based
- Keep the structure and sections intact

Enhanced report:"""
        
        else:
            return f"""Please enhance this family wellbeing report to be more warm, personal, and encouraging while maintaining all key information:

{base_narrative}

Requirements:
- Keep all data and insights exactly as provided
- Use warm, family-friendly language
- Be encouraging and supportive in tone
- Make technical information accessible
- Maintain the caring, personal approach

Enhanced report:"""
    
    async def generate_executive_summary(
        self, 
        wellbeing_metrics: WellbeingMetrics,
        audience: str = "family"
    ) -> str:
        """Generate executive summary using LLM"""
        
        try:
            prompt = f"""Generate a brief executive summary (2-3 sentences) for a wellbeing report with these key metrics:

- Daily activities: {wellbeing_metrics.avg_daily_activities:.1f} per day
- Engagement score: {wellbeing_metrics.avg_engagement_score:.2f}/1.0
- Social interactions: {wellbeing_metrics.total_social_interactions}
- Activity trend: {wellbeing_metrics.activity_trend}
- Engagement trend: {wellbeing_metrics.engagement_trend}

Audience: {audience}
Tone: {"Professional and clinical" if audience == "clinician" else "Warm and family-friendly"}

Summary:"""
            
            response = await self.client.post(
                f"{self.agent_url}/v1/chat",
                json={
                    "message": prompt,
                    "user_id": wellbeing_metrics.user_id,
                    "context": {
                        "task": "executive_summary",
                        "audience": audience
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("reply", "Summary generation unavailable")
            else:
                return "Summary generation unavailable"
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation unavailable"
    
    async def generate_insights(
        self, 
        wellbeing_metrics: WellbeingMetrics,
        max_insights: int = 5
    ) -> list:
        """Generate additional insights using LLM"""
        
        try:
            prompt = f"""Based on these wellbeing metrics, generate {max_insights} key insights that might not be immediately obvious:

Metrics:
- Activities: {wellbeing_metrics.total_activities} total, {wellbeing_metrics.avg_daily_activities:.1f}/day
- Engagement: {wellbeing_metrics.avg_engagement_score:.2f}/1.0
- Social: {wellbeing_metrics.total_social_interactions} interactions
- Mood: {wellbeing_metrics.avg_mood_score or 'N/A'}
- Trends: Activity {wellbeing_metrics.activity_trend}, Engagement {wellbeing_metrics.engagement_trend}

Activity breakdown: {wellbeing_metrics.activity_breakdown}

Generate insights as a JSON array of strings, focusing on patterns, correlations, or recommendations that require deeper analysis.

Insights:"""
            
            response = await self.client.post(
                f"{self.agent_url}/v1/chat",
                json={
                    "message": prompt,
                    "user_id": wellbeing_metrics.user_id,
                    "context": {
                        "task": "insight_generation",
                        "format": "json_array"
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "[]")
                
                # Try to parse as JSON array
                try:
                    import json
                    insights = json.loads(reply)
                    return insights[:max_insights] if isinstance(insights, list) else []
                except:
                    # Fallback: split by lines and clean up
                    lines = reply.strip().split('\n')
                    insights = [line.strip('- ').strip() for line in lines if line.strip()]
                    return insights[:max_insights]
            
            return []
        
        except Exception as e:
            print(f"Error generating insights: {e}")
            return []


# Convenience functions
async def enhance_report_with_llm(
    report_data: ReportData,
    enhance_narrative: bool = True,
    generate_summary: bool = True
) -> ReportData:
    """Enhance complete report using LLM"""
    
    summariser = ReportSummariser()
    
    try:
        # Enhance narrative if requested
        if enhance_narrative and report_data.narrative_summary:
            enhanced_narrative = await summariser.enhance_narrative(
                report_data.narrative_summary,
                report_data.wellbeing_metrics,
                report_data.audience
            )
            report_data.narrative_summary = enhanced_narrative
        
        # Generate executive summary if requested
        if generate_summary:
            executive_summary = await summariser.generate_executive_summary(
                report_data.wellbeing_metrics,
                report_data.audience
            )
            report_data.generation_metadata["executive_summary"] = executive_summary
        
        # Generate additional insights
        additional_insights = await summariser.generate_insights(
            report_data.wellbeing_metrics
        )
        if additional_insights:
            report_data.generation_metadata["llm_insights"] = additional_insights
        
        return report_data
    
    finally:
        await summariser.close()
