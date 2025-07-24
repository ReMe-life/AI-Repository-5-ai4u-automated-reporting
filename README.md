# luki-modules-reporting  
*Automated wellbeing reports, trend analysis & NLG for ReMeLife*

---

## 1. Overview  
This module generates **clear, human-readable reports** from ELR® data, activity logs, and engagement metrics. It turns raw signals into **actionable summaries** for families, carers, and clinicians—automatically and on schedule.

---

## 2. Core Capabilities  
- **Natural Language Generation (NLG):** Convert structured metrics into caregiver-friendly narratives.  
- **Wellbeing Trend Analysis:** Detect changes in mood, engagement, cognition across time windows.  
- **Visual Summaries (optional):** Produce charts/plots (PNG/SVG) for dashboards or PDFs.  
- **Template System:** Reusable report templates per audience (family vs clinician).  
- **APIs & Agent Tools:** Expose “generate_report”, “get_trends” for the LUKi agent or external services.

---

## 3. Tech Stack  
- **NLG & Summarisation:**  
  - Lightweight templates (Jinja2) + rule-based sentence assembly  
  - Optional LLM-assisted summarisation via internal agent (not in this repo)  
- **Analytics & Time Series:** pandas, statsmodels/prophet (optional)  
- **Data Viz:** matplotlib / plotly (static export)  
- **Schema & Validation:** pydantic  
- **Orchestration:** LangChain tools to let LUKi trigger reports

---

## 4. Repository Structure  
~~~text
luki_modules_reporting/
├── __init__.py
├── config.py
├── data/
│   ├── schemas.py             # pydantic models: ActivityLog, MoodEntry, etc.
│   └── loaders.py             # adapters to pull metrics from stores/APIs
├── analytics/
│   ├── aggregate.py           # rollups, stats
│   ├── trends.py              # time-series analysis
│   └── viz.py                 # chart generators (png/svg)
├── nlg/
│   ├── templates/
│   │   ├── family.j2
│   │   └── clinician.j2
│   ├── builder.py             # assemble narrative from stats + templates
│   └── summariser.py          # optional LLM summarisation hook
├── interfaces/
│   ├── agent_tools.py         # LangChain @tool wrappers
│   └── api.py                 # FastAPI endpoints (optional)
└── tests/
~~~

---

## 5. Quick Start  
~~~bash
git clone git@github.com:REMELife/luki-modules-reporting.git
cd luki-modules-reporting
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
~~~

### Minimal example  
~~~python
from datetime import date, timedelta
from luki_modules_reporting.data.loaders import load_demo_metrics
from luki_modules_reporting.analytics.aggregate import aggregate_metrics
from luki_modules_reporting.nlg.builder import build_report

# 1. Load demo data (replace with real ELR/metrics adapters)
metrics = load_demo_metrics(user_id="user_123",
                            start=date.today()-timedelta(days=7),
                            end=date.today())

# 2. Aggregate & analyse
stats = aggregate_metrics(metrics)

# 3. Build narrative
report_text = build_report(stats, audience="family")  # or "clinician"
print(report_text)
~~~

### Generate chart & embed in report  
~~~python
from luki_modules_reporting.analytics.viz import activity_chart
fig_path = activity_chart(metrics, out_path="outputs/activity.png")

# pass fig_path to the template context inside build_report(...)
~~~

### Expose as LangChain tool  
~~~python
# interfaces/agent_tools.py
from langchain.tools import tool
from .nlg.builder import build_report
from .data.loaders import fetch_metrics_window
from .analytics.aggregate import aggregate_metrics

@tool("generate_wellbeing_report", return_direct=True)
def generate_wellbeing_report(user_id: str, days: int = 7) -> str:
    """Return a text wellbeing report for the last N days."""
    metrics = fetch_metrics_window(user_id=user_id, days=days)
    stats = aggregate_metrics(metrics)
    return build_report(stats, audience="family")
~~~

---

## 6. Privacy & Compliance  
- Do **not** log raw ELR text in this repo; only derived stats.  
- Encrypt any temporary files (figures, PDFs) at rest.  
- Respect consent flags—exclude hidden/sensitive categories from outputs.  
- Keep PHI out of public issues; use synthetic examples.

---

## 7. Roadmap  
- PDF export service (WeasyPrint / ReportLab)  
- Multi-language report templates (i18n)  
- Clinician-specific metrics (MMSE scores, med adherence)  
- Alerting: threshold-based notifications (e.g., sudden drop in engagement)  
- Differential privacy for aggregated reports across cohorts

---

## 8. Contributing  
Open to PRs. Follow `CONTRIBUTING.md`, keep tests green, and document new templates.

---

## 9. License  
**Apache-2.0** © 2025 Singularities Ltd / ReMeLife.  
(Add via GitHub “Choose a license template” or paste the standard Apache-2.0 text in `LICENSE`.)

---

**Turn data into insight. Help carers act, not guess.**
