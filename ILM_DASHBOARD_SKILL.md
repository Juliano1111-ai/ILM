# SKILL: ILM Geo-INQUIRE Dashboard

> **Purpose of this file.** This is the single, authoritative reference for the ILM
> Geo-INQUIRE Streamlit dashboard. Keep it in the Claude **Project knowledge** so
> every new conversation can search it — that way you never re-paste the codebase,
> the file paths, the deployment steps, or the "gotchas" again. When you ask Claude
> to change the dashboard, point it here first ("check the ILM skill").

---

## 1. What this project is

A password-protected **Streamlit** dashboard that visualises the Geo-INQUIRE
**Implementation Level Matrix (ILM)** for two access programmes:

- **Virtual Access (VA)** — the primary focus. Services/installations offered by
  research infrastructures, scored on implementation status, data representation,
  licensing, metadata standards, etc.
- **Transnational Access (TA)** — physical/virtual access to test-bed facilities,
  organised by funding **Call (1–4)**.

The project: *Geosphere INfrastructures for QUestions into Integrated REsearch* —
Horizon Europe, Research Infrastructures. Grant **101058518**, call
**HORIZON-INFRA-2021-SERV-01**, **1 Oct 2022 → 30 Sep 2026**, EU contribution
**€13,923,475.77**, **51 partners**, coordinated by **GFZ Helmholtz Centre for
Geosciences**. Main RIs in the data: **EPOS, EMSO, ChEESE** (plus ARISE, BedrettoLab, GFZ).

---

## 2. Where everything lives

**Local working directory (macOS):**
```
/Users/juliano/Library/CloudStorage/OneDrive-UniversityofBergen/Documents/
  GEO-INQUIRE/Geo-INQUIRE_Code/GoogleSheet_Python/ILM_Dashboard_correct2/
```

**Files in that directory:**
| File | Role |
|------|------|
| `ilm_dashboard_app.py` | The entire app (single file). |
| `requirements.txt` | Python deps. **`kaleido==0.2.1` is pinned** — do not loosen. |
| `.streamlit/config.toml` | Forces the light theme. **Must be inside `.streamlit/`**, not the repo root. |
| `valiant-splicer-409609-e34abed30cc1.json` | Google service-account creds. **Never commit** (in `.gitignore`). |
| `ILM_Python_2.xlsx` | Excel fallback if Google Sheets is unreachable. |
| `Logo.jpg` | Login-page + header logo. |
| `ILM_Old/` | Frozen historical snapshots (see §4). |
| `notes.md`, `README.md` | Notes. The `ghp_…` token in `notes.md` is **expired** — use the fine-grained `github_pat_…` token. |

**Cloud:**
- App URL: `https://ilm-geoinquire.streamlit.app` (password `geoinquire2026`)
- GitHub: `https://github.com/Juliano1111-ai/ILM.git` (branch `main`)
- Live Google Sheet gid: `2069740867`
- On Streamlit Cloud, creds live in **Secrets** as `gcp_service_account` (TOML), NOT the JSON file.

---

## 3. Data flow / architecture

```
Google Sheets (live)  ──► load_google_sheets_data() ─┐
                                                      ├─► va_df / ta_df  (renamed, cleaned)
ILM_Python_2.xlsx (fallback) ──► load_excel_data() ──┘     va_raw / ta_raw (original 4-row header kept)

ILM_Old/*.xlsx (frozen) ──► load_historical_va_data() ──► VA_DATA_BY_YEAR = {2023, 2024, 2025, 2026}
```

- **`VA_DATA_BY_YEAR`** maps each year tab to a DataFrame. `2023/2024/2025` are the
  frozen snapshots; **`2026` is `va_df`** (the live, interactive current data).
- **Tab order is 2026 · Live first**, then 2025, 2024, 2023 — so the dashboard opens
  on the live data (`YEAR_TAB_KEYS = ("2026","2025","2024","2023")`,
  `LIVE_YEAR_KEY = "2026"`). The PNG download button renders only on the live tab.
