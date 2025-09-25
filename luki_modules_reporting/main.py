"""
LUKi Modules Reporting - FastAPI Application
Provides wellbeing reports, analytics, and data visualization
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import structlog

from .config import settings

# Try to import modules, fall back to mock classes if not available
try:
    from .analytics.wellbeing import WellbeingAnalyzer
except ImportError:
    class WellbeingAnalyzer:
        async def generate_report(self, user_id: str, days: int = 7):
            return {"status": "mock", "user_id": user_id, "report": "Mock wellbeing report"}
        
        async def get_trends(self, user_id: str):
            return {"user_id": user_id, "trends": {"mood": "improving", "activity": "stable"}}

try:
    from .nlg.report_generator import ReportGenerator
except ImportError:
    class ReportGenerator:
        async def generate_text_report(self, data: dict):
            return "Mock generated report text based on data"
        
        async def generate_summary(self, data: dict):
            return {"summary": "Mock summary", "key_insights": ["Mock insight 1", "Mock insight 2"]}

try:
    from .data.aggregator import DataAggregator
except ImportError:
    class DataAggregator:
        async def aggregate_user_data(self, user_id: str, days: int):
            return {"user_id": user_id, "data": "mock aggregated data", "days": days}
        
        async def get_statistics(self, user_id: str):
            return {"user_id": user_id, "stats": {"total_activities": 42, "avg_mood": 7.5}}

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize services
wellbeing_analyzer = None
report_generator = None
data_aggregator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global wellbeing_analyzer, report_generator, data_aggregator
    
    logger.info("Starting LUKi Modules Reporting", version=settings.service_version)
    
    try:
        # Initialize services
        wellbeing_analyzer = WellbeingAnalyzer()
        report_generator = ReportGenerator()
        data_aggregator = DataAggregator()
        
        logger.info("✅ Reporting services initialized successfully")
        
    except Exception as e:
        logger.error("❌ Failed to initialize reporting services", error=str(e))
        # Continue startup even if some services fail
        
    yield
    
    logger.info("Shutting down LUKi Modules Reporting")

# Create FastAPI app
app = FastAPI(
    title="LUKi Modules Reporting",
    description="Wellbeing reports, analytics, and data visualization for LUKi",
    version=settings.service_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
        "components": {
            "wellbeing_analyzer": wellbeing_analyzer is not None,
            "report_generator": report_generator is not None,
            "data_aggregator": data_aggregator is not None
        }
    }
    
    return status

@app.post("/reports/{user_id}/wellbeing")
async def generate_wellbeing_report(user_id: str, days: int = None):
    """Generate wellbeing report for user"""
    if not wellbeing_analyzer:
        raise HTTPException(status_code=503, detail="Wellbeing analyzer not available")
    
    report_days = days or settings.default_report_days
    if report_days > settings.max_report_days:
        raise HTTPException(status_code=400, detail=f"Maximum report days is {settings.max_report_days}")
    
    try:
        report = await wellbeing_analyzer.generate_report(user_id, report_days)
        logger.info("Wellbeing report generated", user_id=user_id, days=report_days)
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error("Failed to generate wellbeing report", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{user_id}/trends")
async def get_trends(user_id: str):
    """Get user trends and patterns"""
    if not wellbeing_analyzer:
        raise HTTPException(status_code=503, detail="Wellbeing analyzer not available")
    
    try:
        trends = await wellbeing_analyzer.get_trends(user_id)
        return {"user_id": user_id, "trends": trends}
    except Exception as e:
        logger.error("Failed to get trends", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/generate")
async def generate_text_report(report_data: dict):
    """Generate natural language report from data"""
    if not report_generator:
        raise HTTPException(status_code=503, detail="Report generator not available")
    
    try:
        text_report = await report_generator.generate_text_report(report_data)
        return {"status": "success", "report": text_report}
    except Exception as e:
        logger.error("Failed to generate text report", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/summarize")
async def summarize_data(data: dict):
    """Generate summary and key insights from data"""
    if not report_generator:
        raise HTTPException(status_code=503, detail="Report generator not available")
    
    try:
        summary = await report_generator.generate_summary(data)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error("Failed to generate summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{user_id}/aggregate")
async def aggregate_user_data(user_id: str, days: int = None):
    """Aggregate user data for analysis"""
    if not data_aggregator:
        raise HTTPException(status_code=503, detail="Data aggregator not available")
    
    report_days = days or settings.default_report_days
    
    try:
        aggregated_data = await data_aggregator.aggregate_user_data(user_id, report_days)
        return {"status": "success", "data": aggregated_data}
    except Exception as e:
        logger.error("Failed to aggregate user data", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{user_id}/statistics")
async def get_user_statistics(user_id: str):
    """Get user statistics and metrics"""
    if not data_aggregator:
        raise HTTPException(status_code=503, detail="Data aggregator not available")
    
    try:
        stats = await data_aggregator.get_statistics(user_id)
        return {"user_id": user_id, "statistics": stats}
    except Exception as e:
        logger.error("Failed to get user statistics", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LUKi Modules Reporting",
        "version": settings.service_version,
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
