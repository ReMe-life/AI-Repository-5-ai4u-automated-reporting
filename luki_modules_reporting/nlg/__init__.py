"""Natural Language Generation module for LUKi Reporting

Contains template system, narrative builders, and optional LLM summarization.
"""

from .builder import build_report, ReportBuilder
from .summariser import ReportSummariser

__all__ = [
    "build_report",
    "ReportBuilder",
    "ReportSummariser",
]