- Every VA chart renders **four year tabs** via `render_in_year_tabs(builder, …)`.
- Every TA chart renders **four Call tabs** via `render_in_call_tabs(builder, ta_dataframe=ta_df, …)`,
  filtered by the `call` column (extracted from `project_id` prefixes `TA1`–`TA4`).
- **Historical files are discovered by globbing** `ILM_Old/*.xlsx` and matching the
  4-digit year in the filename (anchored to the script directory via
  `os.path.dirname(os.path.abspath(__file__))`). Exact filenames no longer matter,
  but the files **must be committed to the repo** or the live app can't see them.
  A diagnostic is stashed in `st.session_state["_hist_diag"]`; the "no data" banner
  prints which files were found.

---

## 4. The historical year-tab snapshots (VA)

`HISTORICAL_VA_FILES` in the code maps year → file under `ILM_Old/`:

| Tab  | File in `ILM_Old/` | Sheet | Notes |
|------|--------------------|-------|-------|
| 2023 | `GeoINQUIRE-ImplementationLevelMatrix - 21 December 2023, 11_05.xlsx` | `ILM_VA` | uses `Research infrastructure (RI)` (no "Compliant with") |
| 2024 | `GeoINQUIRE-ImplementationLevelMatrix - 5 November 2024, 11_39.xlsx`  | `ILM-VA` | sheet name has a **hyphen** |
| 2025 | `GeoINQUIRE-ImplementationLevelMatrix - 12 November 2025, 10_47.xlsx` | `ILM_VA` | |
| 2026 | (live data — Google Sheets / Excel fallback) | — | shows when the dashboard opens |

To **swap which file represents a year**, edit `HISTORICAL_VA_FILES` only.
Sheet-name detection tries, in order: `ILM_VA`, `ILM-VA`,
`Implementation_Level_Matrix_VA`, `Implementation_Level_Matrix`. Add new ones to
`HISTORICAL_VA_SHEET_CANDIDATES`.

All VA workbooks read with `header=3` (the 4-row hierarchical header). Column names
are normalised by `_apply_va_column_renames()` — it maps both the 2023 vintage
(`TCS Name`, `Research infrastructure (RI)`) and the 2024/2025 vintage
(`Contact person`, `Compliant with Research infrastructure (RI)`) onto the same
internal names: `contact_person, email, affiliation, service_name, compliant_ri,
implementation_status, data_repr, license, metadata_standard, gender`.

---

## 5. Conventions you must preserve

1. **`st.set_page_config(...)` is the very first Streamlit call.** Anything before it
   crashes the app on startup.
2. **VA and TA are independent.** Editing a TA section must not touch VA code and
   vice-versa.
3. **New features are additive** — keep existing functionality unless explicitly
   replacing it.
4. **Charts are built by closures.** A VA chart is:
   ```python
   def _builder(_df, _yr):
       if 'somecol' not in _df.columns:
           return None
       fig = ...                      # build from _df, not va_df
       return fig
   render_in_year_tabs(_builder, figure_key="unique_key", source_cols=[...],
                       access_type="VA", download_label_base="...", figure_title="...")
   ```
   TA charts are identical but call `render_in_call_tabs(_builder, figure_key=...,
   ta_dataframe=ta_df, …)`.
5. **No misleading "0" slices.** Pie/donut factories call `_filter_zero_slices()`;
   stat dicts go through the cleaner in `compute_va_statistics()`. When you add a new
   categorical chart, filter `{"", "0", "0.0", "nan", "None", "-"}` out first (use the
   `value_counts_clean()` helper).
6. **Palette & type.** Use the `COLORS` dict (navy `#1f3a5f`, blue `#2563eb`,
   emerald `#0e9f6e`, …) and `FONT_FAMILY` (Inter stack). Don't hard-code hex.
