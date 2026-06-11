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
internal names. **As of the colour-consistency rework it also maps the analytics
columns that the Analytics page needs** — without these the old-year tabs showed
"No data for Service Running / Api Standards":

- the nine de-duplicated `[0;1]` binary columns →
  `service_running, parametrization, provides_data, license_exists,
  fully_described, qp_documentation, data_quality, payloads, converter_plugin`
  (exact-name map for `[0;1]`, `[0;1].1` … `[0;1].8`, **plus** a positional
  fallback as insurance);
- `(OGC, ERDDAP, etc)` → `api_standard`, `Service Response Formats` → `response_formats`;
- `implementation_status, documentation_status` and the nine binary columns are
  coerced to numeric by the nested `_clean_numeric` helper, which treats
  `[request]` / `TBD` / blank as `NaN` (so counts don't get polluted).

Full internal schema: `contact_person, email, affiliation, service_name,
compliant_ri, implementation_status, data_repr, response_formats, license,
metadata_standard, api_standard, service_running, parametrization, provides_data,
license_exists, fully_described, qp_documentation, data_quality, payloads,
converter_plugin, documentation_status, gender`.

> **If a chart is empty only on the old-year tabs**, the column it reads probably
> isn't being produced by `_apply_va_column_renames` for that vintage — add the
> mapping there, not in the chart.

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
6. **Colour is by *label*, never by position.** Every chart routes its colours
   through `resolve_colors(labels, color_map=None, palette=None)` so the *same
   category gets the same colour on every year/Call tab* (the thing that was
   broken: "Not implemented" was red in 2026 but blue in 2025 because colours were
   sliced from a palette by row order). The rule inside `resolve_colors`:
   1. a caller `color_map` (case-insensitive) wins;
   2. else, if **no** `palette` was passed, `CANONICAL_COLORS` is consulted
      (fixed status / yes-no / access colours — e.g. `not implemented → #dc2626`
      red, `implemented → #0e9f6e` green, `yes → green`, `no → red`);
   3. else a colour from a **persistent registry** keyed on the label (namespaced
      per palette): the first time a label is seen it's given the next free slot in
      `STABLE_PALETTE` (or the palette you passed) and that pairing never changes —
      so the same category keeps its colour across every year tab even when the set
      of categories present differs from one year to the next. (An earlier version
      ranked labels *within each call*, which reshuffled colours whenever a category
      appeared/disappeared between years — that was the consistency bug.)
   How to call it:
   - status / yes-no charts → pass the status dict as `color_map` (donut/pie) or
     as `color_palette` (the bar factory accepts a **dict**); canonical colours apply.
   - "keep it all blues/greens" charts (RI, metadata, data-representation) → pass
     the palette: `resolve_colors(cats, palette=COLORS['blue_palette'])`, or call the
     bar factory with `color_palette=COLORS['blue_palette']`.
   - one solid colour → pass a **string** (`color_palette='#8E44AD'`), *not*
     `['#8E44AD']*n`.
   **Never pre-build a per-row colour list and pass it as `color_palette`** — the bar
   factory now treats a *list* as a palette to rank against, so a pre-aligned list
   gets scrambled. Pass the `color_map` dict and let the factory resolve it.
   Add any new fixed colour to `CANONICAL_COLORS`; never hard-code hex at a chart.
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
    `variant="footer"`) **and on the login/password page** (`variant="login"`, a light
    card headed "How to acknowledge Geo-INQUIRE"). Never remove it.
    **Definition order matters:** `EU_FLAG_SVG`, `GEOINQUIRE_ACK_SENTENCE` and
    `render_eu_acknowledgement()` must be defined *immediately after
    `st.set_page_config(...)` and BEFORE `def check_password()`* — `check_password`
    calls it on the login page and the module-level gate `if not check_password():`
    runs at import, so a later definition raises
    `NameError: name 'render_eu_acknowledgement' is not defined`.

