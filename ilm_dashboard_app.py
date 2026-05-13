# =====================================================================================
# ILM Geo-INQUIRE Dashboard — Professional Implementation Level Matrix
# =====================================================================================
#
# Copyright (c) 2024–2026 Geo-INQUIRE Project
# University of Bergen, Norway
#
# Developed by: Juliano Ramanantsoa (assisted by Claude)
# Project    : Geo-INQUIRE — Implementation Level Matrix (ILM) Dashboard
# Purpose    : Interactive visualization and analytics for Virtual Access (VA)
#              and Transnational Access (TA) project data
#
# What this dashboard provides
# ----------------------------
#   * Real-time data integration with Google Sheets (primary source)
#   * Excel-file fallback (GeoINQUIRE-ImplementationLevelMatrix.xlsx)
#   * Comprehensive analytics and KPI tracking
#   * Professional visualizations (300 DPI export via kaleido)
#   * Multi-dimensional analysis (gender, hosts, temporal trends)
#   * Secure password-protected access (session-based)
#   * Per-figure year tabs (2023 / 2024 / 2025 / 2026) on the VA Dashboard
#     and Analytics pages — placeholders where year-specific figures can be
#     appended later by the user.
#   * Data tab with a 4-row MultiIndex header that mirrors the first four
#     rows of the source Excel sheet (group bands, topics, criteria, names).
#
# License: Internal use — Geo-INQUIRE Project
# Contact: Geo-INQUIRE Project Administration, University of Bergen
#
# Version     : 2.1
# Last Updated: May 12, 2026
# Contact     : heriniaina.j.ramanantsoa@uib.no
#
# =====================================================================================
# INSTALLATION REQUIREMENTS
# =====================================================================================
#   - streamlit              : pip install streamlit
#   - plotly                 : pip install plotly
#   - pandas                 : pip install pandas
#   - numpy                  : pip install numpy
#   - matplotlib             : pip install matplotlib
#   - seaborn                : pip install seaborn
#   - streamlit-option-menu  : pip install streamlit-option-menu
#   - kaleido                : pip install -U kaleido     (PNG export at 300 DPI)
#   - gspread                : pip install gspread        (Google Sheets API)
#   - oauth2client           : pip install oauth2client   (Google Sheets auth)
#   - openpyxl               : pip install openpyxl       (Excel file reading)
# =====================================================================================

# --- Standard library imports ---------------------------------------------------
import os                                          # Filesystem checks (logo, credentials)
import io                                          # In-memory bytes buffers for downloads
import re                                          # Regex helpers (Call number extraction)
from datetime import datetime                      # Used for date stamps and conversions

# --- Third-party scientific stack ----------------------------------------------
import numpy as np                                 # Numeric arrays for matrices/heatmap
import pandas as pd                                # Tabular data manipulation

# --- Streamlit framework + UI helpers ------------------------------------------
import streamlit as st                             # Web UI framework
from streamlit_option_menu import option_menu      # Pretty horizontal top-navigation menu

# --- Plotting libraries --------------------------------------------------------
import plotly.graph_objects as go                  # Low-level Plotly (bars, pies, scatter)
import plotly.express as px                        # High-level Plotly (grouped bars)
from plotly.subplots import make_subplots          # (Reserved for multi-panel figures)
import matplotlib.pyplot as plt                    # Used only for the heatmap figure
import matplotlib.patches as mpatches              # Legend patches (heatmap)
import seaborn as sns                              # Heatmap styling

# --- Google Sheets API ---------------------------------------------------------
import gspread                                                          # Sheets client
from oauth2client.service_account import ServiceAccountCredentials      # Service-account auth

# ===============================================================================================
# GLOBAL CONSTANTS — paths, sheet names, URLs, and the year-tab range
# ===============================================================================================
# Every constant below is annotated line-by-line so you (Juliano) can
# adjust any of them without having to read the rest of the file.
# Change a value here and the rest of the dashboard picks it up
# automatically; nothing downstream hard-codes these names.
# ===============================================================================================

# --- Excel fallback workbook ----------------------------------------------------
# Primary path searched on disk when Google Sheets is unavailable. This MUST
# match the filename you keep in the same folder as ilm_dashboard_app.py.
# If you ever rename the workbook (e.g. to a new year's export), change only
# this one line. The .xlsx must live in the repository root next to the
# Python script.
EXCEL_PATH          = "ILM_Python_2.xlsx"

# Optional secondary path — tried if EXCEL_PATH is missing. Leave it equal
# to EXCEL_PATH (or to "") if you only ever keep one Excel file around.
# Useful when you have a backup snapshot under a second name during a
# migration; the loader silently tries this one second.
EXCEL_PATH_LEGACY   = "ILM_Python_2.xlsx"

# --- Google Sheets — the live data source --------------------------------------
# Full URL of the working spreadsheet, including the gid of the worksheet
# you want the dashboard to open by default. If you ever migrate to a new
# Google Sheet, paste its full URL here (keep the gid query parameter so
# the right tab is selected). The string is split across three lines purely
# for readability — Python concatenates adjacent string literals.
GOOGLE_SHEET_URL    = ("https://docs.google.com/spreadsheets/d/"
                      "1noNhzwKOp1_t9RfgJc__zvXs-23t_BofigcZBjTnADM/"
                      "edit?gid=2069740867#gid=2069740867")

# Filename of the Google service-account JSON used for authentication.
# Must sit in the same folder as this script for local runs. On Streamlit
# Cloud this file is NOT used — the secret is read from `st.secrets`
# instead. Keep this name in .gitignore so the key is never pushed.
GOOGLE_CREDS_FILE   = "valiant-splicer-409609-e34abed30cc1.json"

# --- Sheet / worksheet names ---------------------------------------------------
# Both loaders (Excel and Google Sheets) look for a "preferred" name first
# and then fall back to a "legacy" name. That way the same code works no
# matter which export you have in front of you.

# VA sheet name in the *new* reference workbook (e.g. the
# Implementation-Level-Matrix export you would download from the official
# Geo-INQUIRE Google Drive). The Excel loader tries this name first.
VA_SHEET_NAME       = "Implementation_Level_Matrix_VA"

# TA sheet name in the *new* reference workbook. Same logic as VA.
TA_SHEET_NAME       = "TA_Individual_Applications"

# Legacy VA sheet name used by:
#   * ILM_Python_2.xlsx  → tab is called "ILM_Connector_VA"
#   * The live Google Sheet → tab is called "ILM_Connector" (no _VA suffix)
# We keep the Excel form here because it is also what `load_excel_data`
# reads; the Google Sheets loader hard-codes "ILM_Connector" separately
# (see `load_google_sheets_data`).
VA_SHEET_LEGACY     = "ILM_Connector_VA"

# Legacy TA sheet name. Used by BOTH the Excel file and the Google Sheet —
# the tab is named "ILM_Connector_TA" in both places.
TA_SHEET_LEGACY     = "ILM_Connector_TA"

# --- Year tabs around each figure ----------------------------------------------
# These are the year tabs that appear under every chart on the VA Dashboard
# and the Analytics page. Each tab currently shows the all-years figure as
# a placeholder; replace the placeholder with a year-specific chart inside
# `render_in_year_tabs` (search the file for ">>> APPEND YEAR-").
# Add a year (e.g. 2027) by extending the tuple — the rest of the dashboard
# picks it up automatically.
YEAR_TABS           = (2023, 2024, 2025, 2026)

# ===============================================================================================
# STREAMLIT PAGE CONFIGURATION — MUST BE FIRST STREAMLIT COMMAND
# ===============================================================================================
st.set_page_config(page_title="ILM Geo-INQUIRE Dashboard", layout="wide", initial_sidebar_state="expanded")

# ===============================================================================================
# PASSWORD PROTECTION SYSTEM
# ===============================================================================================
# Implements secure password-based authentication for dashboard access
# Password: geoinquire2026
# Session-based authentication (clears on browser close)
# ===============================================================================================
def check_password():
    """Returns True if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "geoinquire2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem;
            max-width: 600px;
            margin: 0 auto;
        }
        .welcome-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2C3E50;
            margin-bottom: 1rem;
            text-align: center;
        }
        .welcome-subtitle {
            font-size: 1.2rem;
            color: #34495E;
            margin-bottom: 2rem;
            text-align: center;
        }
        .description-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            margin: 2rem 0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .description-box h3 {
            color: white;
            margin-bottom: 1rem;
        }
        .feature-list {
            list-style: none;
            padding-left: 0;
        }
        .feature-list li {
            padding: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }
        .feature-list li:before {
            content: "\2713";
            position: absolute;
            left: 0;
            font-weight: bold;
            color: #27AE60;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        # Display Geo-INQUIRE logo centered on login page
        _logo_col1, _logo_col2, _logo_col3 = st.columns([1, 2, 1])
        with _logo_col2:
            if os.path.exists("Logo.jpg"):
                st.image("Logo.jpg", use_container_width=True)
            else:
                st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h1 style="font-size: 4rem; margin: 0;">🌍</h1></div>', unsafe_allow_html=True)
        st.markdown('<h1 class="welcome-title">ILM Geo-INQUIRE Dashboard</h1>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-subtitle">Implementation Level Matrix - Virtual Access and Transnational Access</p>', unsafe_allow_html=True)
        
        # st.markdown("""
        # <div class="description-box">
        #     <h3>Dashboard Overview</h3>
        #     <p>
        #         This interactive dashboard provides comprehensive analytics and visualization tools for the 
        #         <strong>Geo-INQUIRE</strong> project. Monitor implementation progress, analyze trends, and 
        #         explore detailed metrics across Virtual Access (VA) and Transnational Access (TA) initiatives.
        #     </p>
        #     <br>
        #     <h3>Key Features</h3>
        #     <ul class="feature-list">
        #         <li><strong>Real-time Data Integration:</strong> Dynamic connection to Google Sheets with automatic updates</li>
        #         <li><strong>Implementation Matrix:</strong> Visual heatmaps tracking project completion status</li>
        #         <li><strong>Multi-dimensional Analytics:</strong> Gender distribution, host analysis, and temporal trends</li>
        #         <li><strong>KPI Monitoring:</strong> Track key performance indicators</li>
        #         <li><strong>Professional Exports:</strong> High-resolution charts (300 DPI) ready for presentations</li>
        #     </ul>
        # </div>
        # """, unsafe_allow_html=True)
        
        st.text_input(
            "🔐 Please enter the password to access the dashboard",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter password"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Password incorrect. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; color: #95A5A6; margin-top: 3rem; padding: 2rem;">
            <p style="font-size: 0.9rem;">
                For access credentials or technical support, please contact the project administrator.
            </p>
            <p style="font-size: 0.8rem; margin-top: 1rem;">
                © 2025 Geo-INQUIRE Project | University of Bergen
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# Check password before showing main content
if not check_password():
    st.stop()




# ===============================================================================================
# PROFESSIONAL COLOR PALETTE
# ===============================================================================================
# Defines consistent color scheme throughout the dashboard
# Includes status colors, chart palettes, and theme colors
# ===============================================================================================
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E',
    'accent': '#3498DB',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'info': '#16A085',
    'light': '#ECF0F1',
    'dark': '#2C3E50',
    
    # Extended palette for charts
    'blue_palette': ['#3498DB', '#5DADE2', '#85C1E9', '#AED6F1', '#D6EAF8'],
    'green_palette': ['#27AE60', '#52BE80', '#7DCEA0', '#A9DFBF', '#D5F4E6'],
    'multi_palette': ['#3498DB', '#E74C3C', '#F39C12', '#9B59B6', '#1ABC9C', '#34495E'],
    
    # Status colors
    'implemented': '#27AE60',
    'partly_implemented': '#3498DB',
    'planned': '#F39C12',
    'not_implemented': '#E74C3C',
    'yes': '#27AE60',
    'no': '#E74C3C',
    'unknown': '#95A5A6',
    
    # TA Status colors
    'exhausted': '#27AE60',
    'fixed': '#3498DB',
    'ready': '#1ABC9C',
    'contacted': '#F39C12',
    'negotiated': '#9B59B6',
}

# Professional font settings
FONT_FAMILY = "Arial, sans-serif"
TITLE_FONT_SIZE = 18
LABEL_FONT_SIZE = 14
TICK_FONT_SIZE = 12

# ===============================================================================================
# CUSTOM CSS STYLING
# ===============================================================================================
# Defines custom styles for KPI cards, metrics, and layout
# ===============================================================================================
st.markdown("""
<style>
.block-container { padding-top: 4.25rem !important; padding-bottom: 1rem; }
h1, h2, h3 { margin-bottom: .25rem; font-family: Arial, sans-serif; }
hr { margin: .75rem 0; }
.kpi { 
    padding: 1.2rem 1.5rem; 
    border-radius: 12px; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    color: white;
}
.kpi h3 { 
    font-size: 0.95rem; 
    margin: 0 0 .5rem 0; 
    color: rgba(255,255,255,0.9); 
    font-weight: 600; 
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kpi .val { 
    font-size: 2rem; 
    font-weight: 700; 
    color: white;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.small { font-size: 0.85rem; color: #666; }
[data-testid="stDataFrame"] { border: 1px solid #eee; border-radius: 10px; }
.download-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
}
.chart-container {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
}
@media (min-width: 1200px) { .block-container { padding-top: 3.25rem !important; } }
@media (max-width: 768px) { .block-container { padding-top: 4.75rem !important; } }
</style>
""", unsafe_allow_html=True)

# ------------------------------- Branding -------------------------------
logo_path = "Logo.jpg"
left, right = st.columns([3, 1])
with left:
    st.markdown("<h1 style='line-height:.75;'>Geo-INQUIRE<br><span style='font-size:20px;'>Implementation Level Matrix</span></h1>", unsafe_allow_html=True)
with right:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