7. **Legends** sit horizontally under the chart (`orientation="h"`, `y≈-0.22`,
   generous bottom margin ≈110–120) — the "License Distribution" chart is the
   reference look.
8. **Light theme only** — `.streamlit/config.toml` `base="light"` plus the CSS block
   that forces white backgrounds. Never ship dark/system.
9. **No decorative emojis** in section headers or tab labels. Small status icons
   (⚠️/ℹ️) in `st.info`/`st.warning` are fine.
10. **`st.header("### …")` is wrong** — `st.header` already renders a heading, so the
    `###` shows literally. Use `st.header("Title")` or `st.markdown("### Title")`.
11. **Source-column annotation appears exactly once per figure.** Only the tab
    renderers call `add_source_annotation`; `create_download_button` must NOT (it used
    to, which produced duplicate "Source column: …" lines).
12. **EU funding acknowledgement is mandatory and visible.** `render_eu_acknowledgement()`
    draws the inline 12-star EU flag (`EU_FLAG_SVG`) plus the exact sentence in
    `GEOINQUIRE_ACK_SENTENCE`. It runs as a page footer (module level, end of file,
    `variant="footer"`) and on the login page (`variant="login"`). Never remove it.

## 5a. Transnational Access statistics (expert framing)

The TA sheet is mostly free text, so charts use normalisation helpers — never raw
`value_counts` on these columns:

- `ta_normalize_access_level()` → Open access / Embargoed / Restricted / To be determined.
- `ta_normalize_integration()` → SDL / EPOS platform / ECCSEL / Geo-INQUIRE DMP.
- `ta_data_exposure_status(row)` → **the key outcome metric**: classifies each project as
  *Asset linked (DOI/URL)* / *In progress* / *Described, no link* / *Not reported* by
  scanning `outcome_metadata`, `delivered_outcomes`, `associated_va`, `expected_outcomes`
  for DOIs and URLs.
- `ta_count_asset_links(df)` → number of distinct DOIs/URLs actually recorded.
- `ta_reporting_completeness(df)` → % of projects with each lifecycle field filled
  (stage, visit dates, units, users, expected/delivered outcomes, outcome metadata,
  access level, integration) — a metadata-quality proxy.

The TA Dashboard ("Outcomes & Access") shows: KPIs (projects, host facilities, users
served, **% assets exposed**), then Project-stage funnel + Data-exposure donut, then
Access-level + Integration-strategy, then a full-width Reporting-completeness bar.
TA stats operate on **project rows only** (`project_id` not null), not the
installation-definition padding rows.

---

## 6. Page-by-page map of `ilm_dashboard_app.py`

- **Constants** (top): `HISTORICAL_VA_FILES`, `YEAR_TAB_KEYS/LABELS`,
  `CALL_TAB_KEYS/LABELS/PREFIXES`, `COLORS`, `FONT_FAMILY`.
- **Auth / login** (`check_password`) — password `geoinquire2026`.
- **Loaders** — `load_google_sheets_data`, `load_excel_data`,
  `load_historical_va_data`, `_apply_va_column_renames`.
- **Stats** — `compute_va_statistics` (with the zero-cleaner).
- **Helpers** — `render_in_year_tabs`, `render_in_call_tabs`, `value_counts_clean`,
  `build_four_row_header`, `add_source_annotation`, `create_download_button`.
- **Chart factories** — `create_professional_bar_chart`, `_filter_zero_slices`,
  `create_professional_donut_chart`, `create_professional_pie_chart`,
  `create_enhanced_heatmap`.
- **Pages** (`option_menu`): `Dashboard`, `Analytics`, `KPI` (placeholder),
  `Data` (Table view + Machine-readable placeholder), `Contact`.

---

## 7. How to make common changes

- **Add a year tab (e.g. 2027):** add the file to `HISTORICAL_VA_FILES`, extend
  `YEAR_TAB_KEYS` and `YEAR_TAB_LABELS`, add an entry to `VA_DATA_BY_YEAR`.