13. **The Implementation-Matrix heatmap uses the project's preferred layout, red-free.**
    `create_enhanced_heatmap()` is the RI×Data-Representation matrix where each cell
    shows the **total** services in a white rounded box (centre) and the
    **implemented** count with a `✓` in a green box (lower-left), plus a legend. The
    cell shade encodes the implemented count. The **only** colour rule: never use
    `RdYlGn` or any red ramp (red read as a warning) — it uses a light-blue → navy
    sequential `LinearSegmentedColormap` so the green `✓` corner stands out. Keep the
    "Implementation Matrix Analysis" title and the two-box annotation style; don't
    replace it with a single share-percentage cell (that version was rejected).

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
- **Colour resolver** — `CANONICAL_COLORS`, `STABLE_PALETTE`, `resolve_colors()`
  (see convention 6); every factory and inline figure calls it.
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
  To pin a *category* colour everywhere (e.g. a new status value), add it to
  `CANONICAL_COLORS` — don't touch individual charts.

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
- **A chart is empty only on 2023/2024/2025 tabs** (works on 2026·Live): the column
  it reads isn't being produced by `_apply_va_column_renames` for that older vintage.
  Add the mapping there. This is what caused the empty "Service Running / Api
  Standards" charts.
- **A category's colour differs between year/Call tabs**: something is colouring by
  row position instead of going through `resolve_colors` (convention 6). Most often a
  caller pre-built a per-row colour list and passed it as `color_palette` — pass the
  `color_map` dict instead.
- **`NameError: render_eu_acknowledgement` on the login page**: the EU block was moved
  below `check_password`. It must sit right after `st.set_page_config` and before
  `def check_password` (convention 12).
- **"No secrets found … secrets.toml"** red box: this is the *expected* message only
  when the deployed build pre-dates the `try/except` guard around `st.secrets` in
  `load_google_sheets_data`. The current code swallows it and falls back to the Excel
  loader on a laptop; just redeploy + reboot to clear a stale build.
- **Year tabs stay empty online even after `git add ILM_Old/`**: the `.xlsx` are being
  ignored by `.gitignore` (e.g. a `*.xlsx` rule), so `git add` silently skips them and
  `git ls-files ILM_Old/` returns nothing. Force them in:
  `git add -f "ILM_Old/"*.xlsx`, confirm with `git ls-files ILM_Old/` (must list 3),
  commit, push, reboot. Never force-add the `*.json` credentials.

## 11. Per-Work-Package breakdown

The VA Dashboard shows the whole-project **Overview** first, then **"Overview by
Work Package"** below it: `st.tabs` of `WPn` tokens, each repeating the key figures
filtered to that WP. WP cells look like `WP3 - VA2` / `WP5 - TA2 / VA4`; group by the
leading token via `wp_token()` (normalises `WP03`→`WP3`). `make_wp_filter(token)`
returns a `df→df` filter; `render_in_year_tabs(..., row_filter=...)` applies it per
year. The reusable builders (`build_impl_figure`, `build_ri_figure`,
`build_datarepr_figure`, `build_metadata_figure`, `build_license_figure`) go through
the factories, so per-WP colours match the global view. Plotly chart keys are
namespaced `f"{key}_{scope_tag}"` (e.g. `impl_wp_WP3`) — keep them unique when adding
new scoped figures.

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

---

## 12. v2.3 update — new data + TA Descriptive Overview (June 2026)

### Data source / files
- The app reads **`ILM_Python_2.xlsx`** (EXCEL_PATH). Its tabs are **`ILM_Connector_VA`**
  (182×47) and **`ILM_Connector_TA`** (229×27). `VA_SHEET_LEGACY="ILM_Connector_VA"`,
  `TA_SHEET_LEGACY="ILM_Connector_TA"`. The new master data ships as `ILM_Python_22.xlsx`;
  to refresh, copy its two sheets into `ILM_Python_2.xlsx` (a plain file copy works).
- Live Google Sheet (one doc, two tabs): VA tab `ILM_Connector` **gid=2069740867**,
  TA tab `ILM_Connector_TA` **gid=636297091**. The Sheets loader opens both by NAME.
  Config constants: `GOOGLE_SHEET_URL_VA`, `GOOGLE_SHEET_URL_TA`.