# ===============================================================================================
# SIDEBAR CONFIGURATION
# ===============================================================================================
# Allows users to switch between Virtual Access and Transnational Access projects
# ===============================================================================================
with st.sidebar:
    # Bold project toggle header
    st.markdown(
        '<p style="font-size:1.25rem; font-weight:900; color:#1a1a2e; '
        'letter-spacing:1px; margin-bottom:0.5rem; text-transform:uppercase; '
        'border-bottom:3px solid #3498DB; padding-bottom:0.3rem;">Select Project</p>',
        unsafe_allow_html=True,
    )

    # Inject custom CSS to make the radio buttons large, bold & highly visible
    st.markdown("""
    <style>
    /* ===== BOLD PROJECT TOGGLE BUTTONS ===== */
    div[data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem !important;
    }
    div[data-testid="stSidebar"] .stRadio > div > label {
        font-weight: 900 !important;
        font-size: 1.15rem !important;
        padding: 0.75rem 1.2rem !important;
        border: 3px solid #2980B9 !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.25s ease !important;
        background: #F0F8FF !important;
        display: flex !important;
        align-items: center !important;
        color: #1a1a2e !important;
        letter-spacing: 0.3px !important;
    }
    div[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: #D6EAF8 !important;
        border-color: #1a6fb5 !important;
        transform: translateX(3px);
    }
    div[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    div[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background: linear-gradient(135deg, #2980B9 0%, #1a5276 100%) !important;
        color: white !important;
        border-color: #1a5276 !important;
        box-shadow: 0 4px 12px rgba(41,128,185,0.45) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    project_label = st.radio(
        "Select Project",
        ["Virtual Access", "Transnational Access"],
        horizontal=False,
        label_visibility="collapsed",
    )

    st.markdown(
        f'<p style="font-size:0.85rem; color:#555; margin-top:0.4rem; font-weight:600;">'
        f'Active: <strong style="color:#2980B9;">{project_label}</strong></p>',
        unsafe_allow_html=True,
    )

    # ---- Geo-INQUIRE Project Metadata ----
    st.markdown("---")
    st.markdown(
        '<p style="font-size:1.05rem; font-weight:800; color:#1a1a2e; '
        'letter-spacing:0.5px; margin-bottom:0.3rem;">About Geo-INQUIRE</p>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f8f9fa 0%,#e8f4fd 100%);
                padding:1rem; border-radius:10px; border-left:4px solid #2980B9;
                font-size:0.82rem; color:#333; line-height:1.5; margin-bottom:0.8rem;">
        <strong>Geosphere INfrastructures for QUestions into Integrated REsearch</strong><br><br>
        Geo-INQUIRE is a <strong>Horizon Europe</strong> project enhancing access to
        key geoscience data, products and services to monitor and model
        geosphere dynamics at new levels of detail and precision.<br><br>
        <strong>Key Facts:</strong><br>
        &bull; <strong>Grant No:</strong> 101058518<br>
        &bull; <strong>Call:</strong> HORIZON-INFRA-2021-SERV-01<br>
        &bull; <strong>Partners:</strong> 51 organisations<br>
        &bull; <strong>Facilities:</strong> 150+ VA & TA services<br>
        &bull; <strong>RIs:</strong> EPOS, EMSO, ECCSEL
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.75rem; color:#888; line-height:1.4;">
        <a href="https://www.geo-inquire.eu/" target="_blank"
           style="color:#2980B9; text-decoration:none; font-weight:600;">
           www.geo-inquire.eu</a><br>
        University of Bergen, Norway<br>
        © 2024–2026 Geo-INQUIRE Project
    </div>
    """, unsafe_allow_html=True)

# ===============================================================================================
# TOP NAVIGATION MENU
# ===============================================================================================
# Main navigation: Dashboard | Analytics | KPI | Data | Contact
# Dynamically adjusts based on selected project type
# ===============================================================================================
# Same menu for both projects (removed separate TA Dashboard tab)
menu_options = ["Dashboard", "Analytics", "KPI", "Data", "Contact"]
menu_icons = ["house", "bar-chart-fill", "bullseye", "database", "envelope"]

selected = option_menu(
    menu_title=None,
    options=menu_options,
    icons=menu_icons,
    default_index=0,
    orientation="horizontal",
)