- **Add a VA chart:** copy an existing `_builder` block, change the column + figure,
  give it a unique `figure_key`, wrap with `render_in_year_tabs`.
- **Fill in a KPI:** the `KPI` page is a placeholder card today. Replace the markdown
  block under `elif selected == "KPI":` with real metric computations when the
  indicator set (TRL, test users, users served, datasets accessible, uptime…) is final.
- **Add machine-readable data:** the `Data → Machine-readable` tab is the reserved
  home for the tidy/long-format or JSON-LD export.
- **Change colours/fonts:** edit `COLORS` / `FONT_FAMILY` once; everything inherits.

---

## 8. Deploy (the only sequence that works)

```bash
cd .../ILM_Dashboard_correct2

# 0. config.toml MUST be in .streamlit/ — fix if it's in the repo root:
mkdir -p .streamlit && mv config.toml .streamlit/ 2>/dev/null

# 1. Local test (one-time kaleido fix kills the Plotly/Kaleido warning)
pip install "kaleido==0.2.1"
streamlit run ilm_dashboard_app.py

# 2. Protect creds, then stage
grep valiant-splicer .gitignore || echo "valiant-splicer-409609-e34abed30cc1.json" >> .gitignore
grep ".streamlit/secrets.toml" .gitignore || echo ".streamlit/secrets.toml" >> .gitignore
git add ilm_dashboard_app.py requirements.txt .streamlit/config.toml ILM_Old/
git status            # confirm the .json is NOT staged

# 3. Commit & push (use the github_pat_… token, NOT the expired ghp_…)
git commit -m "…describe the change…"
git push origin main

# 4. Streamlit Cloud — REBOOT after every deploy that changes loader return shapes
#    or @st.cache_data signatures (otherwise stale cache → ValueError on unpack).
#    share.streamlit.io → ilm-geoinquire → ⋮ Manage app → wait for green →
#    ⋮ → Reboot app.
```

**Production smoke test:** open incognito, log in, confirm `Data Source: Google
Sheets ✅`, VA charts show 2023/2024/2025/2026 tabs with *different* numbers per tab,
TA shows Call 1–4, no "0" pie slices, light theme, no red errors, PNG download works.

**Rollback:** `git revert <hash> && git push origin main`, then reboot.

---

## 9. Known gotchas (have bitten us before)

- Plotly 6.0 + Kaleido 1.x ⇒ broken PNG export + scary warning. **Pin `kaleido==0.2.1`.**
- `config.toml` placed in the repo root does nothing — must be `.streamlit/config.toml`.
- **Historical year tabs empty on the live app?** The `ILM_Old/*.xlsx` files almost
  certainly weren't committed/pushed. `git add ILM_Old/` and push, then reboot. Confirm
  with `git ls-files ILM_Old/`. The glob loader matches by year, so exact filenames
  don't matter — but the files must be *in the repo*.
- Forgetting to reboot Streamlit Cloud after a loader change ⇒ `ValueError: not enough
  values to unpack`. Reboot clears the cache.
- Sheet names drift between exports (`ILM_VA` vs `ILM-VA` vs `Implementation_Level_Matrix_VA`).
  Keep `HISTORICAL_VA_SHEET_CANDIDATES` in sync.
- The 2023 export uses older column names; rely on `_apply_va_column_renames`.

---

## 10. How to use this skill with Claude

1. **Put this file in the Project's knowledge** (Project → Knowledge → add files), or
   keep it pinned in the repo as `ILM_DASHBOARD_SKILL.md`.
2. Start any new chat in this Project with, e.g.:
   > "Per the ILM skill, add a 2027 year tab and a new VA chart for *Service Response
   > Formats*. Here's the latest `ilm_dashboard_app.py`." (attach the file)
3. Claude will read this skill via project search, follow the conventions in §5, make
   the change, run a syntax check, and hand you the deploy steps from §8.
4. Keep this file updated when conventions change — it is the project's memory.
