<p align="center">
  <img src="Logo.jpg" alt="Geo-INQUIRE logo" width="320">
</p>

# ILM Geo-INQUIRE Dashboard

Implementation Level Matrix (ILM) monitoring dashboard for the **Geo-INQUIRE**
project. It tracks the maturity of **Virtual Access (VA)** services and the
progress of **Transnational Access (TA)** projects, for the research team and
project reporting.

> Funded by the European Union — Horizon Europe, Grant Agreement No. **101058518**
> (Geo-INQUIRE). 

---

## Features

- 🔐 Password-protected access (session-based)
- 📡 ILM - Live Google Sheets integration, with an Excel snapshot as automatic fallback
- 📊 VA analytics — implementation status, RI coverage, and a **TRL maturity matrix** (1–9)
- 🌍 TA descriptive overview — applications per installation, project-stage progress,
  a completion pipeline, and a world map of TA users
- 🎯 KPI tracking (test users, datasets, uptime, …)
- 🧾 Every figure cites its source spreadsheet column and exports as **300-DPI PNG**
- 🗂️ Year tabs (2023–2026) for VA, from frozen yearly snapshots

## Tech stack

Python · Streamlit · Plotly · pandas · openpyxl · kaleido

---

## Installation

**Prerequisites:** Python 3.9+ and (for live data) a Google service-account key.

```bash
git clone https://github.com/YOUR_USERNAME/ILM.git
cd ILM
pip install -r requirements.txt
streamlit run ilm_dashboard_app.py
```

Credentials are read from `.streamlit/secrets.toml` locally and from **Streamlit
Secrets** in the cloud. A real key file is **never** committed (see *Security*).

---

## Usage

**Pages**

| Page | Purpose |
|------|---------|
| Dashboard | Overview and key metrics |
| Analytics | Detailed analysis, RI matrix, TRL maturity |
| KPI | Key Performance Indicators |
| Data | Raw data tables with readable headers |
| Contact | Project information |

**Switch project** in the sidebar: *Virtual Access* ↔ *Transnational Access*.
The available tabs and figures adapt to the selected project.

---

## Data sources

- **Primary:** Google Sheet from the ILM table and mirrored — tabs `ILM_Connector` (VA) and `ILM_Connector_TA` (TA),
  read via the Google Sheets API.
- **Fallback:** `ILM_Python_2.xlsx` (same two tabs).
- **History:** frozen yearly snapshots in `ILM_Old/` feed the VA year tabs.

---

## Deployment (Streamlit Community Cloud)

1. Push to GitHub (include `ILM_Python_2.xlsx` and `ILM_Old/*.xlsx` — they may be
   skipped by `.gitignore`, so add with `git add -f`).
2. Connect the repo at <https://share.streamlit.io>.
3. Add the service-account block under **Settings → Secrets**.
4. **Reboot** the app after any change to data loaders, cache signatures, or
   `requirements.txt`.

---

## Project structure

```
ILM/
├── ilm_dashboard_app.py      # main application
├── requirements.txt          # dependencies (kaleido pinned for PNG export)
├── ILM_Python_2.xlsx         # data snapshot / Excel fallback
├── ILM_Old/                  # frozen yearly snapshots (VA year tabs)
├── README.md
├── .gitignore
└── .streamlit/
    ├── config.toml           # light theme
    └── secrets.toml          # credentials — NOT in Git
```

---

## Security

- ⚠️ Never commit credentials — keep `*.json` and `.streamlit/secrets.toml` out of Git.
- ⚠️ Use Streamlit Secrets for cloud deployment; reboot after updating them.
- ⚠️ Rotate the service-account key periodically.

---

## Authors & license

Developed by **Juliano Ramanantsoa** (assisted by Claude),
University of Bergen.

- **Code / software:** open source under the [MIT License](LICENSE).
- **ILM data & content:** internal to the Geo-INQUIRE Project (not covered by the
  MIT license).

© 2024–2026 Juliano Ramanantsoa, Geo-INQUIRE Project,
University of Bergen.
Contact: heriniaina.j.ramanantsoa@uib.no

**Version 2.3** · June 2026

---
