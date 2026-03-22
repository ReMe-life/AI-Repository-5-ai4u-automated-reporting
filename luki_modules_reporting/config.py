"""Configuration management for LUKi Modules Reporting

Handles environment variables, service settings, and feature flags.
Uses Pydantic for validation and type safety.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class ReportingSettings(BaseSettings):
    """Configuration settings for LUKi Reporting Module"""
    
    # Service Configuration
    service_name: str = "luki-modules-reporting"
    service_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    
    # Data Sources
    memory_service_url: str = Field(
        default="http://localhost:8002",
        description="URL for LUKi Memory Service"
    )
    api_gateway_url: str = Field(
        default="http://localhost:8080",
        description="URL for LUKi API Gateway"
    )
    security_service_url: str = Field(
        default="http://localhost:8103",
        description="URL for LUKi Security & Privacy Service"
    )
    
    # Report Generation
    default_report_days: int = Field(
        default=7,
        description="Default number of days for report generation"
    )
    max_report_days: int = Field(
        default=90,
        description="Maximum number of days allowed for reports"
    )
    
    # Template Configuration
    template_dir: str = Field(
        default="luki_modules_reporting/nlg/templates",
        description="Directory containing report templates"
    )
    
    # Output Configuration
    output_dir: str = Field(
        default="outputs",
        description="Directory for generated reports and charts"
    )
    chart_format: str = Field(
        default="png",
        description="Default format for generated charts (png, svg, pdf)"
    )
    chart_dpi: int = Field(
        default=300,
        description="DPI for generated chart images"
    )
    
    # Analytics Configuration
    trend_analysis_enabled: bool = Field(
        default=True,
        description="Enable trend analysis in reports"
    )
    statistical_significance_threshold: float = Field(
        default=0.05,
        description="P-value threshold for statistical significance"
    )
    
    # Privacy & Compliance
    anonymize_data: bool = Field(
        default=True,
        description="Anonymize sensitive data in reports"
    )
    respect_consent_flags: bool = Field(
        default=True,
        description="Respect user consent flags when generating reports"
    )
    
    # Caching
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching for report data"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds (1 hour default)"
    )
    
    class Config:
        env_prefix = "LUKI_REPORTING_"
        case_sensitive = False


# Global settings instance
settings = ReportingSettings()
