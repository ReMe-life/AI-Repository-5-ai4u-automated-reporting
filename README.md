# luki-modules-reporting

> **This repository is archived.** Active development continues in a private repository. This public version reflects the ReMeLife integration era and is no longer maintained.

Reporting module for LUKi. Generates wellbeing reports, trend analysis, and visualisations from ELR data and activity logs.

## What It Does

- Aggregates activity, mood, and engagement metrics over configurable time windows
- Detects trends and anomalies in wellbeing data (seasonal decomposition, z-score)
- Generates natural language summaries from structured metrics (Jinja2 templates, optional LLM)
- Produces chart visualisations (matplotlib)
- Exposes report generation as callable tools for the LUKi agent

## Stack

- **NLG:** Jinja2 templates + rule-based sentence assembly, optional LLM summarisation
- **Analytics:** pandas, statsmodels (seasonal decomposition), scipy
- **Visualisation:** matplotlib, plotly
- **API:** FastAPI
- **Deployment:** Docker on Railway

## Structure

```
luki_modules_reporting/
├── main.py                  # FastAPI app, all endpoints
├── config.py                # Service configuration
├── data/
│   ├── schemas.py           # Pydantic models (ActivityLog, MoodEntry, etc.)
│   └── loaders.py           # Metric fetching from memory service
├── analytics/
│   ├── aggregate.py         # Metric rollups and statistics
│   ├── trends.py            # Time-series trend detection
│   ├── wellbeing.py         # Wellbeing score computation
│   └── viz.py               # Chart generation (PNG/SVG)
├── nlg/
│   ├── templates/
│   │   ├── family.j2        # Family-audience report template
│   │   └── clinician.j2     # Clinician-audience report template
│   ├── builder.py           # Report assembly from stats + templates
│   └── summariser.py        # LLM summarisation hook
└── interfaces/
    └── agent_tools.py       # Functions exposed to LUKi agent
```

## Setup

```bash
git clone git@github.com:ReMeLife/luki-modules-reporting.git
cd luki-modules-reporting
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn luki_modules_reporting.main:app --reload --port 8103
```

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/{user_id}/wellbeing` | Generate wellbeing report |
| GET | `/reports/{user_id}/trends` | Analyse trends over time window |
| POST | `/reports/generate` | Generate text narrative |
| GET | `/health` | Service health |

## Agent Tools

- `generate_wellbeing_report` — text report for a given time window
- `get_activity_trends` — trend analysis with anomaly detection
- `create_visual_report` — chart generation

## License

Apache License 2.0. Copyright 2025 Singularities Ltd / ReMeLife. See [LICENSE](LICENSE).