# ===============================================================================================
# DATA LOADING FUNCTIONS
# ===============================================================================================
# Two data sources with automatic fallback:
# 1. PRIMARY: Google Sheets (auto-refresh every 5 minutes)
# 2. FALLBACK: Local Excel file (ILM_Python_2.xlsx)
# 
# Sheet structure:
# - Row 4: Column headers
# - Row 5+: Data
# ===============================================================================================
@st.cache_data(ttl=300)
def load_excel_data():
    """
    Load VA + TA data from the local Excel workbook (fallback source).

    The reference workbook is the one the user attached in May 2026:
        GeoINQUIRE-ImplementationLevelMatrix.xlsx
    It contains the following sheets we care about:
        * Implementation_Level_Matrix_VA  — Virtual Access ILM
        * TA_Individual_Applications      — Transnational Access applications

    Both sheets share the same 4-row header structure:
        Row 1: group bands (e.g. "Implementation Level 1", "KPI-Virtual Access")
        Row 2: per-column topics / questions
        Row 3: criteria explanations
        Row 4: actual column names               ← used as the DataFrame header
        Row 5+: data rows                        ← actual records

    Returns
    -------
    df_va         : pandas.DataFrame   (renamed columns for internal use)
    df_ta         : pandas.DataFrame   (renamed columns for internal use)
    va_header4    : list[list[str]]    Rows 1–4 of the VA sheet (for Data tab display)
    ta_header4    : list[list[str]]    Rows 1–4 of the TA sheet (for Data tab display)
    va_raw        : pandas.DataFrame   VA data with ORIGINAL Excel column names (for Data tab)
    ta_raw        : pandas.DataFrame   TA data with ORIGINAL Excel column names (for Data tab)
    """
    try:
        # ─── 1) Locate the Excel file ────────────────────────────────────────
        # Try the new reference workbook first; fall back to the legacy name
        # so existing deployments keep working without renaming files.
        excel_path = EXCEL_PATH if os.path.exists(EXCEL_PATH) else EXCEL_PATH_LEGACY
        if not os.path.exists(excel_path):
            st.error(f"Excel file not found. Looked for: {EXCEL_PATH} and {EXCEL_PATH_LEGACY}")
            return None, None, None, None, None, None

        # ─── 2) Decide which sheet names to use depending on the workbook ────
        # The new workbook uses descriptive sheet names; the legacy one used
        # the Google Sheets export tab names.
        xl = pd.ExcelFile(excel_path)
        va_sheet = VA_SHEET_NAME if VA_SHEET_NAME in xl.sheet_names else VA_SHEET_LEGACY
        ta_sheet = TA_SHEET_NAME if TA_SHEET_NAME in xl.sheet_names else TA_SHEET_LEGACY

        # ─── 3) Read VA sheet WITHOUT a header so we can grab rows 1–4 ──────
        # We need the raw rows to build the 4-row MultiIndex for the Data tab.
        raw_va_full = pd.read_excel(excel_path, sheet_name=va_sheet, header=None)
        # Coerce every cell of the first four rows to string for header display
        va_header4 = [
            ["" if pd.isna(v) else str(v) for v in raw_va_full.iloc[i].tolist()]
            for i in range(4)
        ]

        # Build a "raw" VA DataFrame whose columns are the EXACT Excel names
        # from row 4. This is what the Data tab will display (with multi-header).
        va_raw = raw_va_full.iloc[4:].copy()                          # data starts at row 5
        va_raw.columns = raw_va_full.iloc[3]                          # row 4 → column names
        va_raw = va_raw.reset_index(drop=True)

        # ─── 4) Load VA sheet WITH header=3 for the cleaned internal frame ──
        # The data starts at index 4 (row 5). No skiprows is needed for the
        # new workbook — the previous skiprows=[4] would have dropped the
        # first real data row.
        df_va = pd.read_excel(excel_path, sheet_name=va_sheet, header=3)
        
        # Clean up column names for VA
        va_col_mapping = {
            'Contact person': 'contact',
            'Email': 'email',
            'Affiliation': 'affiliation',
            'Service/Installation Name': 'service_name',
            'Compliant with Research infrastructure (RI)': 'compliant_ri',
            'Implementation status to RI \n\n[0; not implemented,\n0.2; planned,\n0.5; partly implemented,\n1; implemented]': 'implementation_status',
            'Installation ID': 'installation_id',
            'Service ID': 'service_id',
            'WP': 'wp',
            'Data Representations [georeferenced/non-georeferenced/time-series/software]': 'data_repr',
            'Service Response Formats': 'response_formats',
            'License': 'license',
            'Standard of metadata describing the service at RI integration level (not data)': 'metadata_standard',
            'Installation URL': 'installation_url',
            'Scientific domain/category': 'domain',
            '[%]': 'completeness_pct',
            '[0;1]': 'service_running',
            'URL of the service endpoint': 'endpoint_url',
            '(OGC, ERDDAP, etc)': 'api_standard',
            '[0;1].1': 'parametrization',
            '[0;1].2': 'provides_data',
            'percentage': 'availability',
            '[0;1].3': 'license_exists',
            '[0;1].4': 'fully_described',
            '[0, not implemented; 0.2 planned; \n0.5, partly implemented; 1, implemented]': 'documentation_status',
            'URL': 'documentation_url',
            '[0;1].5': 'qp_documentation',
            '[0;1].6': 'data_quality',
            '[0;1].7': 'payloads',
            '[e.g. OAuth, SAML, API access token, none]': 'auth_method',
            '[open; restricted; embargoed]': 'data_policy',
            '[0;1].8': 'converter_plugin',
            '[1-9]': 'trl',
        }
        
        existing_renames = {k: v for k, v in va_col_mapping.items() if k in df_va.columns}
        df_va = df_va.rename(columns=existing_renames)
        
        # Fix duplicate column names by making them unique
        cols = pd.Series(df_va.columns)
        for dup in cols[cols.duplicated()].unique():
            dup_indices = [i for i, x in enumerate(cols) if x == dup]
            for i, idx in enumerate(dup_indices[1:], start=1):
                cols[idx] = f"{dup}_{i}"
        df_va.columns = cols
        

        
        # -------------------------------------------------------------------------
        # DATA CLEANING: Convert implementation status values to float
        # Handles: numbers, text values, NaN, special cases like [request], TBD
        # -------------------------------------------------------------------------
        def clean_implementation_value(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, str):
                if val.lower() in ['[request]', 'request', 'tbd', 'to be determined']:
                    return np.nan
                try:
                    return float(val)
                except:
                    return np.nan
            return float(val) if isinstance(val, (int, float)) else np.nan
        
        if 'implementation_status' in df_va.columns:
            df_va['implementation_status'] = df_va['implementation_status'].apply(clean_implementation_value)
        
        if 'documentation_status' in df_va.columns:
            df_va['documentation_status'] = df_va['documentation_status'].apply(clean_implementation_value)
        
        binary_cols = ['service_running', 'parametrization', 'provides_data', 'license_exists', 
                      'fully_described', 'qp_documentation', 'data_quality', 'payloads', 'converter_plugin']
        for col in binary_cols:
            if col in df_va.columns:
                df_va[col] = df_va[col].apply(clean_implementation_value)
        
        # ─── 5) Read TA sheet — repeat the same approach ─────────────────────
        # TA structure differs slightly: row 1 is a description, row 2 is the
        # table title, row 3 is the group bands, row 4 holds the real column
        # names, row 5 is sub-descriptions, and data starts at row 6.  We
        # still keep the "first four lines" for the multi-header display
        # because that is what the user asked for.
        raw_ta_full = pd.read_excel(excel_path, sheet_name=ta_sheet, header=None)
        ta_header4 = [
            ["" if pd.isna(v) else str(v) for v in raw_ta_full.iloc[i].tolist()]
            for i in range(4)
        ]

        # Raw TA frame with original Excel column names (row 4) — used by the
        # Data tab. Note: for TA the actual data rows start at index 5 (row 6)
        # because row 5 contains the sub-descriptions ("Provide the given …").
        ta_raw = raw_ta_full.iloc[5:].copy()
        ta_raw.columns = raw_ta_full.iloc[3]
        ta_raw = ta_raw.reset_index(drop=True)

        # Cleaned, internal TA frame with column renaming for analytics.
        df_ta = pd.read_excel(excel_path, sheet_name=ta_sheet, header=3, skiprows=[4])
        
        ta_col_mapping = {
            'Installation ID': 'installation_id',
            'Project ID': 'project_id',
            'PI Gender ': 'pi_gender',
            'Project title': 'project_title',
            'Project acronym': 'project_acronym',
            'TA host': 'ta_host',
            'PI Affiliation': 'pi_affiliation',
            'Project Stage\n(completed milestone)': 'project_stage',
            'Stage updated on': 'stage_updated',
            'Comments to the stage\n(optional)': 'stage_comments',
            'Start of the Visit/Access': 'visit_start',
            'End of the Visit/Access': 'visit_end',
            'Unit of access': 'unit_of_access',
            'Number of units requested': 'units_requested',
            'Number of Users': 'number_of_users',
            'Number of units used': 'units_used',
            'Short description of the activity': 'activity_description',
            'Expected assets as outcomes': 'expected_outcomes',
            'Delivered assets as outcomes': 'delivered_outcomes',
            'Metadata of the outcome': 'outcome_metadata',
            'Level of access': 'access_level',
            'Associated WP': 'associated_wp',
            'Associated VA': 'associated_va',
            'Associated RI': 'associated_ri',
            'Expected strategy of integration': 'integration_strategy',
            'Service provider contact ': 'provider_contact',
        }
        
        existing_ta_renames = {k: v for k, v in ta_col_mapping.items() if k in df_ta.columns}
        df_ta = df_ta.rename(columns=existing_ta_renames)
        
        # Extract Call information
        if 'project_id' in df_ta.columns:
            df_ta['call'] = df_ta['project_id'].apply(lambda x: extract_call(x) if pd.notna(x) else None)
            df_ta['application_number'] = df_ta['project_id'].apply(lambda x: extract_app_number(x) if pd.notna(x) else None)
        
        # Return six items: cleaned VA, cleaned TA, raw 4-row VA header,
        # raw 4-row TA header, original-name VA frame, original-name TA frame.
        return df_va, df_ta, va_header4, ta_header4, va_raw, ta_raw
        
    except Exception as e:
        st.error(f"Error loading Excel data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None, None, None, None


# -------------------------------------------------------------------------
# HELPER FUNCTION: Extract Call Number from Project ID
# Format: PROJECT-C#-A# where C# is the call number
# -------------------------------------------------------------------------
def extract_call(project_id):
    """Extract call number from project ID"""
    try:
        match = re.search(r'-C(\d+)-', str(project_id))
        if match:
            return f"Call {match.group(1)}"
        return "Unknown"
    except:
        return "Unknown"

def extract_app_number(project_id):
    """Extract application number from project ID"""
    try:
        parts = str(project_id).split('-')
        if len(parts) >= 5:
            return parts[-1]
        return None
    except:
        return None

# Load data from Google Sheets (PRIMARY SOURCE)
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_google_sheets_data():
    """Load data from Google Sheets - PRIMARY DATA SOURCE"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # ─── Authentication ───────────────────────────────────────────────────
        # Two ways to authenticate, tried in this order:
        #   1. Streamlit Cloud secrets (`st.secrets["gcp_service_account"]`)
        #   2. Local service-account JSON file next to this script
        #
        # On a developer laptop with no `.streamlit/secrets.toml`, simply
        # touching `st.secrets` raises StreamlitSecretNotFoundError. We catch
        # that quietly and treat it as "no secrets defined" — NOT as a fatal
        # error — so the local JSON path can take over without any red error
        # box on screen.
        try:
            secrets_has_gcp = ("gcp_service_account" in st.secrets)
        except Exception:
            # No secrets.toml at all → treat as "no Cloud secrets defined"
            secrets_has_gcp = False

        try:
            if secrets_has_gcp:
                # Streamlit Cloud path: build credentials from the secrets block.
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                client = gspread.authorize(creds)
            else:
                # Local-development path: use the JSON keyfile on disk.
                json_keyfile_path = GOOGLE_CREDS_FILE
                if not os.path.exists(json_keyfile_path):
                    # Neither secrets nor JSON → fail quietly; the caller will
                    # fall back to the Excel workbook. No st.error here so the
                    # UI stays clean.
                    return None, None, None, None, None, None, "Credentials file missing"
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
                client = gspread.authorize(creds)
        except Exception as e:
            # Auth itself failed (bad key, network issue, etc.). Return the
            # message so the caller can decide whether to show it.
            return None, None, None, None, None, None, f"Auth error: {str(e)}"
        
        # Use the correct spreadsheet URL
        sheet_url = "https://docs.google.com/spreadsheets/d/1noNhzwKOp1_t9RfgJc__zvXs-23t_BofigcZBjTnADM/edit?gid=2069740867#gid=2069740867"
        
        spreadsheet = client.open_by_url(sheet_url)
        
        # Load Virtual Access data
        try:
            worksheet_va = spreadsheet.worksheet("ILM_Connector")
            data_va = worksheet_va.get_all_values()
            if len(data_va) < 4:
                st.warning("⚠️ Virtual Access worksheet has insufficient data")
                df_va = pd.DataFrame()
                va_header4 = None
                va_raw = pd.DataFrame()
            else:
                # ─── Capture the four-line header BEFORE we reduce to columns ──
                # data_va[0..3] are rows 1..4 of the sheet — exactly what the
                # user wants displayed as a 4-row MultiIndex in the Data tab.
                va_header4 = [list(data_va[i]) for i in range(4)]

                # Build TWO frames from the Google Sheets payload:
                #   * df_va  — column names from row 4, will be renamed for analytics
                #   * va_raw — same column names, kept verbatim for the Data tab
                df_va  = pd.DataFrame(data_va[4:], columns=data_va[3])
                va_raw = df_va.copy()
                
                # CRITICAL: Map exact column names from Google Sheets (with newlines and brackets!)
                va_col_mapping = {
                    'Contact person': 'contact',
                    'Email': 'email',
                    'Affiliation': 'affiliation',
                    'Service/Installation Name': 'service_name',
                    'Compliant with Research infrastructure (RI)': 'compliant_ri',
                    # This column has newlines in it!
                    'Implementation status to RI \n\n[0; not implemented,\n0.2; planned,\n0.5; partly implemented,\n1; implemented]': 'implementation_status',
                    'Installation ID': 'installation_id',
                    'Service ID': 'service_id',
                    'WP': 'wp',
                    # This column has brackets!
                    'Data Representations [georeferenced/non-georeferenced/time-series/software]': 'data_repr',
                    'Service Response Formats': 'response_formats',
                    'License': 'license',
                    # Note: "Standard" not "Standards"
                    'Standard of metadata describing the service at RI integration level (not data)': 'metadata_standard',
                    'Installation URL': 'installation_url',
                    'Scientific domain/category': 'domain',
                    '[%]': 'completeness_pct',
                    'URL of the service endpoint': 'endpoint_url',
                    '(OGC, ERDDAP, etc)': 'api_standard',
                    'percentage': 'availability',
                    '[e.g. OAuth, SAML, API access token, none]': 'auth_method',
                    '[open; restricted; embargoed]': 'data_policy',
                    '[1-9]': 'trl',
                    'URL': 'documentation_url',
                }
                
                # Handle multiple [0;1] columns by position
                # Based on test output, there are multiple columns named [0;1]
                # We need to identify them by index
                cols_list = list(df_va.columns)
                zero_one_indices = [i for i, col in enumerate(cols_list) if col == '[0;1]']
                
                # Map [0;1] columns by position (from Excel mapping order)
                if len(zero_one_indices) >= 1:
                    df_va.columns.values[zero_one_indices[0]] = 'service_running'
                if len(zero_one_indices) >= 2:
                    df_va.columns.values[zero_one_indices[1]] = 'parametrization'
                if len(zero_one_indices) >= 3:
                    df_va.columns.values[zero_one_indices[2]] = 'provides_data'
                if len(zero_one_indices) >= 4:
                    df_va.columns.values[zero_one_indices[3]] = 'license_exists'
                if len(zero_one_indices) >= 5:
                    df_va.columns.values[zero_one_indices[4]] = 'fully_described'
                if len(zero_one_indices) >= 6:
                    df_va.columns.values[zero_one_indices[5]] = 'qp_documentation'
                if len(zero_one_indices) >= 7:
                    df_va.columns.values[zero_one_indices[6]] = 'data_quality'
                if len(zero_one_indices) >= 8:
                    df_va.columns.values[zero_one_indices[7]] = 'payloads'
                if len(zero_one_indices) >= 9:
                    df_va.columns.values[zero_one_indices[8]] = 'converter_plugin'
                
                # Also handle the documentation_status column which has newlines
                doc_status_col = '[0, not implemented; 0.2 planned; \n0.5, partly implemented; 1, implemented]'
                if doc_status_col in df_va.columns:
                    df_va = df_va.rename(columns={doc_status_col: 'documentation_status'})
                
                # Apply other mappings
                existing_renames = {k: v for k, v in va_col_mapping.items() if k in df_va.columns}
                df_va = df_va.rename(columns=existing_renames)
                
                # Clean implementation values
                def clean_implementation_value(val):
                    if pd.isna(val) or val == '' or str(val).strip() == '':
                        return np.nan
                    if isinstance(val, str):
                        val_clean = val.strip().lower()
                        if val_clean in ['[request]', 'request', 'tbd', 'to be determined', 'n/a']:
                            return np.nan
                        try:
                            return float(val)
                        except:
                            return np.nan
                    try:
                        return float(val)
                    except:
                        return np.nan
                
                # Apply cleaning to numeric columns
                if 'implementation_status' in df_va.columns:
                    df_va['implementation_status'] = df_va['implementation_status'].apply(clean_implementation_value)
                
                if 'documentation_status' in df_va.columns:
                    df_va['documentation_status'] = df_va['documentation_status'].apply(clean_implementation_value)
                
                binary_cols = ['service_running', 'parametrization', 'provides_data', 'license_exists', 
                              'fully_described', 'qp_documentation', 'data_quality', 'payloads', 'converter_plugin']
                for col in binary_cols:
                    if col in df_va.columns:
                        df_va[col] = df_va[col].apply(clean_implementation_value)
                
        except gspread.exceptions.WorksheetNotFound:
            st.error("❌ Worksheet 'ILM_Connector' not found!")
            st.info(f"🔍 Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
            return None, None, None, None, None, None, "VA worksheet not found"
        except Exception as e:
            import traceback
            st.error(f"❌ Error loading VA data: {str(e)}")
            st.code(traceback.format_exc())
            return None, None, None, None, None, None, f"VA data error: {str(e)}"
        
        # Load Transnational Access data
        try:
            worksheet_ta = spreadsheet.worksheet("ILM_Connector_TA")
            data_ta = worksheet_ta.get_all_values()
            if len(data_ta) < 4:
                df_ta = pd.DataFrame()
                ta_header4 = None
                ta_raw = pd.DataFrame()
            else:
                # Same trick as for VA: keep the first four rows for the Data
                # tab's MultiIndex header, then build a cleaned-up frame for
                # analytics by renaming columns to short internal names.
                ta_header4 = [list(data_ta[i]) for i in range(4)]
                df_ta  = pd.DataFrame(data_ta[4:], columns=data_ta[3])
                ta_raw = df_ta.copy()
                
                # Map TA column names (these have newlines too!)
                ta_col_mapping = {
                    'Installation ID': 'installation_id',
                    'Project ID': 'project_id',
                    'PI Gender ': 'pi_gender',
                    'PI Gender': 'pi_gender',
                    'Project title': 'project_title',
                    'Project acronym': 'project_acronym',
                    'TA host': 'ta_host',
                    'PI Affiliation': 'pi_affiliation',
                    # This column has newlines!
                    'Project Stage\n(completed milestone)': 'project_stage',
                    'Stage updated on': 'stage_updated',
                    # This column has newlines!
                    'Comments to the stage\n(optional)': 'stage_comments',
                    'Start of the Visit/Access': 'visit_start',
                    'End of the Visit/Access': 'visit_end',
                    'Unit of access': 'unit_of_access',
                    'Number of units requested': 'units_requested',
                    'Number of Users': 'number_of_users',
                    'Number of units used': 'units_used',
                    'Short description of the activity': 'activity_description',
                    'Expected assets as outcomes': 'expected_outcomes',
                    'Delivered assets as outcomes': 'delivered_outcomes',
                    'Metadata of the outcome': 'outcome_metadata',
                    'Level of access': 'access_level',
                    'Associated WP': 'associated_wp',
                    'Associated VA': 'associated_va',
                    'Associated RI': 'associated_ri',
                    'Expected strategy of integration': 'integration_strategy',
                    'Service provider contact ': 'provider_contact',
                    'Service provider contact': 'provider_contact',
                }
                
                existing_renames = {k: v for k, v in ta_col_mapping.items() if k in df_ta.columns}
                df_ta = df_ta.rename(columns=existing_renames)
                
        except gspread.exceptions.WorksheetNotFound:
            st.warning("⚠️ Worksheet 'ILM_Connector_TA' not found (optional)")
            df_ta = pd.DataFrame()
            ta_header4 = None
            ta_raw = pd.DataFrame()
        except Exception as e:
            st.warning(f"⚠️ Error loading TA data: {str(e)}")
            df_ta = pd.DataFrame()
            ta_header4 = None
            ta_raw = pd.DataFrame()
        
        # Tuple shape kept consistent with load_excel_data + a trailing error msg.
        return df_va, df_ta, va_header4, ta_header4, va_raw, ta_raw, None
        
    except gspread.exceptions.APIError as e:
        error_msg = f"Google Sheets API Error: {str(e)}"
        st.error(f"❌ {error_msg}")
        st.info("💡 Make sure the sheet is shared with your service account email")
        return None, None, None, None, None, None, error_msg
    except gspread.exceptions.SpreadsheetNotFound:
        error_msg = "Spreadsheet not found or not accessible"
        st.error(f"❌ {error_msg}")
        st.info("💡 Check: 1) Sheet URL is correct, 2) Sheet is shared with service account")
        return None, None, None, None, None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        st.error(f"❌ {error_msg}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, None, None, None, None, error_msg

# Load data from Google Sheets (PRIMARY SOURCE - REAL-TIME).
# The loader now returns six payloads + an error message:
#   va_df_gs       : cleaned VA frame with renamed columns
#   ta_df_gs       : cleaned TA frame with renamed columns
#   va_header4_gs  : first four rows of the VA sheet (for the Data tab's MultiIndex)
#   ta_header4_gs  : first four rows of the TA sheet (for the Data tab's MultiIndex)
#   va_raw_gs      : VA frame with the original Excel/Sheets column names
#   ta_raw_gs      : TA frame with the original Excel/Sheets column names
#   error          : non-None string if loading failed
(va_df_gs, ta_df_gs,
 va_header4_gs, ta_header4_gs,
 va_raw_gs, ta_raw_gs, error) = load_google_sheets_data()

if va_df_gs is not None and not va_df_gs.empty:
    # SUCCESS: Use the live Google Sheets payload.
    va_df,       ta_df       = va_df_gs,       ta_df_gs
    va_header4,  ta_header4  = va_header4_gs,  ta_header4_gs
    va_raw,      ta_raw      = va_raw_gs,      ta_raw_gs
    data_source = "Google Sheets ✅ (Real-time)"
else:
    # FALLBACK: Read from the local Excel workbook. We attempt the Excel
    # load FIRST and only emit a warning if BOTH sources fail — that keeps
    # the UI clean in normal local-dev runs where Google Sheets isn't
    # configured but the Excel backup is right there.
    (va_df, ta_df,
     va_header4, ta_header4,
     va_raw, ta_raw) = load_excel_data()
    data_source = "Excel File (Backup)"

    if va_df is not None and not va_df.empty:
        # Excel rescued us — show a single, low-key info line instead of the
        # scary red "Authentication error" wall that earlier versions
        # produced. The actual auth error (if any) is still available in
        # the `error` variable for debugging.
        st.info(
            f"ℹ️ Running on the Excel backup (`{EXCEL_PATH}`). "
            f"Live Google Sheets data is unavailable — this is normal when "
            f"no credentials are configured locally."
        )
    
    if va_df is None or va_df.empty:
        st.error("❌ No data available! Please check:")
        st.markdown("""
        1. **Google Sheets Setup:**
           - Credentials file: `valiant-splicer-409609-e34abed30cc1.json` in same folder
           - Sheet shared with service account email
           - Worksheet names: `ILM_Connector` and `ILM_Connector_TA`
        
        2. **Or Excel Backup:**
           - Place `GeoINQUIRE-ImplementationLevelMatrix.xlsx` (or the legacy
             `ILM_Python_2.xlsx`) in the same folder
           
        3. **Test Connection:**
           - Run: `python test_google_sheets.py`
        """)
        st.stop()

# ------------------------------- Helper Functions (ORIGINAL) -------------------------------
def standardize_implementation_value(val):
    """Standardize implementation values to categorical labels"""
    if pd.isna(val):
        return 'Unknown'
    try:
        val_float = float(val)
        if val_float >= 1.0:
            return 'Implemented'
        elif val_float >= 0.5:
            return 'Partly implemented'
        elif val_float >= 0.2:
            return 'Planned'
        else:
            return 'Not implemented'
    except:
        return 'Unknown'

def standardize_binary_value(val):
    """Standardize binary values to Yes/No"""
    if pd.isna(val):
        return 'N/A'
    try:
        val_float = float(val)
        return 'Yes' if val_float >= 1.0 else 'No'
    except:
        return 'N/A'

def compute_va_statistics(df):
    """Compute statistics for Virtual Access"""
    if df is None or df.empty:
        return {}
    
    stats = {}
    
    if 'implementation_status' in df.columns:
        impl_counts = df['implementation_status'].apply(standardize_implementation_value).value_counts().to_dict()
        stats['implementation'] = impl_counts
    
    if 'service_running' in df.columns:
        running_counts = df['service_running'].apply(standardize_binary_value).value_counts().to_dict()
        stats['service_running'] = running_counts
    
    if 'parametrization' in df.columns:
        param_counts = df['parametrization'].apply(standardize_binary_value).value_counts().to_dict()
        stats['parametrization'] = param_counts
    
    if 'fully_described' in df.columns:
        desc_counts = df['fully_described'].apply(standardize_binary_value).value_counts().to_dict()
        stats['fully_described'] = desc_counts
    
    if 'documentation_status' in df.columns:
        doc_counts = df['documentation_status'].apply(standardize_implementation_value).value_counts().to_dict()
        stats['documentation'] = doc_counts
    
    if 'payloads' in df.columns:
        payload_counts = df['payloads'].apply(standardize_binary_value).value_counts().to_dict()
        stats['payloads'] = payload_counts
    
    if 'auth_method' in df.columns:
        auth_counts = df['auth_method'].value_counts().head(5).to_dict()
        stats['auth'] = auth_counts
    
    if 'data_policy' in df.columns:
        policy_counts = df['data_policy'].value_counts().to_dict()
        stats['policy'] = policy_counts
    
    if 'converter_plugin' in df.columns:
        conv_counts = df['converter_plugin'].apply(standardize_binary_value).value_counts().to_dict()
        stats['converter'] = conv_counts
    
    return stats

# ===============================================================================================
# HELPER — Build a 4-row MultiIndex header from the first four rows of the source sheet
# ===============================================================================================
# The user asked that the Data tab show the same header as in the Excel file:
# the first four rows form a hierarchical header (group band → topic → criteria → name).
# pandas already supports MultiIndex columns natively in st.dataframe, so we wrap
# the four raw rows into a MultiIndex and assign it as the frame's columns.
# ===============================================================================================
def build_four_row_header(header_rows, ncols):
    """
    Build a 4-level pandas.MultiIndex from rows 1–4 of the source sheet.

    Parameters
    ----------
    header_rows : list[list]   Four lists of equal length (rows 1, 2, 3, 4).
    ncols       : int          Number of columns the resulting MultiIndex must have.

    Returns
    -------
    pandas.MultiIndex with levels named (Group, Topic, Criteria, Column).

    Notes
    -----
    * Empty cells (NaN / None / "") in rows 1–3 are forward-filled along the
      row so a merged group band like "Implementation Level 1" propagates to
      the columns it spans in the Excel sheet.  Row 4 (the real column names)
      is NEVER forward-filled — every column keeps its own name.
    * If rows are shorter than ``ncols`` (can happen when the sheet has
      trailing empty columns) they are right-padded with empty strings.
    """
    levels = []
    last_seen = ["", "", "", ""]                         # Forward-fill memory per level
    # Pad / truncate each row to ncols so they all have the same width
    padded = []
    for r in header_rows:
        row = [("" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v).strip())
               for v in r]
        if len(row) < ncols:
            row = row + [""] * (ncols - len(row))
        else:
            row = row[:ncols]
        padded.append(row)

    # Forward-fill rows 1–3 (indices 0–2); leave row 4 (index 3) untouched.
    for level_idx in range(4):
        new_row = []
        for col_idx in range(ncols):
            val = padded[level_idx][col_idx]
            if level_idx < 3:
                # Forward-fill across this row for the group/topic/criteria bands
                if val == "":
                    val = last_seen[level_idx]
                else:
                    last_seen[level_idx] = val
            new_row.append(val if val != "" else " ")     # MultiIndex dislikes empty strings
        levels.append(new_row)

    # Build the MultiIndex; the tuple order must match the row order.
    tuples = list(zip(*levels))
    return pd.MultiIndex.from_tuples(
        tuples,
        names=["Group", "Topic", "Criteria", "Column"]
    )


# ===============================================================================================
# HELPER — Render a figure inside four year tabs (2023, 2024, 2025, 2026)
# ===============================================================================================
# The user asked that every figure in the VA Dashboard and in the Analytics
# section be wrapped in four year tabs so they can later append year-specific
# figures.  This helper centralises the pattern so each chart only needs one
# call instead of duplicating tab boilerplate everywhere.
#
# Each tab contains:
#   * an `st.info(...)` banner explaining the tab is a placeholder.
#   * a clearly-marked comment block ("APPEND YEAR-XXXX FIGURE HERE") that the
#     user can locate quickly when pasting their own per-year figure later.
#   * the all-years figure rendered as a starting point so the dashboard
#     never looks empty.
#   * a single download button under the latest year tab (2026) to avoid
#     duplicating identical buttons on every tab.
# ===============================================================================================
def render_in_year_tabs(fig, figure_key, source_cols=None, access_type="VA",
                        download_label_base=None, figure_title=""):
    """
    Render ``fig`` inside four tabs labelled by ``YEAR_TABS``.

    Parameters
    ----------
    fig                 : plotly.graph_objects.Figure or matplotlib Figure
        The all-years figure to show as a placeholder inside each tab.
    figure_key          : str
        Stable identifier used for Streamlit widget keys (must be unique
        across the page).  Year and tab suffixes are appended automatically.
    source_cols         : list[str] | None
        Internal column keys for ``add_source_annotation`` (optional).
    access_type         : "VA" or "TA"
        Selects which source-column mapping is used in the annotation.
    download_label_base : str | None
        Filename base for the PNG download button.  If None no button is
        rendered.
    figure_title        : str
        Human-readable figure title used inside the placeholder banner.
    """
    if fig is None:
        st.info(f"⚠️ No data available for: {figure_title or figure_key}")
        return

    # Create the four year tabs in the order defined by YEAR_TABS.
    year_tab_labels = [f"📅 {y}" for y in YEAR_TABS]
    tabs = st.tabs(year_tab_labels)

    for tab, year in zip(tabs, YEAR_TABS):
        with tab:
            # ╔══════════════════════════════════════════════════════════════╗
            # ║  >>> APPEND YEAR-{year} FIGURE FOR THIS CHART BELOW <<<      ║
            # ║                                                              ║
            # ║  This tab currently shows the all-years figure as a place-   ║
            # ║  holder.  Replace the `st.plotly_chart` / `st.pyplot` call   ║
            # ║  below with the chart built from data filtered to year       ║
            # ║  == {year} once it becomes available.                        ║
            # ╚══════════════════════════════════════════════════════════════╝
            st.info(
                f"📅 **{year} view of '{figure_title or figure_key}'** — placeholder. "
                f"Replace the chart below with a {year}-specific figure when ready."
            )

            # Render the placeholder figure.  We branch on figure type because
            # the heatmap is a matplotlib Figure while everything else is
            # Plotly.  Streamlit handles both via different functions.
            if isinstance(fig, plt.Figure):
                st.pyplot(fig, clear_figure=False, use_container_width=False)
            else:
                st.plotly_chart(
                    fig,
                    use_container_width=False,
                    key=f"{figure_key}_{year}"
                )

            # Show the source-column annotation only once per tab.
            if source_cols:
                add_source_annotation(source_cols, access_type=access_type)

            # Render a single download button under the most recent year tab
            # to avoid cluttering every tab with identical buttons.
            if download_label_base and year == YEAR_TABS[-1]:
                create_download_button(
                    fig,
                    f"{download_label_base}_{year}",
                    col_keys=source_cols,
                    access_type=access_type,
                )



# ===============================================================================================
# COLUMN SOURCE MAPPING — Maps internal column names to original ILM table column names
# ===============================================================================================
# This mapping allows each figure to display which original column(s) from the ILM table
# were used, so readers can backtrack to the source data.
# ===============================================================================================
VA_COLUMN_SOURCES = {
    'compliant_ri': 'Compliant with Research infrastructure (RI)',
    'implementation_status': 'Implementation status to RI [0; not implemented, 0.2; planned, 0.5; partly implemented, 1; implemented]',
    'data_repr': 'Data Representations [georeferenced/non-georeferenced/time-series/software]',
    'license': 'License',
    'metadata_standard': 'Standard of metadata describing the service at RI integration level (not data)',
    'service_running': '[0;1] - Service Running',
    'api_standard': '(OGC, ERDDAP, etc)',
    'parametrization': '[0;1] - Parametrization',
    'fully_described': '[0;1] - Fully Described',
    'documentation_status': '[0, not implemented; 0.2 planned; 0.5, partly implemented; 1, implemented]',
    'payloads': '[0;1] - Payloads',
    'auth_method': '[e.g. OAuth, SAML, API access token, none]',
    'data_policy': '[open; restricted; embargoed]',
    'converter_plugin': '[0;1] - Converter Plugin',
    'completeness_pct': '[%] - Completeness',
    'trl': '[1-9] - TRL',
    'domain': 'Scientific domain/category',
    'service_name': 'Service/Installation Name',
    'installation_id': 'Installation ID',
    'service_id': 'Service ID',
    'wp': 'WP',
}

TA_COLUMN_SOURCES = {
    'project_id': 'Project ID',
    'pi_gender': 'PI Gender',
    'project_title': 'Project title',
    'project_acronym': 'Project acronym',
    'ta_host': 'TA host',
    'pi_affiliation': 'PI Affiliation',
    'project_stage': 'Project Stage (completed milestone)',
    'stage_updated': 'Stage updated on',
    'visit_start': 'Start of the Visit/Access',
    'visit_end': 'End of the Visit/Access',
    'unit_of_access': 'Unit of access',
    'units_requested': 'Number of units requested',
    'number_of_users': 'Number of Users',
    'units_used': 'Number of units used',
    'expected_outcomes': 'Expected assets as outcomes',
    'delivered_outcomes': 'Delivered assets as outcomes',
    'access_level': 'Level of access',
    'associated_wp': 'Associated WP',
    'associated_va': 'Associated VA',
    'associated_ri': 'Associated RI',
    'integration_strategy': 'Expected strategy of integration',
    'call': 'Project ID (derived: Call number)',
}


def add_source_annotation(col_keys, access_type="VA"):
    """Add a discreet italic annotation showing the original ILM column name(s) used for a figure."""
    source_map = VA_COLUMN_SOURCES if access_type == "VA" else TA_COLUMN_SOURCES
    if isinstance(col_keys, str):
        col_keys = [col_keys]
    sources = []
    for key in col_keys:
        if key in source_map:
            sources.append(source_map[key])
    if sources:
        source_text = " | ".join(sources)
        st.markdown(
            f'<p style="font-size: 0.7rem; font-style: italic; color: #999; margin: 0.1rem 0 0.5rem 0; line-height: 1.2;">'
            f'Source column: {source_text}</p>',
            unsafe_allow_html=True
        )


# ===============================================================================================
# PROFESSIONAL PNG EXPORT (300 DPI) 
# ===============================================================================================
def create_download_button(fig, filename_base, col_keys=None, access_type="VA"):
    """Create professional PNG download button at 300 DPI using kaleido.
    Also adds column source annotation if col_keys are provided."""
    if fig is None:
        return
    
    # Add column source annotation if provided
    if col_keys:
        add_source_annotation(col_keys, access_type)
    
    try:
        # Try PNG export at 300 DPI using kaleido
        png_bytes = fig.to_image(
            format="png",
            width=1200,
            height=800,
            scale=3  # 3x scale = ~300 DPI at print size
        )
        
        st.download_button(
            label="\u2b07 Download PNG (300 DPI)",
            data=png_bytes,
            file_name=f"{filename_base}.png",
            mime="image/png",
            key=f"png_{filename_base}"
        )
    except Exception:
        # Fallback: export as HTML with high-res camera button
        try:
            html_bytes = fig.to_html(
                include_plotlyjs='cdn',
                config={
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': filename_base,
                        'height': 800,
                        'width': 1200,
                        'scale': 3
                    },
                    'displayModeBar': True,
                    'displaylogo': False
                }
            ).encode()
            
            st.download_button(
                label="\u2b07 Download HTML (use camera icon for PNG)",
                data=html_bytes,
                file_name=f"{filename_base}.html",
                mime="text/html",
                key=f"html_{filename_base}"
            )
        except Exception as e:
            st.caption(f"Export not available: {str(e)}")


# ------------------------------- Enhanced Complex Heatmap -------------------------------
def create_enhanced_heatmap(df):
    """Create a professional heatmap with enhanced styling showing implementation matrix"""
    if df is None or df.empty:
        return None
    
    # Use the correct column names from our data
    if 'compliant_ri' not in df.columns or 'implementation_status' not in df.columns:
        return None
    
    # Prepare data
    ris = sorted([x for x in df['compliant_ri'].unique() if pd.notna(x)])
    
    # Get data representations
    if 'data_repr' in df.columns:
        drs_all = []
        for val in df['data_repr'].dropna():
            parts = str(val).split(',')
            for rep in parts:
                rep = rep.strip()
                if rep and rep not in drs_all and rep.lower() not in ['nan', 'unknown', 'none']:
                    drs_all.append(rep)
        # Take top 6 most common
        drs = sorted(drs_all[:6]) if drs_all else ['Georeferenced', 'Time-series', 'Software']
    else:
        drs = ['Georeferenced', 'Time-series', 'Software']
    
    # Create matrices
    total_matrix = np.zeros((len(ris), len(drs)))
    implemented_matrix = np.zeros((len(ris), len(drs)))
    
    for i, ri in enumerate(ris):
        for j, dr in enumerate(drs):
            # Count services for this RI and data representation.
            mask = (df['compliant_ri'] == ri)
            if 'data_repr' in df.columns:
                # `dr` may contain regex-special characters (e.g. "time-series",
                # "georeferenced/non-georeferenced"). Pass `regex=False` to treat
                # the needle as a literal substring — this also silences the
                # "pattern is interpreted as a regular expression, and has match
                # groups" UserWarning that pandas emits for parenthesised values.
                mask = mask & (
                    df['data_repr'].astype(str)
                                   .str.contains(dr, na=False, case=False, regex=False)
                )
            
            total_count = mask.sum()
            total_matrix[i, j] = total_count
            
            if total_count > 0:
                # Count implemented services
                impl_mask = mask & (df['implementation_status'].apply(
                    lambda x: standardize_implementation_value(x) == 'Implemented'
                ))
                impl_count = impl_mask.sum()
                implemented_matrix[i, j] = impl_count
    
    # Create figure with matplotlib
    fig, ax = plt.subplots(figsize=(16, 10), dpi=100)
    
    # Use seaborn for the heatmap
    sns.heatmap(implemented_matrix, cmap="RdYlGn", cbar=True, linewidths=1.5, linecolor="white", 
                xticklabels=drs, yticklabels=ris, ax=ax,
                cbar_kws={'label': 'Implemented Services', 'shrink': 0.8})
    
    # Add annotations
    for i in range(len(ris)):
        for j in range(len(drs)):
            if total_matrix[i,j] > 0:
                # Total count - center, large and bold
                ax.text(j+0.5, i+0.5, f'{int(total_matrix[i,j])}', 
                       ha='center', va='center',
                       color='black', fontsize=16, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                edgecolor='gray', alpha=0.9, linewidth=2))
                
                # Implemented count - bottom left corner
                ax.text(j+0.18, i+0.82, f'{int(implemented_matrix[i,j])}✓', 
                       ha='center', va='center',
                       color='#145A32', fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#A9DFBF', 
                                edgecolor='#145A32', alpha=0.9, linewidth=1.5))
    
    # Enhanced title and labels
    ax.set_title('Implementation Matrix Analysis\nTotal Services (center) | Implemented Services (green corner)', 
                pad=20, fontsize=18, fontweight='bold', family='Arial')
    ax.set_xlabel('Data Representations', fontsize=14, fontweight='bold', family='Arial')
    ax.set_ylabel('Research Infrastructure', fontsize=14, fontweight='bold', family='Arial')
    
    # Improve tick labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11, family='Arial')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11, family='Arial')
    
    # Add legend
    from matplotlib.patches import Rectangle
    legend_elements = [
        Rectangle((0, 0), 1, 1, fc='white', ec='gray', lw=2, label='Total Services (center)'),
        Rectangle((0, 0), 1, 1, fc='#A9DFBF', ec='#145A32', lw=1.5, label='Implemented (green corner)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.15, 1), 
             fontsize=10, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    return fig


# ------------------------------- ORIGINAL VA Chart Functions -------------------------------
def create_professional_bar_chart(df, x, y, title, orientation='v', color_palette=None):
    """Create a professional bar chart"""
    if df is None or df.empty:
        return go.Figure()
    
    if color_palette is None:
        color_palette = COLORS['blue_palette']
    
    fig = go.Figure()
    
    if orientation == 'v':
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[y],
            marker=dict(
                color=color_palette if isinstance(color_palette, list) else [color_palette] * len(df),
                line=dict(width=0)
            ),
            text=df[y],
            textposition='outside',
            textfont=dict(size=12, family=FONT_FAMILY),
            showlegend=False
        ))
    else:
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[y],
            orientation='h',
            marker=dict(
                color=color_palette if isinstance(color_palette, list) else [color_palette] * len(df),
                line=dict(width=0)
            ),
            text=df[x],
            textposition='outside',
            textfont=dict(size=12, family=FONT_FAMILY),
            showlegend=False
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
        xaxis=dict(showgrid=False, zeroline=False, title='', tickfont=dict(size=TICK_FONT_SIZE)),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False, title='', tickfont=dict(size=TICK_FONT_SIZE)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=40),
        height=500,
        width=1200,  # FIXED WIDTH
        font=dict(family=FONT_FAMILY),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        )
    )
    
    return fig

def create_professional_donut_chart(df, names, values, title, color_map=None):
    """Create a professional donut chart"""
    if df is None or df.empty:
        return go.Figure()
    
    if color_map:
        colors = [color_map.get(name, COLORS['info']) for name in df[names]]
    else:
        colors = COLORS['multi_palette'][:len(df)]
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=df[names],
        values=df[values],
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, family=FONT_FAMILY),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=100),
        height=500,
        width=1200,  # FIXED WIDTH
        font=dict(family=FONT_FAMILY),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            traceorder="normal"
        )
    )
    
    return fig

def create_professional_pie_chart(df, names, values, title, color_map=None):
    """Create a professional pie chart"""
    if df is None or df.empty:
        return go.Figure()
    
    if color_map:
        colors = [color_map.get(name, COLORS['info']) for name in df[names]]
    else:
        colors = COLORS['multi_palette'][:len(df)]
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=df[names],
        values=df[values],
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='percent',
        textfont=dict(size=11, family=FONT_FAMILY),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=100),
        height=500,
        width=1200,  # FIXED WIDTH
        font=dict(family=FONT_FAMILY),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
            traceorder="normal"
        )
    )
    
    return fig

# ------------------------------- MAIN CONTENT -------------------------------

if selected == "Dashboard":
    st.markdown(f"<span class='small'>Home → Dashboard ({data_source})</span>", unsafe_allow_html=True)
    st.header("Overview")
    
    if project_label == "Virtual Access":
        # Virtual Access Dashboard
        if va_df is not None and not va_df.empty:
            # KPI Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total = len(va_df)
                st.markdown(f"<div class='kpi'><h3>Total Services</h3><div class='val'>{total}</div></div>", unsafe_allow_html=True)
            with col2:
                impl_count = len(va_df[va_df['implementation_status'].apply(lambda x: standardize_implementation_value(x) == 'Implemented')]) if 'implementation_status' in va_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>Implemented</h3><div class='val'>{impl_count}</div></div>", unsafe_allow_html=True)
            with col3:
                running_count = len(va_df[va_df['service_running'].apply(lambda x: standardize_binary_value(x) == 'Yes')]) if 'service_running' in va_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>Services Running</h3><div class='val'>{running_count}</div></div>", unsafe_allow_html=True)
            with col4:
                ris = va_df['compliant_ri'].nunique() if 'compliant_ri' in va_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>Research Infrastructures</h3><div class='val'>{ris}</div></div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ===== 5 KEY DASHBOARD VISUALIZATIONS =====
            st.markdown("## 📊 Key Metrics Overview")
            
            # Row 1: RI and Implementation Status (2 columns)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                # ── FIGURE 1: Research Infrastructures (RI) ─────────────────────
                # Builds a bar chart of the number of services per RI.
                # The figure is then rendered inside four year tabs (2023–2026)
                # via `render_in_year_tabs`, with placeholder banners so the
                # user can replace each tab's content with year-specific data.
                if 'compliant_ri' in va_df.columns:
                    ri_counts = va_df['compliant_ri'].value_counts().to_dict()
                    ri_data = pd.DataFrame(list(ri_counts.items()), columns=['RI', 'Count']).sort_values('Count', ascending=False)
                    
                    # Build the all-years bar chart for RI distribution.
                    fig_ri = go.Figure()
                    fig_ri.add_trace(go.Bar(
                        x=ri_data['RI'],
                        y=ri_data['Count'],
                        marker=dict(
                            color=COLORS['blue_palette'][:len(ri_data)],
                            line=dict(width=0)
                        ),
                        text=ri_data['Count'],
                        textposition='outside',
                        textfont=dict(size=14, family=FONT_FAMILY, color=COLORS['dark']),
                        showlegend=False
                    ))
                    
                    fig_ri.update_layout(
                        title=dict(text='1. Research Infrastructures (RI)', 
                                 font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                        xaxis=dict(title='Research Infrastructure', showgrid=False, tickfont=dict(size=TICK_FONT_SIZE)),
                        yaxis=dict(title='Number of Services', showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickfont=dict(size=TICK_FONT_SIZE)),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=450,
                        width=580,
                        margin=dict(l=60, r=40, t=80, b=60),
                        font=dict(family=FONT_FAMILY)
                    )
                    
                    # Render inside the four year tabs (2023, 2024, 2025, 2026).
                    render_in_year_tabs(
                        fig_ri,
                        figure_key="ri_distribution",
                        source_cols=["compliant_ri"],
                        access_type="VA",
                        download_label_base="ri_distribution",
                        figure_title="1. Research Infrastructures (RI)",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                # ── FIGURE 2: Implementation Status to RI ───────────────────────
                # Donut chart of services by implementation status. The chart is
                # rendered inside four year tabs (2023–2026) so per-year figures
                # can be appended later.
                if 'implementation_status' in va_df.columns:
                    impl_counts = va_df['implementation_status'].apply(standardize_implementation_value).value_counts().to_dict()
                    impl_data = pd.DataFrame(list(impl_counts.items()), columns=['Status', 'Count']).sort_values('Count', ascending=False)
                    
                    color_map = {
                        'Implemented': COLORS['implemented'],
                        'Partly implemented': COLORS['partly_implemented'],
                        'Planned': COLORS['planned'],
                        'Not implemented': COLORS['not_implemented'],
                        'Unknown': COLORS['unknown']
                    }
                    colors = [color_map.get(s, COLORS['info']) for s in impl_data['Status']]
                    
                    fig_impl = go.Figure()
                    fig_impl.add_trace(go.Pie(
                        labels=impl_data['Status'],
                        values=impl_data['Count'],
                        hole=0.4,
                        marker=dict(colors=colors, line=dict(color='white', width=2)),
                        textinfo='label+percent',
                        textfont=dict(size=12, family=FONT_FAMILY),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                    ))
                    
                    fig_impl.update_layout(
                        title=dict(text='2. Implementation Status to RI',
                                 font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=450,
                        width=580,
                        font=dict(family=FONT_FAMILY),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        ),
                        margin=dict(l=40, r=40, t=80, b=100)
                    )
                    
                    render_in_year_tabs(
                        fig_impl,
                        figure_key="implementation_status",
                        source_cols=["implementation_status"],
                        access_type="VA",
                        download_label_base="implementation_status",
                        figure_title="2. Implementation Status to RI",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 2: Data Representations and License (2 columns)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'data_repr' in va_df.columns:
                    # Simplify data representations for better visualization
                    def simplify_data_repr(val):
                        if pd.isna(val):
                            return 'Unknown'
                        val_str = str(val).lower()
                        if 'georeferenced' in val_str and 'time-series' in val_str:
                            return 'Georeferenced + Time-series'
                        elif 'georeferenced' in val_str and 'non-georeferenced' not in val_str:
                            return 'Georeferenced'
                        elif 'software' in val_str:
                            return 'Software'
                        elif 'non-georeferenced' in val_str:
                            return 'Non-Georeferenced'
                        elif 'blended' in val_str:
                            return 'Blended'
                        else:
                            return 'Other'
                    
                    data_repr_counts = va_df['data_repr'].apply(simplify_data_repr).value_counts().head(8).to_dict()
                    data_repr_data = pd.DataFrame(list(data_repr_counts.items()), columns=['Type', 'Count']).sort_values('Count', ascending=True)
                    
                    fig_repr = go.Figure()
                    fig_repr.add_trace(go.Bar(
                        x=data_repr_data['Count'],
                        y=data_repr_data['Type'],
                        orientation='h',
                        marker=dict(
                            color=COLORS['green_palette'][:len(data_repr_data)],
                            line=dict(width=0)
                        ),
                        text=data_repr_data['Count'],
                        textposition='outside',
                        textfont=dict(size=12, family=FONT_FAMILY),
                        showlegend=False
                    ))
                    
                    fig_repr.update_layout(
                        title=dict(text='3. Data Representations',
                                 font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                        xaxis=dict(title='Number of Services', showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickfont=dict(size=TICK_FONT_SIZE)),
                        yaxis=dict(title='', showgrid=False, tickfont=dict(size=TICK_FONT_SIZE)),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=450,
                        width=580,
                        margin=dict(l=200, r=40, t=80, b=60),
                        font=dict(family=FONT_FAMILY)
                    )
                    
                    render_in_year_tabs(
                        fig_repr,
                        figure_key="data_representations",
                        source_cols=["data_repr"],
                        access_type="VA",
                        download_label_base="data_representations",
                        figure_title="3. Data Representations",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'license' in va_df.columns:
                    # Simplify license names for better visualization
                    def simplify_license(val):
                        if pd.isna(val):
                            return 'Unknown'
                        val_str = str(val).upper()
                        if 'CC-BY 4.0' in val_str or 'CC-BY-4.0' in val_str or 'CC BY 4.0' in val_str:
                            return 'CC-BY 4.0'
                        elif 'CC-BY-NC' in val_str or 'CC BY-NC' in val_str:
                            return 'CC-BY-NC'
                        elif 'CC-BY-ND' in val_str or 'CC BY-ND' in val_str:
                            return 'CC-BY-ND'
                        elif 'GPL' in val_str or 'AGPL' in val_str:
                            return 'GPL/AGPL'
                        elif 'FROM DATA OWNER' in val_str:
                            return 'From Data Owner'
                        elif 'EACH DATASET' in val_str:
                            return 'Per Dataset'
                        elif 'MIT' in val_str:
                            return 'MIT'
                        elif 'BSD' in val_str:
                            return 'BSD'
                        else:
                            return 'Other'
                    
                    license_counts = va_df['license'].apply(simplify_license).value_counts().head(8).to_dict()
                    license_data = pd.DataFrame(list(license_counts.items()), columns=['License', 'Count']).sort_values('Count', ascending=False)
                    
                    fig_license = go.Figure()
                    fig_license.add_trace(go.Pie(
                        labels=license_data['License'],
                        values=license_data['Count'],
                        marker=dict(colors=COLORS['multi_palette'][:len(license_data)], line=dict(color='white', width=2)),
                        textinfo='label+percent',
                        textfont=dict(size=11, family=FONT_FAMILY),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                    ))
                    
                    fig_license.update_layout(
                        title=dict(text='4. License Distribution',
                                 font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=450,
                        width=580,
                        font=dict(family=FONT_FAMILY),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.25,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=9)
                        ),
                        margin=dict(l=40, r=40, t=80, b=110)
                    )
                    
                    render_in_year_tabs(
                        fig_license,
                        figure_key="va_license_distribution",
                        source_cols=["license"],
                        access_type="VA",
                        download_label_base="license_distribution",
                        figure_title="4. License Distribution",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 3: Metadata Standards (full width)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            if 'metadata_standard' in va_df.columns:
                metadata_counts = va_df['metadata_standard'].value_counts().head(10).to_dict()
                metadata_data = pd.DataFrame(list(metadata_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                
                fig_metadata = go.Figure()
                fig_metadata.add_trace(go.Bar(
                    x=metadata_data['Standard'],
                    y=metadata_data['Count'],
                    marker=dict(
                        color=COLORS['blue_palette'][:len(metadata_data)],
                        line=dict(width=0)
                    ),
                    text=metadata_data['Count'],
                    textposition='outside',
                    textfont=dict(size=13, family=FONT_FAMILY),
                    showlegend=False
                ))
                
                fig_metadata.update_layout(
                    title=dict(text='5. Standards of Metadata Describing the Service',
                             font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                    xaxis=dict(title='Metadata Standard', showgrid=False, tickfont=dict(size=TICK_FONT_SIZE), tickangle=-45),
                    yaxis=dict(title='Number of Services', showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickfont=dict(size=TICK_FONT_SIZE)),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=450,
                    width=1200,
                    margin=dict(l=60, r=40, t=80, b=120),
                    font=dict(family=FONT_FAMILY)
                )
                
                render_in_year_tabs(
                    fig_metadata,
                    figure_key="va_metadata_standards_dashboard",
                    source_cols=["metadata_standard"],
                    access_type="VA",
                    download_label_base="metadata_standards",
                    figure_title="5. Standards of Metadata Describing the Service",
                )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            # Implementation Matrix Heatmap (full width)
            # ── This is figure "6" in the VA Dashboard: a matplotlib heatmap
            #    showing the count of services per (RI × Data Representation).
            #    We wrap it inside the four year tabs (2023–2026) just like the
            #    other Dashboard figures so the user can append year-specific
            #    heatmaps later.
            st.markdown("## 📊 Implementation Matrix Analysis")
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if va_df is not None and not va_df.empty:
                try:
                    # Build the all-years heatmap once and reuse it across tabs.
                    fig_heatmap = create_enhanced_heatmap(va_df)
                    if fig_heatmap:
                        # Create the year tabs manually (matplotlib needs special
                        # download-button handling, so we don't go through the
                        # render_in_year_tabs helper here).
                        year_tab_labels = [f"📅 {y}" for y in YEAR_TABS]
                        _heatmap_tabs = st.tabs(year_tab_labels)
                        for _tab, _yr in zip(_heatmap_tabs, YEAR_TABS):
                            with _tab:
                                # ╔══════════════════════════════════════════════════════╗
                                # ║  >>> APPEND YEAR-{_yr} HEATMAP BELOW THIS LINE <<<   ║
                                # ║  Replace the call below with a year-specific build   ║
                                # ║  once year-filtered data is available.                ║
                                # ╚══════════════════════════════════════════════════════╝
                                st.info(
                                    f"📅 **{_yr} view of Implementation Matrix** — placeholder. "
                                    f"Replace the chart below with a {_yr}-specific heatmap when ready."
                                )
                                st.pyplot(fig_heatmap, clear_figure=False, use_container_width=False)
                                
                                # Render the download button only on the most recent
                                # year tab to avoid duplicate buttons / key clashes.
                                if _yr == YEAR_TABS[-1]:
                                    buf = io.BytesIO()
                                    fig_heatmap.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                                    buf.seek(0)
                                    st.download_button(
                                        label="📥 Download Implementation Matrix (High-Res PNG)",
                                        data=buf,
                                        file_name=f"implementation_matrix_heatmap_{_yr}.png",
                                        mime="image/png",
                                        key=f"heatmap_download_{_yr}",
                                    )
                                    add_source_annotation(
                                        ["compliant_ri", "implementation_status", "data_repr"],
                                        access_type="VA",
                                    )
                                    st.caption(
                                        "**Legend:** Large numbers in center = Total services | "
                                        "Green boxes with ✓ = Implemented services"
                                    )
                    else:
                        st.info("Heatmap data not available")
                except Exception as e:
                    st.warning(f"Could not generate heatmap: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Virtual Access data available")
    
    else:  # Transnational Access
        if ta_df is not None and not ta_df.empty:
            # KPI Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"<div class='kpi'><h3>Total Applications</h3><div class='val'>{len(ta_df)}</div></div>", unsafe_allow_html=True)
            with col2:
                hosts = ta_df['ta_host'].nunique() if 'ta_host' in ta_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>TA Hosts</h3><div class='val'>{hosts}</div></div>", unsafe_allow_html=True)
            with col3:
                completed = len(ta_df[ta_df['project_stage'].str.contains('exhausted', case=False, na=False)]) if 'project_stage' in ta_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>Completed</h3><div class='val'>{completed}</div></div>", unsafe_allow_html=True)
            with col4:
                calls = ta_df['call'].nunique() if 'call' in ta_df.columns else 0
                st.markdown(f"<div class='kpi'><h3>Calls</h3><div class='val'>{calls}</div></div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # TA Overview
            st.markdown("## 📊 Transnational Access Overview")
            col1, col2 = st.columns(2)
            
            with col1:
                if 'project_stage' in ta_df.columns:
                    stage_counts = ta_df['project_stage'].value_counts().to_dict()
                    stage_data = pd.DataFrame(list(stage_counts.items()), columns=['Stage', 'Count']).sort_values('Count', ascending=False)
                    stage_color_map = {
                        'Visit/access exhausted': COLORS['exhausted'],
                        'Time window for the visit/access fixed': COLORS['fixed'],
                        'Data/products ready': COLORS['ready'],
                        'PI contacted': COLORS['contacted'],
                        'Project details negotiated': COLORS['negotiated']
                    }
                    fig_stage = create_professional_donut_chart(stage_data, 'Stage', 'Count',
                                                               'Project Stage Distribution',
                                                               color_map=stage_color_map)
                    render_in_year_tabs(
                        fig_stage,
                        figure_key="project_stages",
                        source_cols=["project_stage"],
                        access_type="TA",
                        download_label_base="project_stages",
                        figure_title="Project Stages",
                    )
            with col2:
                if 'call' in ta_df.columns:
                    call_counts = ta_df['call'].value_counts().to_dict()
                    call_data = pd.DataFrame(list(call_counts.items()), columns=['Call', 'Count']).sort_values('Call')
                    fig_calls = create_professional_bar_chart(call_data, 'Call', 'Count',
                                                              'Applications by Call',
                                                              orientation='v',
                                                              color_palette=COLORS['blue_palette'])
                    render_in_year_tabs(
                        fig_calls,
                        figure_key="applications_by_call",
                        source_cols=["call"],
                        access_type="TA",
                        download_label_base="applications_by_call",
                        figure_title="Applications By Call",
                    )
        else:
            st.warning("No Transnational Access data available")

elif selected == "Analytics":
    st.markdown("<span class='small'>Home → Analytics</span>", unsafe_allow_html=True)
    st.header("Detailed Analytics")
    
    if project_label == "Virtual Access":
        # ORIGINAL VA ANALYTICS CODE
        if va_df is not None and not va_df.empty:
            va_stats = compute_va_statistics(va_df)
            
            st.markdown("## 🎯 Implementation Level 1")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'service_running' in va_stats:
                    running_data = pd.DataFrame(list(va_stats['service_running'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_running = create_professional_donut_chart(running_data, 'Status', 'Count',
                                                                 'Service Running Status',
                                                                 color_map=color_map)
                    render_in_year_tabs(
                        fig_running,
                        figure_key="service_running",
                        source_cols=["service_running"],
                        access_type="VA",
                        download_label_base="service_running",
                        figure_title="Service Running",
                    )
            st.markdown("---")
            
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'api_standard' in va_df.columns:
                    api_counts = va_df['api_standard'].value_counts().head(8).to_dict()
                    api_data = pd.DataFrame(list(api_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                    fig_api = create_professional_bar_chart(api_data, 'Standard', 'Count',
                                                           'API Standards Distribution',
                                                           orientation='v',
                                                           color_palette=COLORS['blue_palette'])
                    render_in_year_tabs(
                        fig_api,
                        figure_key="api_standards",
                        source_cols=["api_standard"],
                        access_type="VA",
                        download_label_base="api_standards",
                        figure_title="Api Standards",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'metadata_standard' in va_df.columns:
                    meta_counts = va_df['metadata_standard'].value_counts().head(6).to_dict()
                    meta_data = pd.DataFrame(list(meta_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                    fig_meta = create_professional_pie_chart(meta_data, 'Standard', 'Count',
                                                            'Metadata Standards')
                    render_in_year_tabs(
                        fig_meta,
                        figure_key="metadata_standards",
                        source_cols=["metadata_standard"],
                        access_type="VA",
                        download_label_base="metadata_standards",
                        figure_title="Metadata Standards",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("## 🚀 Implementation Level 2")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'parametrization' in va_stats:
                    param_data = pd.DataFrame(list(va_stats['parametrization'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_param = create_professional_donut_chart(param_data, 'Status', 'Count',
                                                               'Service Parametrization',
                                                               color_map=color_map)
                    render_in_year_tabs(
                        fig_param,
                        figure_key="parametrization",
                        source_cols=["parametrization"],
                        access_type="VA",
                        download_label_base="parametrization",
                        figure_title="Parametrization",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'license' in va_df.columns:
                    license_counts = va_df['license'].value_counts().head(6).to_dict()
                    license_data = pd.DataFrame(list(license_counts.items()), columns=['License', 'Count']).sort_values('Count', ascending=False)
                    fig_license = create_professional_pie_chart(license_data, 'License', 'Count',
                                                                'License Distribution')
                    render_in_year_tabs(
                        fig_license,
                        figure_key="license_types",
                        source_cols=["license"],
                        access_type="VA",
                        download_label_base="license_types",
                        figure_title="License Types",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'fully_described' in va_stats:
                    desc_data = pd.DataFrame(list(va_stats['fully_described'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_desc = create_professional_donut_chart(desc_data, 'Status', 'Count',
                                                              'Full Description Status',
                                                              color_map=color_map)
                    render_in_year_tabs(
                        fig_desc,
                        figure_key="fully_described",
                        source_cols=["fully_described"],
                        access_type="VA",
                        download_label_base="fully_described",
                        figure_title="Fully Described",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("## 🚀 Implementation Level 3")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'documentation' in va_stats:
                    doc_data = pd.DataFrame(list(va_stats['documentation'].items()), columns=['Status', 'Count']).sort_values('Count', ascending=False)
                    color_map = {
                        'Implemented': COLORS['implemented'],
                        'Partly implemented': COLORS['partly_implemented'],
                        'Planned': COLORS['planned'],
                        'Not implemented': COLORS['not_implemented'],
                        'Unknown': COLORS['unknown']
                    }
                    fig_doc = create_professional_bar_chart(doc_data, 'Status', 'Count',
                                                           'Documentation Status',
                                                           orientation='v',
                                                           color_palette=[color_map.get(s, COLORS['info']) for s in doc_data['Status']])
                    render_in_year_tabs(
                        fig_doc,
                        figure_key="documentation",
                        source_cols=["documentation_status"],
                        access_type="VA",
                        download_label_base="documentation",
                        figure_title="Documentation",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'payloads' in va_stats:
                    payload_data = pd.DataFrame(list(va_stats['payloads'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_payload = create_professional_donut_chart(payload_data, 'Status', 'Count',
                                                                 'Payload Support',
                                                                 color_map=color_map)
                    render_in_year_tabs(
                        fig_payload,
                        figure_key="payloads",
                        source_cols=["payloads"],
                        access_type="VA",
                        download_label_base="payloads",
                        figure_title="Payloads",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'auth' in va_stats:
                    auth_data = pd.DataFrame(list(va_stats['auth'].items()), columns=['Method', 'Count']).sort_values('Count', ascending=False)
                    fig_auth = create_professional_pie_chart(auth_data, 'Method', 'Count',
                                                            'Authentication Methods')
                    render_in_year_tabs(
                        fig_auth,
                        figure_key="authentication",
                        source_cols=["auth_method"],
                        access_type="VA",
                        download_label_base="authentication",
                        figure_title="Authentication",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'converter' in va_stats:
                    conv_data = pd.DataFrame(list(va_stats['converter'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_conv = create_professional_donut_chart(conv_data, 'Status', 'Count',
                                                              'Converter Plugin Availability',
                                                              color_map=color_map)
                    render_in_year_tabs(
                        fig_conv,
                        figure_key="converter",
                        source_cols=["converter_plugin"],
                        access_type="VA",
                        download_label_base="converter",
                        figure_title="Converter",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Virtual Access data available")
    
    else:
        # ENHANCED TA ANALYTICS with 10+ charts
        if ta_df is not None and not ta_df.empty:
            st.markdown("## 📊 Comprehensive Transnational Access Analytics")
            st.markdown("---")
            
            # Row 1
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'pi_gender' in ta_df.columns:
                    gender_counts = ta_df['pi_gender'].value_counts().to_dict()
                    gender_data = pd.DataFrame(list(gender_counts.items()), columns=['Gender', 'Count'])
                    color_map = {'Female': '#E74C3C', 'Male': '#3498DB', 'Other': '#95A5A6'}
                    fig_gender = create_professional_pie_chart(gender_data, 'Gender', 'Count',
                                                              'Principal Investigator Gender Distribution',
                                                              color_map=color_map)
                    render_in_year_tabs(
                        fig_gender,
                        figure_key="ta_gender_distribution",
                        source_cols=["pi_gender"],
                        access_type="TA",
                        download_label_base="ta_gender_distribution",
                        figure_title="Gender Distribution",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'ta_host' in ta_df.columns:
                    host_counts = ta_df['ta_host'].value_counts().head(10).to_dict()
                    host_data = pd.DataFrame(list(host_counts.items()), columns=['Host', 'Count']).sort_values('Count', ascending=True)
                    fig_host = create_professional_bar_chart(host_data, 'Count', 'Host',
                                                            'Top 10 TA Host Distribution',
                                                            orientation='h',
                                                            color_palette=COLORS['green_palette'])
                    render_in_year_tabs(
                        fig_host,
                        figure_key="ta_host_distribution",
                        source_cols=["ta_host"],
                        access_type="TA",
                        download_label_base="ta_host_distribution",
                        figure_title="Host Distribution",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 2
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'unit_of_access' in ta_df.columns:
                    unit_counts = ta_df['unit_of_access'].value_counts().to_dict()
                    unit_data = pd.DataFrame(list(unit_counts.items()), columns=['Unit', 'Count'])
                    fig_unit = create_professional_pie_chart(unit_data, 'Unit', 'Count',
                                                            'Access Unit Types')
                    render_in_year_tabs(
                        fig_unit,
                        figure_key="ta_access_units",
                        source_cols=["unit_of_access"],
                        access_type="TA",
                        download_label_base="ta_access_units",
                        figure_title="Access Units",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'number_of_users' in ta_df.columns:
                    user_counts = ta_df['number_of_users'].value_counts().head(8).to_dict()
                    user_data = pd.DataFrame(list(user_counts.items()), columns=['Users', 'Count']).sort_values('Users')
                    fig_users = create_professional_bar_chart(user_data, 'Users', 'Count',
                                                             'Number of Users Distribution',
                                                             orientation='v',
                                                             color_palette=['#8E44AD'] * len(user_data))
                    render_in_year_tabs(
                        fig_users,
                        figure_key="ta_number_of_users",
                        source_cols=["number_of_users"],
                        access_type="TA",
                        download_label_base="ta_number_of_users",
                        figure_title="Number Of Users",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 3: Call-Based Analysis
            st.markdown("### 📊 Call-Based Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'call' in ta_df.columns and 'pi_gender' in ta_df.columns:
                    call_gender = ta_df.groupby(['call', 'pi_gender']).size().reset_index(name='count')
                    fig_call_gender = px.bar(
                        call_gender,
                        x='call',
                        y='count',
                        color='pi_gender',
                        title='Gender Distribution by Call',
                        labels={'count': 'Number of Applications', 'call': 'Call', 'pi_gender': 'Gender'},
                        color_discrete_map={'Female': '#E74C3C', 'Male': '#3498DB', 'Other': '#95A5A6'},
                        height=400
                    )
                    fig_call_gender.update_layout(
                        font=dict(family=FONT_FAMILY, size=12),
                        title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                        margin=dict(l=60, r=60, t=60, b=100)
                    )
                    render_in_year_tabs(
                        fig_call_gender,
                        figure_key="ta_call_gender",
                        source_cols=["call", "pi_gender"],
                        access_type="TA",
                        download_label_base="ta_call_gender",
                        figure_title="Call Gender",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'call' in ta_df.columns and 'ta_host' in ta_df.columns:
                    top_hosts = ta_df['ta_host'].value_counts().head(5).index
                    call_host_filtered = ta_df[ta_df['ta_host'].isin(top_hosts)]
                    call_host = call_host_filtered.groupby(['call', 'ta_host']).size().reset_index(name='count')
                    
                    fig_call_host = px.bar(
                        call_host,
                        x='call',
                        y='count',
                        color='ta_host',
                        title='Top 5 Hosts - Applications by Call',
                        labels={'count': 'Number of Applications', 'call': 'Call', 'ta_host': 'TA Host'},
                        height=400
                    )
                    fig_call_host.update_layout(
                        font=dict(family=FONT_FAMILY, size=12),
                        title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(size=10)),
                        margin=dict(l=60, r=60, t=60, b=120)
                    )
                    render_in_year_tabs(
                        fig_call_host,
                        figure_key="ta_call_host",
                        source_cols=["call", "ta_host"],
                        access_type="TA",
                        download_label_base="ta_call_host",
                        figure_title="Call Host",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 4: Temporal Analysis
            st.markdown("### 📊 Temporal Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'visit_start' in ta_df.columns:
                    ta_temporal = ta_df[ta_df['visit_start'].notna()].copy()
                    if not ta_temporal.empty:
                        ta_temporal['visit_start_date'] = pd.to_datetime(ta_temporal['visit_start'], errors='coerce')
                        ta_temporal['month_year'] = ta_temporal['visit_start_date'].dt.to_period('M').astype(str)
                        
                        monthly_counts = ta_temporal['month_year'].value_counts().sort_index().head(12)
                        monthly_data = pd.DataFrame({
                            'Month': monthly_counts.index,
                            'Applications': monthly_counts.values
                        })
                        
                        fig_monthly = go.Figure()
                        fig_monthly.add_trace(go.Scatter(
                            x=monthly_data['Month'][-12:], # last year
                            y=monthly_data['Applications'],
                            mode='lines+markers',
                            line=dict(color=COLORS['accent'], width=3),
                            marker=dict(size=10, color=COLORS['accent']),
                            fill='tozeroy',
                            fillcolor='rgba(52, 152, 219, 0.2)'
                        ))
                        
                        fig_monthly.update_layout(
                            title='Visit Start Dates - Monthly Distribution',
                            xaxis_title='<b>Month</b>',
                            yaxis_title='<b>Number of Applications</b>',
                            font=dict(family=FONT_FAMILY, size=12),
                            title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                            height=400,
                            margin=dict(l=60, r=60, t=60, b=80),
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        
                        render_in_year_tabs(
                            fig_monthly,
                            figure_key="ta_monthly_distribution",
                            source_cols=["visit_start"],
                            access_type="TA",
                            download_label_base="ta_monthly_distribution",
                            figure_title="Monthly Distribution",
                        )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'units_requested' in ta_df.columns and 'units_used' in ta_df.columns:
                    units_comparison = ta_df[ta_df['units_requested'].notna() & ta_df['units_used'].notna()].copy()
                    if not units_comparison.empty:
                        units_comparison['units_requested'] = pd.to_numeric(units_comparison['units_requested'], errors='coerce')
                        units_comparison['units_used'] = pd.to_numeric(units_comparison['units_used'], errors='coerce')
                        units_comparison = units_comparison.dropna(subset=['units_requested', 'units_used'])
                        
                        if not units_comparison.empty:
                            fig_units = go.Figure()
                            fig_units.add_trace(go.Bar(
                                name='Requested',
                                x=units_comparison.index[:15],
                                y=units_comparison['units_requested'][:15],
                                marker_color=COLORS['warning']
                            ))
                            fig_units.add_trace(go.Bar(
                                name='Used',
                                x=units_comparison.index[:15],
                                y=units_comparison['units_used'][:15],
                                marker_color=COLORS['implemented']
                            ))
                            
                            fig_units.update_layout(
                                title='Units Requested vs Used (Sample)',
                                xaxis_title='<b>Application</b>',
                                yaxis_title='<b>Number of Units</b>',
                                barmode='group',
                                font=dict(family=FONT_FAMILY, size=12),
                                title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                                height=400,
                                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                                margin=dict(l=60, r=60, t=60, b=80)
                            )
                            
                            render_in_year_tabs(
                                fig_units,
                                figure_key="ta_units_comparison",
                                source_cols=["units_requested", "units_used"],
                                access_type="TA",
                                download_label_base="ta_units_comparison",
                                figure_title="Units Comparison",
                            )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 5: Geographic/Institutional
            st.markdown("### 🌎 Geographic and Institutional Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'pi_affiliation' in ta_df.columns:
                    affil_counts = ta_df['pi_affiliation'].value_counts().head(10)
                    affil_data = pd.DataFrame({
                        'Institution': affil_counts.index,
                        'Applications': affil_counts.values
                    }).sort_values('Applications', ascending=True)
                    
                    fig_affil = create_professional_bar_chart(
                        affil_data, 'Applications', 'Institution',
                        'Top 10 PI Institutions',
                        orientation='h',
                        color_palette=['#F39C12'] * len(affil_data)
                    )
                    render_in_year_tabs(
                        fig_affil,
                        figure_key="ta_top_institutions",
                        source_cols=["pi_affiliation"],
                        access_type="TA",
                        download_label_base="ta_top_institutions",
                        figure_title="Top Institutions",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'associated_wp' in ta_df.columns:
                    wp_counts = ta_df['associated_wp'].value_counts().to_dict()
                    wp_data = pd.DataFrame(list(wp_counts.items()), columns=['Work Package', 'Count'])
                    fig_wp = create_professional_pie_chart(wp_data, 'Work Package', 'Count',
                                                           'Associated Work Packages')
                    render_in_year_tabs(
                        fig_wp,
                        figure_key="ta_work_packages",
                        source_cols=["associated_wp"],
                        access_type="TA",
                        download_label_base="ta_work_packages",
                        figure_title="Work Packages",
                    )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Transnational Access data available")

elif selected == "KPI":
    st.title("🎯 Key Performance Indicators (KPI)")
    st.markdown("---")
    
    if project_label == "Virtual Access":
        # ==================== VIRTUAL ACCESS KPI - FULL IMPLEMENTATION ====================
        st.header("### 📊 Virtual Access KPIs")
        
        # Load raw data to access KPI columns by index. The KPI section talks
        # directly to Google Sheets so it can read raw cell values by column
        # position (avoids the renamings that load_google_sheets_data applies).
        try:
            scope = ["https://spreadsheets.google.com/feeds",
                     "https://www.googleapis.com/auth/drive"]

            # Same dual-path auth as the main loader: try Streamlit Cloud
            # secrets first, fall back silently to the local JSON. Touching
            # `st.secrets` when no secrets.toml exists raises, so we wrap the
            # lookup in its own try/except to keep the page clean.
            try:
                secrets_has_gcp = ("gcp_service_account" in st.secrets)
            except Exception:
                secrets_has_gcp = False

            if secrets_has_gcp:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            else:
                json_keyfile_path = GOOGLE_CREDS_FILE
                if not os.path.exists(json_keyfile_path):
                    # Fail quietly — the KPI section can't render without a
                    # live Google Sheets connection, but we surface a single
                    # informational message instead of multiple red errors.
                    st.info(
                        "ℹ️ KPI charts require a live Google Sheets connection. "
                        "Add `valiant-splicer-409609-e34abed30cc1.json` locally, "
                        "or configure `gcp_service_account` in Streamlit Cloud "
                        "secrets, to see this page."
                    )
                    raise Exception("Credentials missing")
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)

            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)
            worksheet_va = spreadsheet.worksheet("ILM_Connector")
            data_va = worksheet_va.get_all_values()
            df_raw = pd.DataFrame(data_va[4:], columns=data_va[3])
            
                        # ==================== IMPROVED KPI CODE ====================

            # ==================== KPI 1: USAGE LOGGING SYSTEM (UPDATED) ====================
            # Column 35 (AJ): Does your installation have Usage Logging system in place?
            # Values: YES, NO, Partially, In progress
            col_35 = df_raw.iloc[:, 35]  # Usage Logging

            st.subheader("KPI-1: Usage Logging System")
            st.caption("Tracks installations with active usage logging capabilities")

            # Calculate usage logging statistics (handles all 4 categories)
            usage_logging_counts = col_35.value_counts()

            # Normalize different case variations
            yes_count = (
                usage_logging_counts.get('YES', 0) + 
                usage_logging_counts.get('yes', 0) + 
                usage_logging_counts.get('Yes', 0)
            )
            no_count = (
                usage_logging_counts.get('NO', 0) + 
                usage_logging_counts.get('no', 0) + 
                usage_logging_counts.get('No', 0)
            )
            partially_count = (
                usage_logging_counts.get('Partially', 0) + 
                usage_logging_counts.get('partially', 0) + 
                usage_logging_counts.get('PARTIALLY', 0)
            )
            in_progress_count = (
                usage_logging_counts.get('In progress', 0) + 
                usage_logging_counts.get('in progress', 0) + 
                usage_logging_counts.get('IN PROGRESS', 0)
            )

            col1, col2 = st.columns(2)

            with col1:
                # Display metrics
                total_installations = len(col_35.dropna())
    
                st.metric("Total Installations", total_installations)
    
                # Show all 4 categories
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("✅ Fully Implemented", yes_count, 
                             delta=f"{yes_count/total_installations*100:.1f}%" if total_installations > 0 else "N/A")
                    st.metric("🟡 Partially", partially_count,
                             delta=f"{partially_count/total_installations*100:.1f}%" if total_installations > 0 else "N/A")
                with col_b:
                    st.metric("🔄 In Progress", in_progress_count,
                             delta=f"{in_progress_count/total_installations*100:.1f}%" if total_installations > 0 else "N/A")
                    st.metric("❌ Not Implemented", no_count,
                             delta=f"{no_count/total_installations*100:.1f}%" if total_installations > 0 else "N/A")

            with col2:
                # Create enhanced pie chart with 4 categories
                labels = ['Fully Implemented', 'In Progress', 'Partially', 'Not Implemented']
                values = [yes_count, in_progress_count, partially_count, no_count]
                colors = [COLORS['success'], COLORS['info'], COLORS['warning'], COLORS['danger']]
    
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors),
                    textfont=dict(size=14, family=FONT_FAMILY),
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )])
    
                fig.update_layout(
                    title=dict(
                        text="<b>Usage Logging System Distribution</b>",
                        font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                    ),
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    font=dict(family=FONT_FAMILY)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(
                    '<p style="font-size: 0.7rem; font-style: italic; color: #999; margin: 0.1rem 0 0.5rem 0;">'
                    'Source column: Column AJ – Does your installation have Usage Logging system in place?</p>',
                    unsafe_allow_html=True
                )

            # Summary text
            implementation_rate = ((yes_count + partially_count) / total_installations * 100) if total_installations > 0 else 0
            st.caption(f"📊 **Implementation Rate:** {implementation_rate:.1f}% of installations have usage logging (fully or partially implemented)")

            st.markdown("---")

            # ==================== KPI 2: ACCESSIBLE DATASETS ====================
            # Column 37: Total data items/records
            # Column 39 (AN): Datasets at start or current datasets
            # Column 40 (AO): New datasets or volume
            st.subheader("📚 KPI-2: Accessible Datasets")
            st.caption("Tracks the number of datasets and data records available through installations")

            col_37 = df_raw.iloc[:, 37]  # Total data items/records
            col_39 = df_raw.iloc[:, 39]  # Datasets (seems to be at start or total)
            col_40 = df_raw.iloc[:, 40]  # New datasets or additional info

            # Convert to numeric
            data_items = pd.to_numeric(col_37, errors='coerce').dropna()
            datasets_col_39 = pd.to_numeric(col_39, errors='coerce').dropna()
            datasets_col_40 = pd.to_numeric(col_40, errors='coerce').dropna()

            col1, col2 = st.columns(2)

            with col1:
                # Display dataset metrics
                st.markdown("**Dataset Statistics:**")
    
                if len(data_items) > 0:
                    st.metric("🗂️ Total Data Items/Records", f"{int(data_items.sum()):,}",
                             help="Total number of individual data records across all installations")
                    st.metric("📊 Average per Installation", f"{data_items.mean():.0f}",
                             help="Average data items per installation")
    
                if len(datasets_col_39) > 0:
                    st.metric("📚 Total Datasets Available", f"{int(datasets_col_39.sum()):,}",
                             help="Total number of distinct datasets")
                    st.metric("📈 Average Datasets/Installation", f"{datasets_col_39.mean():.1f}")

            with col2:
                # Create bar chart comparing installations
                if len(data_items) > 0:
                    # Top 10 installations by data items
                    top_installations = data_items.nlargest(10)
        
                    fig = go.Figure(data=[go.Bar(
                        x=[f"Installation {i+1}" for i in range(len(top_installations))],
                        y=top_installations.values,
                        marker=dict(color=COLORS['accent'], line=dict(color='white', width=1)),
                        text=[f"{int(v):,}" for v in top_installations.values],
                        textposition='outside',
                        textfont=dict(size=10, family=FONT_FAMILY)
                    )])
        
                    fig.update_layout(
                        title=dict(
                            text="<b>Top 10 Installations by Data Items</b>",
                            font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                        ),
                        xaxis_title="<b>Installation</b>",
                        yaxis_title="<b>Number of Data Items</b>",
                        height=400,
                        showlegend=False,
                        font=dict(family=FONT_FAMILY),
                        yaxis=dict(type='log')  # Log scale for better visualization
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(
                        '<p style="font-size: 0.7rem; font-style: italic; color: #999; margin: 0.1rem 0 0.5rem 0;">'
                        'Source columns: Col AL – Total data items/records | Col AN – Datasets</p>',
                        unsafe_allow_html=True
                    )

            # Additional visualization: Distribution of datasets
            if len(datasets_col_39) > 0:
                st.markdown("---")
                st.markdown("**Dataset Distribution Analysis:**")
    
                col1, col2 = st.columns(2)
    
                with col1:
                    # Histogram of dataset counts
                    fig = go.Figure(data=[go.Histogram(
                        x=datasets_col_39,
                        nbinsx=20,
                        marker=dict(color=COLORS['blue_palette'][2], line=dict(color='white', width=1)),
                        name='Installations'
                    )])
        
                    fig.update_layout(
                        title=dict(
                            text="<b>Distribution of Dataset Counts</b>",
                            font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                        ),
                        xaxis_title="<b>Number of Datasets</b>",
                        yaxis_title="<b>Number of Installations</b>",
                        height=350,
                        showlegend=False,
                        font=dict(family=FONT_FAMILY)
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
                with col2:
                    # Box plot showing dataset distribution
                    fig = go.Figure(data=[go.Box(
                        y=datasets_col_39,
                        marker=dict(color=COLORS['success']),
                        name='Dataset Count',
                        boxmean='sd'  # Show mean and standard deviation
                    )])
        
                    fig.update_layout(
                        title=dict(
                            text="<b>Dataset Count Statistics</b>",
                            font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                        ),
                        yaxis_title="<b>Number of Datasets</b>",
                        height=350,
                        showlegend=False,
                        font=dict(family=FONT_FAMILY)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Summary metrics table
            st.markdown("---")
            st.subheader("📊 KPI Summary Table")

            kpi_summary = pd.DataFrame({
                'KPI Metric': [
                    'Usage Logging - Fully Implemented',
                    'Usage Logging - In Progress',
                    'Usage Logging - Partially',
                    'Usage Logging - Not Implemented',
                    'Total Data Items/Records',
                    'Total Datasets Available',
                    'Installations with Data',
                    'Average Datasets per Installation'
                ],
                'Value': [
                    f"{yes_count} ({yes_count/total_installations*100:.1f}%)" if total_installations > 0 else "N/A",
                    f"{in_progress_count} ({in_progress_count/total_installations*100:.1f}%)" if total_installations > 0 else "N/A",
                    f"{partially_count} ({partially_count/total_installations*100:.1f}%)" if total_installations > 0 else "N/A",
                    f"{no_count} ({no_count/total_installations*100:.1f}%)" if total_installations > 0 else "N/A",
                    f"{int(data_items.sum()):,}" if len(data_items) > 0 else "N/A",
                    f"{int(datasets_col_39.sum()):,}" if len(datasets_col_39) > 0 else "N/A",
                    f"{len(data_items)}" if len(data_items) > 0 else "N/A",
                    f"{datasets_col_39.mean():.1f}" if len(datasets_col_39) > 0 else "N/A"
                ]
            })

            st.dataframe(kpi_summary, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error loading KPI data: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    else:  # Transnational Access
        # ==================== TRANSNATIONAL ACCESS KPI - UNDER DEVELOPMENT ====================
        st.info("🚧 This section is currently under development. KPI metrics and visualizations will be available soon.")
        
        # Show preview of coming features
        st.subheader("📊 Coming Soon:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #3498DB;">
                <h4>Project Metrics</h4>
                <ul>
                    <li>Project Completion Rates</li>
                    <li>Visit/Access Statistics</li>
                    <li>Host Distribution</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #27AE60;">
                <h4>User Metrics</h4>
                <ul>
                    <li>Total Users by Call</li>
                    <li>Gender Distribution</li>
                    <li>Affiliation Analysis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #F39C12;">
                <h4>Outcomes</h4>
                <ul>
                    <li>Expected vs Delivered Assets</li>
                    <li>Integration Strategies</li>
                    <li>Quality Indicators</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("Check back soon for detailed KPI analytics and visualizations for Transnational Access!")



# ===============================================================================================
# =================================== DATA SECTION ============================================
# ===============================================================================================
# The Data tab displays the RAW source data for both Virtual Access and Transnational
# Access using the EXACT same column-header structure as the source Excel file:
# rows 1–4 of the spreadsheet form a 4-row hierarchical header (group band → topic
# → criteria → column name).  We build a `pandas.MultiIndex` from these four rows
# via the `build_four_row_header()` helper defined near the top of this file and
# attach it to the raw frame (`va_raw` / `ta_raw`).  Users can also download the
# data as a CSV with the original column names.
# ===============================================================================================

elif selected == "Data":
    # Breadcrumb-style header line
    st.markdown("<span class='small'>Home → Data</span>", unsafe_allow_html=True)
    st.header("Data Table")

    # ── A short note explaining the 4-row header to anyone unfamiliar with the
    #    Excel layout — keeps the table self-documenting. ────────────────────
    st.caption(
        "The header below mirrors the first four rows of the source spreadsheet: "
        "**Group band → Topic → Criteria → Column name**, exactly as in the "
        "Excel file `GeoINQUIRE-ImplementationLevelMatrix.xlsx`."
    )

    # ---------------------------------------------------------------------------
    # VIRTUAL ACCESS BRANCH
    # ---------------------------------------------------------------------------
    if project_label == "Virtual Access":
        if va_raw is not None and not va_raw.empty:
            # 1) Work on a copy so the source frame stays untouched between reruns.
            va_display = va_raw.copy()

            # 2) De-duplicate column names that may repeat in row 4 of the sheet
            #    (e.g. several "[0;1]" cells). Streamlit's dataframe rendering
            #    rejects an Index with duplicates, so we suffix the duplicates
            #    with _1, _2, ... while leaving the first occurrence intact.
            cols = pd.Series(va_display.columns.astype(str))
            for dup in cols[cols.duplicated()].unique():
                dup_indices = [i for i, x in enumerate(cols) if x == dup]
                for i, idx in enumerate(dup_indices[1:], start=1):
                    cols[idx] = f"{dup}_{i}"
            va_display.columns = cols

            # 3) Build the 4-row MultiIndex from rows 1–4 (`va_header4` was set
            #    inside `load_google_sheets_data` / `load_excel_data`).  The
            #    helper forward-fills the merged group bands so they span the
            #    correct columns, and it gracefully handles the case where
            #    the header rows are shorter than the data.
            if va_header4 is not None and len(va_header4) == 4:
                try:
                    multi_idx = build_four_row_header(va_header4, len(va_display.columns))
                    va_display.columns = multi_idx
                except Exception as exc:
                    # Fall back silently to the flat header if anything goes
                    # wrong — the user still sees the data with single names.
                    st.caption(f"(Could not build multi-row header: {exc})")

            # 4) Render the dataframe and offer a CSV download.
            st.caption(f"**Virtual Access Data** — {len(va_display):,} records")
            st.dataframe(va_display, use_container_width=True)

            # CSV download keeps the row-4 column names (last level of the
            # MultiIndex), which is what users normally want in a spreadsheet.
            st.download_button(
                "📥 Download VA CSV (original column names)",
                data=va_raw.to_csv(index=False).encode("utf-8"),
                file_name="VA_data.csv",
                mime="text/csv",
                key="va_csv_download",
            )
        else:
            st.warning("No Virtual Access data available")

    # ---------------------------------------------------------------------------
    # TRANSNATIONAL ACCESS BRANCH
    # ---------------------------------------------------------------------------
    else:
        if ta_raw is not None and not ta_raw.empty:
            # Same pattern as the VA branch but on the TA sheet.
            ta_display = ta_raw.copy()

            # De-duplicate columns
            cols = pd.Series(ta_display.columns.astype(str))
            for dup in cols[cols.duplicated()].unique():
                dup_indices = [i for i, x in enumerate(cols) if x == dup]
                for i, idx in enumerate(dup_indices[1:], start=1):
                    cols[idx] = f"{dup}_{i}"
            ta_display.columns = cols

            # Build the multi-row header for TA
            if ta_header4 is not None and len(ta_header4) == 4:
                try:
                    multi_idx = build_four_row_header(ta_header4, len(ta_display.columns))
                    ta_display.columns = multi_idx
                except Exception as exc:
                    st.caption(f"(Could not build multi-row header: {exc})")

            st.caption(f"**Transnational Access Data** — {len(ta_display):,} records")
            st.dataframe(ta_display, use_container_width=True)

            st.download_button(
                "📥 Download TA CSV (original column names)",
                data=ta_raw.to_csv(index=False).encode("utf-8"),
                file_name="TA_data.csv",
                mime="text/csv",
                key="ta_csv_download",
            )
        else:
            st.warning("No Transnational Access data available")


elif selected == "Contact":
    st.markdown("<span class='small'>Home → Contact</span>", unsafe_allow_html=True)
    st.header("Contact")
    st.write("• Conceptor: Jan Michalek and Juliano Ramanantsoa")
    st.write("• Reach out: heriniaina.j.ramanantsoa@uib.no")




    