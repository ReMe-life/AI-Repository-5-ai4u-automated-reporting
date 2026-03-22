"""LUKi Modules Reporting

Automated wellbeing reports, trend analysis & NLG for ReMeLife.
Generates clear, human-readable reports from ELR® data, activity logs, and engagement metrics.
"""

__version__ = "0.1.0"
__author__ = "ReMeLife / Singularities Ltd"

from .config import ReportingSettings

__all__ = [
    "ReportingSettings",
    "__version__",
    "__author__",
]