### TA sheet layout (ILM_Connector_TA)
- Headers are on **row 4**; **row 5** is sub-notes; **row 6** is an INSTRUCTION/example row
  ("Provide the given proposal ID…", project_id "New ID attribution…"). Loader reads
  `header=3, skiprows=[4]` then drops the instruction row by detecting
  `installation_id.startswith("Provide the given")` / `project_id contains "New ID attribution"`.
- Column letters → internal names: A installation_id, B project_id, C pi_gender, D project_title,
  E project_acronym, F ta_host, G pi_affiliation, H project_stage, I stage_updated,
  J stage_comments, K visit_start, L visit_end, M unit_of_access, N units_requested,
  O number_of_users, P units_used, Q activity_description, R expected_outcomes,
  S delivered_outcomes, T outcome_metadata, U access_level, V associated_wp, W associated_va,
  X associated_ri, Y integration_strategy, Z asset_link, AA provider_contact.

### Call extraction (IMPORTANT)
- Project IDs are `C1_TA1-44-1_1` → the **Call is the leading `C<n>_`** token. `extract_call`
  uses `re.search(r'(?:^|[-_\s])C(\d+)[-_]', pid)`. (The old `-C\d-` regex returned "Unknown"
  for every real row.) Real TA rows = those with a valid Call → `ta_real_projects(df)`.

### TA Descriptive Overview (Section II, top of the TA Dashboard page)
- **Figure 1** `fig_ta_calls_per_installation` — horizontal stacked bar, installations × Call.
- **Figure 2** `fig_ta_stage_by_call` (100% stacked, per Call) + `fig_ta_stage_by_installation`
  (counts, per installation). Stage (Col H) is bucketed into an ordered lifecycle via
  `TA_STAGE_BUCKETS` / `ta_stage_bucket`.
- **Figure 3** `fig_ta_completion_funnel` — cumulative gates: All → Completed (H) → +Metadata (T)
  → +Integration (Y, not "Not accessible") → +Data (S) → +Open access (U). Important = first
  three; `goal_reached = completed & metadata & integrated` (`ta_completion_flags`).
- **Figure 4** `fig_ta_world_map` (Plotly choropleth, `locationmode="country names"`) +
  `fig_ta_goal_by_call` (per-Call goal vs not-yet). Country comes from PI affiliation (Col G)
  via the dependency-free `resolve_ta_country` (`_TA_COUNTRY_TERMS` explicit names/codes first,
  then `_TA_INSTITUTION_TERMS` keywords). 71/71 affiliations resolve on current data.
- Completion classifiers: `ta_is_completed` (late stages set), `ta_meaningful`
  (drops blank/tbd/"not yet available"), `ta_is_integrated`, `ta_is_open_access` (handles
  "OpenAcces"/"Open-access" typos).

### Notes
- Plotly figures display in-browser without kaleido; PNG export keeps the existing HTML fallback.
- TA_COLUMN_SOURCES now uses the `Col <letter> · <header>` format for the ILM_Connector_TA sheet.
- Header docstring is **Version 2.3 / June 11 2026**; copyright + authors preserved.

### v2.3.1 — TA Overview polish (June 2026)
- TA figures are **title-less** (no "Figure N" inside the plot); the descriptive name is a
  Streamlit `#### header` above each chart, and the legend sits at the top — this removed the
  legend/title overlap. `_ta_layout(fig, height=...)` no longer takes a title.
- Each TA overview figure now has a **300-DPI PNG download** (`create_download_button`) and a
  **source-column caption** (`add_source_annotation(..., access_type="TA")`), exactly like VA.
- **Removed** the empty "Outcomes & Access" and "Reporting & Metadata Completeness" sections and
  the per-Call monitoring bar (old Figure 4b `fig_ta_goal_by_call`). The world map is now full width.
- Installation IDs are normalised by stripping a stray leading `C\d+_` (some Call-4 rows stored
  the project-style ID in Col A) so installations group consistently.
- `requirements.txt` pins **`kaleido==0.2.1`** so PNG export works on Streamlit Cloud without a
  separate Chrome install (kaleido v1 requires Chrome).
- Sidebar "SELECT PROJECT" radio restyled with robust `div[role="radiogroup"]` selectors → bold
  pills, selected option in a navy→blue gradient with white text.
