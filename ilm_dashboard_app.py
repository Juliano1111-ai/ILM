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

# --- Historical snapshots for the year tabs ------------------------------------
# Three frozen point-in-time exports of the ILM workbook, one per project year.
# Each file is treated as a read-only snapshot; the dashboard reads them only to
# populate the 2023 / 2024 / 2025 tabs of each VA figure.
HISTORICAL_VA_FILES = {
    "2023": "ILM_Old/GeoINQUIRE-ImplementationLevelMatrix - 21 December 2023, 11_05.xlsx",
    "2024": "ILM_Old/GeoINQUIRE-ImplementationLevelMatrix - 5 November 2024, 11_39.xlsx",
    "2025": "ILM_Old/GeoINQUIRE-ImplementationLevelMatrix - 12 November 2025, 10_47.xlsx",
}

# Sheet names to try when loading a historical VA workbook (in order).
HISTORICAL_VA_SHEET_CANDIDATES = (
    "ILM_VA",                          # 2023 (Dec) & 2025 exports
    "ILM-VA",                          # 2024 export (note the hyphen)
    "Implementation_Level_Matrix_VA",  # older 2025 export
    "Implementation_Level_Matrix",     # older 2023/2024 exports
)

# Year tab order: the LIVE 2026 data shows FIRST (Streamlit opens on the first
# tab), then the historical snapshots most-recent-first.
YEAR_TAB_KEYS   = ("2026", "2025", "2024", "2023")
YEAR_TAB_LABELS = ("2026  ·  Live", "2025", "2024", "2023")

# Which tab key holds the live, interactive data (used for the download button
# and the VA_DATA_BY_YEAR mapping).  Keep this in sync if the live year changes.
LIVE_YEAR_KEY = "2026"

# --- Call tabs (Transnational Access) ------------------------------------------
# Per spec, TA charts group projects by funding Call (1–4); each Call is
# identified by the project_id prefix ("TA1-…", "TA2-…", ...).
CALL_TAB_KEYS   = ("Call 1", "Call 2", "Call 3", "Call 4")
CALL_TAB_LABELS = ("Call 1", "Call 2", "Call 3", "Call 4")
CALL_PREFIXES   = {"Call 1": "TA1", "Call 2": "TA2", "Call 3": "TA3", "Call 4": "TA4"}

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

        # EU funding acknowledgement (compact card) on the welcome / password page.
        render_eu_acknowledgement(variant="login")
        
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
# Restrained, editorial palette. Names below are reused throughout the dashboard.
COLORS = {
    'primary'   : '#1f3a5f',
    'secondary' : '#3b5b7e',
    'accent'    : '#2563eb',
    'success'   : '#0e9f6e',
    'warning'   : '#d97706',
    'danger'    : '#dc2626',
    'info'      : '#0891b2',
    'light'     : '#f1f5f9',
    'dark'      : '#0f172a',

    # Continuous palettes for ordered categorical charts.
    'blue_palette'  : ['#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'],
    'green_palette' : ['#065f46', '#0e9f6e', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0'],
    # Multi-hue palette — high contrast & color-blind friendly (Okabe–Ito).
    'multi_palette' : ['#2563eb', '#dc2626', '#d97706', '#7c3aed',
                       '#0891b2', '#0e9f6e', '#475569', '#db2777'],

    'implemented'        : '#0e9f6e',
    'partly_implemented' : '#2563eb',
    'planned'            : '#d97706',
    'not_implemented'    : '#dc2626',
    'unknown'            : '#94a3b8',
    'yes' : '#0e9f6e',
    'no'  : '#dc2626',
    'exhausted'  : '#0e9f6e',
    'fixed'      : '#2563eb',
    'ready'      : '#0891b2',
    'contacted'  : '#d97706',
    'negotiated' : '#7c3aed',
}

# Modern system-font stack — looks elegant on any OS.
FONT_FAMILY      = ("Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
                    "Roboto, 'Helvetica Neue', Arial, sans-serif")
TITLE_FONT_SIZE  = 17
LABEL_FONT_SIZE  = 13
TICK_FONT_SIZE   = 12

# Backwards-compatibility shim for older code paths that still reference YEAR_TABS.
YEAR_TABS = YEAR_TAB_KEYS


# ===============================================================================================
# EU FUNDING ACKNOWLEDGEMENT — official emblem + mandated sentence
# ===============================================================================================
# Horizon Europe grants require visible acknowledgement of EU funding using the
# emblem and the standard sentence.  The flag below is an inline SVG (12 gold
# stars on blue) so it renders without any external image dependency.
EU_FLAG_SVG = '''<svg viewBox="0 0 810 540" xmlns="http://www.w3.org/2000/svg" style="height:46px;width:auto;border-radius:3px;display:block;"><rect width="810" height="540" fill="#003399"/><path d="M405.0,54.0 L396.9,78.9 L370.8,78.9 L391.9,94.2 L383.8,119.1 L405.0,103.8 L426.2,119.1 L418.1,94.2 L439.2,78.9 L413.1,78.9 Z" fill="#FFCC00"/><path d="M495.0,78.1 L486.9,103.0 L460.8,103.0 L481.9,118.4 L473.8,143.2 L495.0,127.9 L516.2,143.2 L508.1,118.4 L529.2,103.0 L503.1,103.0 Z" fill="#FFCC00"/><path d="M560.9,144.0 L552.8,168.9 L526.6,168.9 L547.8,184.2 L539.7,209.1 L560.9,193.8 L582.0,209.1 L574.0,184.2 L595.1,168.9 L569.0,168.9 Z" fill="#FFCC00"/><path d="M585.0,234.0 L576.9,258.9 L550.8,258.9 L571.9,274.2 L563.8,299.1 L585.0,283.8 L606.2,299.1 L598.1,274.2 L619.2,258.9 L593.1,258.9 Z" fill="#FFCC00"/><path d="M560.9,324.0 L552.8,348.9 L526.6,348.9 L547.8,364.2 L539.7,389.1 L560.9,373.8 L582.0,389.1 L574.0,364.2 L595.1,348.9 L569.0,348.9 Z" fill="#FFCC00"/><path d="M495.0,389.9 L486.9,414.8 L460.8,414.8 L481.9,430.1 L473.8,455.0 L495.0,439.6 L516.2,455.0 L508.1,430.1 L529.2,414.8 L503.1,414.8 Z" fill="#FFCC00"/><path d="M405.0,414.0 L396.9,438.9 L370.8,438.9 L391.9,454.2 L383.8,479.1 L405.0,463.8 L426.2,479.1 L418.1,454.2 L439.2,438.9 L413.1,438.9 Z" fill="#FFCC00"/><path d="M315.0,389.9 L306.9,414.8 L280.8,414.8 L301.9,430.1 L293.8,455.0 L315.0,439.6 L336.2,455.0 L328.1,430.1 L349.2,414.8 L323.1,414.8 Z" fill="#FFCC00"/><path d="M249.1,324.0 L241.0,348.9 L214.9,348.9 L236.0,364.2 L228.0,389.1 L249.1,373.8 L270.3,389.1 L262.2,364.2 L283.4,348.9 L257.2,348.9 Z" fill="#FFCC00"/><path d="M225.0,234.0 L216.9,258.9 L190.8,258.9 L211.9,274.2 L203.8,299.1 L225.0,283.8 L246.2,299.1 L238.1,274.2 L259.2,258.9 L233.1,258.9 Z" fill="#FFCC00"/><path d="M249.1,144.0 L241.0,168.9 L214.9,168.9 L236.0,184.2 L228.0,209.1 L249.1,193.8 L270.3,209.1 L262.2,184.2 L283.4,168.9 L257.2,168.9 Z" fill="#FFCC00"/><path d="M315.0,78.1 L306.9,103.0 L280.8,103.0 L301.9,118.4 L293.8,143.2 L315.0,127.9 L336.2,143.2 L328.1,118.4 L349.2,103.0 L323.1,103.0 Z" fill="#FFCC00"/></svg>'''

# The exact acknowledgement sentence Geo-INQUIRE asks partners to use.
GEOINQUIRE_ACK_SENTENCE = (
    "Geo-INQUIRE is funded by the European Commission under project number "
    "101058518 within the HORIZON-INFRA-2021-SERV-01 call."
)


def render_eu_acknowledgement(variant="footer"):
    """
    Render the EU funding acknowledgement.

    variant="footer"  -> full-width green banner used at the bottom of each page.
    variant="login"   -> compact light card used on the password / welcome page.
    """
    if variant == "login":
        st.markdown(
            '<div style="margin-top:1.5rem; padding:1rem 1.25rem; border-radius:12px;'
            ' background:#ffffff; border:1px solid #e2e8f0;'
            ' display:flex; align-items:center; gap:1rem;">'
            '<div style="flex:0 0 auto;">' + EU_FLAG_SVG + '</div>'
            '<div style="font-size:0.78rem; color:#475569; line-height:1.45;">'
            '<strong style="color:#1f3a5f;">Funded by the European Union</strong><br>'
            + GEOINQUIRE_ACK_SENTENCE +
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="margin-top:2.5rem; padding:1.5rem 1.75rem; border-radius:14px;'
            ' background:linear-gradient(135deg,#5a9367 0%,#6aa877 100%); color:#ffffff;">'
            '<div style="display:flex; align-items:center; gap:1.25rem; flex-wrap:wrap;">'
            '<div style="flex:0 0 auto;">' + EU_FLAG_SVG + '</div>'
            '<div style="flex:1 1 280px; min-width:240px;">'
            '<div style="font-size:1rem; font-weight:800; margin-bottom:0.35rem;">'
            'How to acknowledge Geo-INQUIRE</div>'
            '<div style="font-size:0.85rem; line-height:1.5; opacity:0.97;">'
            'Please acknowledge Geo-INQUIRE using this sentence:<br>'
            '<em>&ldquo;' + GEOINQUIRE_ACK_SENTENCE + '&rdquo;</em>'
            '</div></div></div></div>',
            unsafe_allow_html=True,
        )


# ===============================================================================================
# CUSTOM CSS STYLING
# ===============================================================================================
# Defines custom styles for KPI cards, metrics, and layout
# ===============================================================================================
st.markdown("""
<style>
/* ============================================================================
   FORCE LIGHT THEME — belt-and-braces with .streamlit/config.toml.
   Even if a viewer's browser / OS is in dark mode, these rules keep the
   dashboard on a clean white canvas with dark text.
   ============================================================================ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stSidebar"],
.main,
.block-container {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[data-testid="stSidebar"] {
    background-color: #f5f7fa !important;
    border-right: 1px solid #e2e8f0;
}

/* ── Typography: modern system-font stack ───────────────────────────────── */
html, body, .stApp, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}
.block-container { padding-top: 4.25rem !important; padding-bottom: 1rem; }
h1, h2, h3 {
    margin-bottom: .25rem;
    color: #1f3a5f !important;
    font-weight: 700;
    letter-spacing: -0.01em;
}
hr { margin: .75rem 0; border-color: #e2e8f0; }

/* ── KPI cards — refined navy gradient that matches the chart palette ───── */
.kpi {
    padding: 1.3rem 1.5rem;
    border-radius: 14px;
    background: linear-gradient(135deg, #1f3a5f 0%, #2563eb 100%);
    border: none;
    box-shadow: 0 6px 16px rgba(31,58,95,0.18);
    color: white;
}
.kpi h3 {
    font-size: 0.8rem;
    margin: 0 0 .5rem 0;
    color: rgba(255,255,255,0.85) !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
.kpi .val {
    font-size: 2.1rem;
    font-weight: 800;
    color: white !important;
    line-height: 1.1;
}
.small { font-size: 0.85rem; color: #64748b; }
[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 10px; }

/* ── Chart container card ───────────────────────────────────────────────── */
.chart-container {
    background: white;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(15,23,42,0.06);
    border: 1px solid #eef2f6;
    margin-bottom: 1.5rem;
}

/* ── Tabs — clean, understated, with a navy active underline ────────────── */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #64748b !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1f3a5f !important;
}
[data-baseweb="tab-highlight"] { background-color: #2563eb !important; }

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
        '<p style="font-size:1.25rem; font-weight:900; color:#1f3a5f; '
        'letter-spacing:1px; margin-bottom:0.5rem; text-transform:uppercase; '
        'border-bottom:3px solid #2563eb; padding-bottom:0.3rem;">Select Project</p>',
        unsafe_allow_html=True,
    )

    # Inject custom CSS to make the radio buttons large, bold & highly visible
    st.markdown("""
    <style>
    /* ===== PROMINENT PROJECT TOGGLE BUTTONS ===== */
    div[data-testid="stSidebar"] .stRadio > div {
        gap: 0.65rem !important;
    }
    div[data-testid="stSidebar"] .stRadio > div > label {
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        padding: 0.95rem 1.1rem !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 12px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        background: #ffffff !important;
        display: flex !important;
        align-items: center !important;
        color: #1f3a5f !important;
        letter-spacing: 0.2px !important;
        box-shadow: 0 1px 3px rgba(15,23,42,0.06) !important;
    }
    /* Hide the tiny default radio dot — the whole pill is the control */
    div[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
        display: none !important;
    }
    div[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: #eff6ff !important;
        border-color: #2563eb !important;
        transform: translateX(2px);
        box-shadow: 0 3px 8px rgba(37,99,235,0.15) !important;
    }
    div[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    div[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background: linear-gradient(135deg, #1f3a5f 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border-color: #1f3a5f !important;
        box-shadow: 0 6px 16px rgba(31,58,95,0.35) !important;
        transform: translateX(2px);
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
        '<p style="font-size:1.05rem; font-weight:800; color:#1f3a5f; '
        'letter-spacing:0.3px; margin-bottom:0.3rem;">About Geo-INQUIRE</p>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <div style="background:#ffffff; padding:1rem; border-radius:12px;
                border:1px solid #e2e8f0; border-left:4px solid #2563eb;
                font-size:0.82rem; color:#334155; line-height:1.55; margin-bottom:0.8rem;">
        <strong>Geosphere INfrastructures for QUestions into Integrated REsearch</strong><br><br>
        A <strong>Horizon Europe</strong> Research Infrastructures project providing and
        enhancing access to key geoscience data, products and services — enabling
        geosphere dynamics to be monitored and modelled at new levels of spatial and
        temporal detail across the land–sea–atmosphere environment.<br><br>
        <strong>Key facts</strong><br>
        &bull; <strong>Grant No:</strong> 101058518<br>
        &bull; <strong>Call:</strong> HORIZON-INFRA-2021-SERV-01<br>
        &bull; <strong>Duration:</strong> Oct 2022 – Sep 2026 (48 months)<br>
        &bull; <strong>EU contribution:</strong> €13.92 million<br>
        &bull; <strong>Partners:</strong> 51 organisations<br>
        &bull; <strong>Portfolio:</strong> 150+ Virtual &amp; Transnational Access facilities<br>
        &bull; <strong>Main RIs:</strong> EPOS, EMSO, ChEESE
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.75rem; color:#94a3b8; line-height:1.45;">
        <a href="https://www.geo-inquire.eu/" target="_blank"
           style="color:#2563eb; text-decoration:none; font-weight:600;">
           www.geo-inquire.eu</a><br>
        University of Bergen, Norway<br>
        © 2022–2026 Geo-INQUIRE Consortium
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


# ===============================================================================================
# HISTORICAL-DATA LOADER — one frozen snapshot per project year
# ===============================================================================================
def _apply_va_column_renames(df):
    """
    Normalise VA column names across all historical and current workbooks.
    Covers three vintages of the ILM matrix (2023 / 2024 / 2025+).
    """
    rename_map = {
        "TCS Name"                      : "contact_person",
        "Service Group Name"            : "affiliation",
        "Research infrastructure (RI)"  : "compliant_ri",
        "Contact person"                : "contact_person",
        "Email"                         : "email",
        "Affiliation"                   : "affiliation",
        "Service/Installation Name"     : "service_name",
        "Compliant with Research infrastructure (RI)": "compliant_ri",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    long_renames = {}
    for c in df.columns:
        s = str(c).lower()
        if "implementation status to ri" in s:
            long_renames[c] = "implementation_status"
        elif "data representations" in s:
            long_renames[c] = "data_repr"
        elif s.strip() == "license":
            long_renames[c] = "license"
        elif "standard of metadata describing the service" in s:
            long_renames[c] = "metadata_standard"
        elif "gender" in s and "pi" not in s:
            long_renames[c] = "gender"
    df = df.rename(columns=long_renames)
    return df


@st.cache_data(ttl=3600)
def load_historical_va_data():
    """
    Load the frozen historical VA snapshots for the 2023 / 2024 / 2025 tabs.

    Robust file discovery — instead of requiring an exact filename match (which
    broke when the snapshots were renamed / re-exported), this:
      1. Anchors to the folder the script lives in, so it works no matter what
         the current working directory is (local `streamlit run`, Streamlit
         Cloud, etc.).
      2. Globs every .xlsx in ILM_Old/ and matches a file to a year simply by
         looking for the 4-digit year in the filename.  "…21 December 2023…"
         matches 2023, "…5 November 2024…" matches 2024, and so on.
      3. Tries the known sheet-name candidates, then falls back to the first
         sheet in the workbook if none match.

    Returns {"2023": df|None, "2024": df|None, "2025": df|None} and stashes a
    short diagnostic in `st.session_state["_hist_diag"]` so the UI can explain
    exactly what was (or wasn't) found.
    """
    import glob

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ilm_old  = os.path.join(base_dir, "ILM_Old")

    out  = {"2023": None, "2024": None, "2025": None}
    diag = {"folder": ilm_old, "found_files": [], "matched": {}, "errors": {}}

    if not os.path.isdir(ilm_old):
        diag["errors"]["folder"] = "ILM_Old/ directory not found next to the app."
        st.session_state["_hist_diag"] = diag
        return out

    xlsx_files = sorted(glob.glob(os.path.join(ilm_old, "*.xlsx")))
    diag["found_files"] = [os.path.basename(f) for f in xlsx_files]

    for year in ("2023", "2024", "2025"):
        # Match by the year appearing anywhere in the filename.
        candidates = [f for f in xlsx_files if year in os.path.basename(f)]
        if not candidates:
            diag["matched"][year] = None
            continue
        path = candidates[0]                       # if several, take the first alphabetically
        diag["matched"][year] = os.path.basename(path)
        try:
            xl = pd.ExcelFile(path)
            sheet = next((s for s in HISTORICAL_VA_SHEET_CANDIDATES if s in xl.sheet_names), None)
            if sheet is None:
                sheet = xl.sheet_names[0]          # fall back to the first sheet
            df = pd.read_excel(path, sheet_name=sheet, header=3)
            df = _apply_va_column_renames(df)
            out[year] = df
        except Exception as exc:
            diag["errors"][year] = str(exc)
            out[year] = None

    st.session_state["_hist_diag"] = diag
    return out


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

# ===============================================================================================
# Compose the per-year data dict that drives every VA year tab.
# 2023 / 2024 / 2025 = frozen snapshots; 2026 = live current data.
# ===============================================================================================
_historical_va = load_historical_va_data()
VA_DATA_BY_YEAR = {
    "2023": _historical_va.get("2023"),
    "2024": _historical_va.get("2024"),
    "2025": _historical_va.get("2025"),
    "2026": va_df,            # 2026 tab = the live, interactive current data
}

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
    """
    Compute summary statistics for the Virtual Access dataframe.

    Every value_counts() result is fed through a small "drop the misleading 0
    and empty labels" cleaner so categorical pies / donuts don't end up with a
    cyan "0" slice when the source sheet has zeros, blanks or "nan" strings
    used as placeholders.
    """
    if df is None or df.empty:
        return {}

    # ── Helper: turn a Series into an ORDERED dict of label → count, ────────
    # ── dropping misleading "0" / empty / nan / "-" placeholders. ──────────
    def _clean_counts(series, head_n=None):
        cleaned = series.dropna().astype(str).str.strip()
        bogus = {"", "0", "0.0", "nan", "None", "n/a", "N/A", "-"}
        cleaned = cleaned[~cleaned.isin(bogus)]
        if cleaned.empty:
            return {}
        vc = cleaned.value_counts()
        if head_n is not None:
            vc = vc.head(head_n)
        return vc.to_dict()

    stats = {}

    if 'implementation_status' in df.columns:
        impl_counts = df['implementation_status'].apply(standardize_implementation_value)
        stats['implementation'] = _clean_counts(impl_counts)

    if 'service_running' in df.columns:
        running_counts = df['service_running'].apply(standardize_binary_value)
        stats['service_running'] = _clean_counts(running_counts)

    if 'parametrization' in df.columns:
        param_counts = df['parametrization'].apply(standardize_binary_value)
        stats['parametrization'] = _clean_counts(param_counts)

    if 'fully_described' in df.columns:
        desc_counts = df['fully_described'].apply(standardize_binary_value)
        stats['fully_described'] = _clean_counts(desc_counts)

    if 'documentation_status' in df.columns:
        doc_counts = df['documentation_status'].apply(standardize_implementation_value)
        stats['documentation'] = _clean_counts(doc_counts)

    if 'payloads' in df.columns:
        payload_counts = df['payloads'].apply(standardize_binary_value)
        stats['payloads'] = _clean_counts(payload_counts)

    if 'auth_method' in df.columns:
        # Auth method is free-text in the source sheet; keep the top 5 only.
        stats['auth'] = _clean_counts(df['auth_method'], head_n=5)

    if 'data_policy' in df.columns:
        stats['policy'] = _clean_counts(df['data_policy'])

    if 'converter_plugin' in df.columns:
        conv_counts = df['converter_plugin'].apply(standardize_binary_value)
        stats['converter'] = _clean_counts(conv_counts)

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
def render_in_year_tabs(fig_or_builder, figure_key, source_cols=None, access_type="VA",
                        download_label_base=None, figure_title="",
                        data_by_year=None):
    """
    Render a chart across four year tabs (2023 / 2024 / 2025 / 2026).

    `fig_or_builder` may be:
      * a pre-built Plotly/matplotlib figure  (shown identically in every tab)
      * a callable `(df, year_label) → Figure` (preferred — rebuilds per year)
    """
    if data_by_year is None:
        data_by_year = VA_DATA_BY_YEAR
    is_builder = callable(fig_or_builder) and not hasattr(fig_or_builder, "to_image")
    if not is_builder and fig_or_builder is None:
        st.info(f"⚠️ No data available for: {figure_title or figure_key}")
        return

    tabs = st.tabs(list(YEAR_TAB_LABELS))
    for tab, year_label in zip(tabs, YEAR_TAB_KEYS):
        with tab:
            year_df = data_by_year.get(year_label)
            if year_df is None or (hasattr(year_df, "empty") and year_df.empty):
                # Surface a precise diagnostic so it's obvious WHY a year is empty.
                diag = st.session_state.get("_hist_diag", {})
                found = diag.get("found_files", [])
                matched = diag.get("matched", {}).get(year_label)
                msg = f"No data available for **{year_label}**."
                if matched:
                    err = diag.get("errors", {}).get(year_label)
                    msg += f" Matched file `{matched}` but could not read it" + (f": {err}" if err else ".")
                elif found:
                    msg += (f" No file in `ILM_Old/` contains \"{year_label}\". "
                            f"Files present: {', '.join(found)}.")
                else:
                    msg += " The `ILM_Old/` folder is empty or missing next to the app."
                st.info(msg)
                continue
            try:
                fig = fig_or_builder(year_df, year_label) if is_builder else fig_or_builder
            except Exception as e:
                st.warning(f"Could not build chart for {year_label}: {e}")
                continue
            if fig is None:
                st.info(f"No data for **{figure_title or figure_key}** in {year_label}.")
                continue
            if isinstance(fig, plt.Figure):
                st.pyplot(fig, clear_figure=False, use_container_width=False)
            else:
                st.plotly_chart(fig, use_container_width=False,
                                key=f"{figure_key}_{year_label}")
            if source_cols:
                add_source_annotation(source_cols, access_type=access_type)
            if download_label_base and year_label == LIVE_YEAR_KEY:
                create_download_button(fig, f"{download_label_base}_{year_label}",
                                       col_keys=source_cols, access_type=access_type)


def render_in_call_tabs(fig_or_builder, figure_key, ta_dataframe,
                        source_cols=None,
                        download_label_base=None, figure_title=""):
    """
    Render a TA chart across four Call tabs (Call 1 → Call 4), filtered by the
    `call` column or the `project_id` prefix.
    """
    is_builder = callable(fig_or_builder) and not hasattr(fig_or_builder, "to_image")
    if not is_builder and fig_or_builder is None:
        st.info(f"⚠️ No data available for: {figure_title or figure_key}")
        return
    if ta_dataframe is None or ta_dataframe.empty:
        st.info("⚠️ No Transnational Access data loaded.")
        return

    tabs = st.tabs(list(CALL_TAB_LABELS))
    for tab, call_label in zip(tabs, CALL_TAB_KEYS):
        with tab:
            df_call = ta_dataframe
            if "call" in df_call.columns:
                num = call_label.split()[-1]
                df_call = df_call[df_call["call"].astype(str).str.strip() == num]
            elif "project_id" in df_call.columns:
                prefix = CALL_PREFIXES[call_label]
                df_call = df_call[df_call["project_id"].astype(str).str.startswith(prefix)]
            if df_call.empty:
                st.info(f"📂 No projects in **{call_label}** yet.")
                continue
            try:
                fig = fig_or_builder(df_call, call_label) if is_builder else fig_or_builder
            except Exception as e:
                st.warning(f"Could not build chart for {call_label}: {e}")
                continue
            if fig is None:
                st.info(f"No data for {figure_title or figure_key} in {call_label}.")
                continue
            if isinstance(fig, plt.Figure):
                st.pyplot(fig, clear_figure=False, use_container_width=False)
            else:
                st.plotly_chart(fig, use_container_width=False,
                                key=f"{figure_key}_{call_label.replace(' ', '_')}")
            if source_cols:
                add_source_annotation(source_cols, access_type="TA")
            if download_label_base and call_label == CALL_TAB_KEYS[-1]:
                create_download_button(fig,
                    f"{download_label_base}_{call_label.replace(' ', '_')}",
                    col_keys=source_cols, access_type="TA")


def value_counts_clean(series):
    """
    Like Series.value_counts() but strips NaN/None, empty strings, the literal
    strings "0"/"0.0"/"nan"/"-", and numeric zeros.  Returns a list of (label,
    count) tuples, largest first.
    """
    if series is None:
        return []
    s = series.dropna()
    stripped = s.astype(str).str.strip()
    bogus = {"", "0", "0.0", "nan", "None", "n/a", "N/A", "-"}
    cleaned = stripped[~stripped.isin(bogus)]
    if cleaned.empty:
        return []
    return list(cleaned.value_counts().items())


# ===============================================================================================
# TRANSNATIONAL ACCESS — domain-aware statistics helpers
# ===============================================================================================
# The TA sheet is full of free-text fields (access level, integration, outcomes,
# metadata), so meaningful charts need normalisation rather than a naive
# value_counts.  These helpers turn the messy text into clean, comparable
# categories and detect whether a project has actually EXPOSED a produced asset
# (a DOI or a URL) versus merely describing or planning one.
# ===============================================================================================
_TA_BOGUS = {"", "0", "0.0", "nan", "none", "n/a", "-", "tbd", "to be determined",
             "to be determined.", "please fill out this cell asap, if applicable"}


def ta_normalize_access_level(val):
    """Map the messy 'Level of access' free text onto clean categories."""
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in _TA_BOGUS or "to be determin" in s or "tbd" in s:
        return "To be determined"
    if "open" in s:                       # "Open Access", "will be open access", "OpenAcces"
        return "Open access"
    if "embargo" in s:                    # "Embargoed", "Preliminary (embargoed)"
        return "Embargoed"
    if "restrict" in s:
        return "Restricted"
    return "Other"


def ta_normalize_integration(val):
    """Map 'Expected strategy of integration' onto a handful of platforms."""
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in _TA_BOGUS:
        return None
    if "sdl" in s and "epos" not in s and "eccsel" not in s and "dmp" not in s:
        return "SDL"
    if "epos" in s:
        return "EPOS platform"
    if "eccsel" in s:
        return "ECCSEL"
    if "dmp" in s or "geo-i" in s:
        return "Geo-INQUIRE DMP"
    return "Other / mixed"


def ta_data_exposure_status(row):
    """
    Classify whether a TA project has actually exposed a produced asset.

    Looks across the outcome/metadata/asset columns for a DOI or a URL:
      • "Asset linked (DOI/URL)" — a concrete, citable/линkable output exists.
      • "In progress"            — research ongoing / not yet available / planned.
      • "Described, no link"      — outcomes described in prose but no link given.
      • "Not reported"           — nothing recorded at all.
    """
    cols = ["outcome_metadata", "delivered_outcomes", "associated_va", "expected_outcomes"]
    text = " ".join(str(row.get(c, "")) for c in cols if c in row.index)
    t = text.lower()
    has_doi = ("doi" in t) or bool(re.search(r"10\.\d{4,9}/\S+", text))
    has_url = bool(re.search(r"https?://", t))
    if has_doi or has_url:
        return "Asset linked (DOI/URL)"
    blank = t.replace("nan", "").strip()
    if not blank:
        return "Not reported"
    if any(k in t for k in ["not yet", "ongoing", "to be determin", "tbd",
                            "in development", "in progress", "submitted", "preprint"]):
        return "In progress"
    return "Described, no link"


def ta_count_asset_links(df):
    """Count how many distinct DOIs / URLs are recorded across the TA outcomes."""
    cols = [c for c in ["outcome_metadata", "delivered_outcomes", "associated_va"] if c in df.columns]
    found = set()
    for _, row in df.iterrows():
        text = " ".join(str(row.get(c, "")) for c in cols)
        for m in re.findall(r"https?://\S+", text):
            found.add(m.rstrip(".,);"))
        for m in re.findall(r"10\.\d{4,9}/\S+", text):
            found.add("doi:" + m.rstrip(".,);"))
    return len(found)


def ta_reporting_completeness(df):
    """
    Return a tidy DataFrame of how completely each lifecycle field is filled,
    as a percentage of the projects in `df`.  Useful as a 'metadata / reporting
    completeness' bar chart.
    """
    fields = {
        "Project stage":       "project_stage",
        "Visit dates":         "visit_start",
        "Units used":          "units_used",
        "No. of users":        "number_of_users",
        "Expected outcomes":   "expected_outcomes",
        "Delivered outcomes":  "delivered_outcomes",
        "Outcome metadata":    "outcome_metadata",
        "Access level":        "access_level",
        "Integration":         "integration_strategy",
    }
    n = len(df)
    rows = []
    for label, col in fields.items():
        if col in df.columns and n:
            filled = df[col].dropna().astype(str).str.strip()
            filled = filled[~filled.str.lower().isin(_TA_BOGUS)]
            pct = round(100 * len(filled) / n, 1)
        else:
            pct = 0.0
        rows.append((label, pct))
    return pd.DataFrame(rows, columns=["Field", "Completeness %"])

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

    NOTE: this function intentionally does NOT render the column-source
    annotation any more.  The caller (`render_in_year_tabs` /
    `render_in_call_tabs`) already shows exactly one source line per figure;
    rendering it here as well produced the duplicate "Source column: …" lines.
    The `col_keys` / `access_type` parameters are kept for backwards
    compatibility but are no longer used for annotation.
    """
    if fig is None:
        return
    
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
    """
    Elegant bar chart.

    Refinements over the default Plotly look:
      • Title left-aligned (editorial style) instead of centered.
      • Subtle horizontal grid only (no vertical gridlines, no axis lines).
      • Larger top margin so the bar value labels never clip the title.
      • Slightly muted bar colors from the curated COLORS palette.
    """
    if df is None or df.empty:
        return go.Figure()

    if color_palette is None:
        color_palette = COLORS['blue_palette']

    fig = go.Figure()
    bar_kwargs = dict(
        marker=dict(
            color=color_palette if isinstance(color_palette, list) else [color_palette] * len(df),
            line=dict(width=0),
        ),
        textfont=dict(size=12, family=FONT_FAMILY, color=COLORS['secondary']),
        showlegend=False,
        hovertemplate='<b>%{x}</b>: %{y}<extra></extra>' if orientation == 'v'
                      else '<b>%{y}</b>: %{x}<extra></extra>',
    )
    if orientation == 'v':
        fig.add_trace(go.Bar(x=df[x], y=df[y], text=df[y],
                             textposition='outside', **bar_kwargs))
    else:
        fig.add_trace(go.Bar(x=df[x], y=df[y], orientation='h', text=df[x],
                             textposition='outside', **bar_kwargs))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.02, xanchor='left',
                   font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY,
                             color=COLORS['primary'])),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, title='',
                   tickfont=dict(size=TICK_FONT_SIZE, color=COLORS['secondary'])),
        yaxis=dict(showgrid=True, gridcolor='rgba(15,23,42,0.06)', gridwidth=1,
                   zeroline=False, showline=False, title='',
                   tickfont=dict(size=TICK_FONT_SIZE, color=COLORS['secondary'])),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=24, r=24, t=72, b=48),
        height=500,
        width=1200,
        font=dict(family=FONT_FAMILY, color=COLORS['secondary']),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=10)),
    )
    return fig


def _filter_zero_slices(labels, values):
    """
    Strip misleading slices from a labels/values pair before drawing a pie or
    donut.  Removes any slice whose label is empty / "0" / "0.0" / "nan" / "-",
    AND any slice whose value is zero (no point drawing an invisible wedge).
    Returns a list of (label, value) pairs.
    """
    bogus = {"", "0", "0.0", "nan", "None", "n/a", "N/A", "-"}
    out = []
    for lab, val in zip(labels, values):
        s = "" if lab is None else str(lab).strip()
        try:
            v_num = float(val)
        except Exception:
            v_num = 0.0
        if s in bogus or v_num <= 0:
            continue
        out.append((s, v_num))
    return out


def create_professional_donut_chart(df, names, values, title, color_map=None):
    """
    Elegant donut chart.

    • Slices with label "0" / empty / "nan" or value ≤ 0 are dropped silently —
      this is what fixes the misleading "0 — 51.4%" wedge in the TA Project
      Stage chart.
    • Title is left-aligned and stays inside the chart's bounding box.
    • White slice separators give a clean editorial look.
    """
    if df is None or df.empty:
        return go.Figure()

    filtered = _filter_zero_slices(df[names].tolist(), df[values].tolist())
    if not filtered:
        return go.Figure()
    labels = [a for a, _ in filtered]
    vals   = [b for _, b in filtered]

    if color_map:
        colors = [color_map.get(name, COLORS['multi_palette'][i % len(COLORS['multi_palette'])])
                  for i, name in enumerate(labels)]
    else:
        colors = (COLORS['multi_palette'] * (len(labels) // len(COLORS['multi_palette']) + 1))[:len(labels)]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=vals,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='white', width=2.5)),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=12, family=FONT_FAMILY, color=COLORS['dark']),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        pull=[0.01] * len(labels),       # tiny separation between slices
        sort=True,
    ))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.02, xanchor='left',
                   font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY,
                             color=COLORS['primary'])),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=24, r=24, t=72, b=120),
        height=520,
        width=1200,
        font=dict(family=FONT_FAMILY),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                    xanchor="center", x=0.5,
                    font=dict(size=11, color=COLORS['secondary']),
                    traceorder="normal", bgcolor='rgba(0,0,0,0)'),
    )
    return fig


def create_professional_pie_chart(df, names, values, title, color_map=None):
    """
    Elegant pie chart.

    Same zero-/empty-slice filter as the donut so categorical pies (e.g. the
    Authentication chart that showed a misleading "0" slice at 2.8 %) only
    contain meaningful labels.
    """
    if df is None or df.empty:
        return go.Figure()

    filtered = _filter_zero_slices(df[names].tolist(), df[values].tolist())
    if not filtered:
        return go.Figure()
    labels = [a for a, _ in filtered]
    vals   = [b for _, b in filtered]

    if color_map:
        colors = [color_map.get(name, COLORS['multi_palette'][i % len(COLORS['multi_palette'])])
                  for i, name in enumerate(labels)]
    else:
        colors = (COLORS['multi_palette'] * (len(labels) // len(COLORS['multi_palette']) + 1))[:len(labels)]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=vals,
        marker=dict(colors=colors, line=dict(color='white', width=2.5)),
        textinfo='percent',
        textfont=dict(size=12, family=FONT_FAMILY, color='white'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        sort=True,
    ))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.02, xanchor='left',
                   font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY,
                             color=COLORS['primary'])),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=24, r=24, t=72, b=120),
        height=520,
        width=1200,
        font=dict(family=FONT_FAMILY),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                    xanchor="center", x=0.5,
                    font=dict(size=11, color=COLORS['secondary']),
                    traceorder="normal", bgcolor='rgba(0,0,0,0)'),
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
            st.markdown("## Key Metrics Overview")
            
            # Row 1: RI and Implementation Status (2 columns)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                # ── FIGURE 1: Research Infrastructures (RI) ─────────────────────
                # Builds a bar chart of the number of services per RI.
                # The figure is then rendered inside four year tabs (2023–2026)
                # via `render_in_year_tabs`, with placeholder banners so the
                # user can replace each tab's content with year-specific data.
                def _builder(_df, _yr):
                    if not ('compliant_ri' in _df.columns):
                        return None
                    ri_counts = _df['compliant_ri'].value_counts().to_dict()
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
                    return fig_ri
                render_in_year_tabs(
                    _builder,
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
                def _builder(_df, _yr):
                    if not ('implementation_status' in _df.columns):
                        return None
                    impl_counts = _df['implementation_status'].apply(standardize_implementation_value).value_counts().to_dict()
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
                    
                    return fig_impl
                render_in_year_tabs(
                    _builder,
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
                def _builder(_df, _yr):
                    if not ('data_repr' in _df.columns):
                        return None
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
                    
                    data_repr_counts = _df['data_repr'].apply(simplify_data_repr).value_counts().head(8).to_dict()
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
                    
                    return fig_repr
                render_in_year_tabs(
                    _builder,
                    figure_key="data_representations",
                    source_cols=["data_repr"],
                    access_type="VA",
                    download_label_base="data_representations",
                    figure_title="3. Data Representations",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('license' in _df.columns):
                        return None
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
                    
                    license_clean = _df['license'].apply(simplify_license).dropna().astype(str).str.strip()
                    _bogus = {"", "0", "0.0", "nan", "None", "n/a", "N/A", "-"}
                    license_clean = license_clean[~license_clean.isin(_bogus)]
                    license_counts = license_clean.value_counts().head(8).to_dict()
                    license_data = pd.DataFrame(list(license_counts.items()), columns=['License', 'Count']).sort_values('Count', ascending=False)
                    
                    fig_license = go.Figure()
                    fig_license.add_trace(go.Pie(
                        labels=license_data['License'],
                        values=license_data['Count'],
                        marker=dict(colors=COLORS['multi_palette'][:len(license_data)], line=dict(color='white', width=2.5)),
                        textinfo='label+percent',
                        textposition='outside',
                        textfont=dict(size=12, family=FONT_FAMILY, color=COLORS['dark']),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                        sort=True,
                    ))
                    
                    fig_license.update_layout(
                        title=dict(text='<b>4. License Distribution</b>', x=0.02, xanchor='left',
                                 font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['primary'])),
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
                            font=dict(size=11, color=COLORS['secondary'])
                        ),
                        margin=dict(l=40, r=40, t=80, b=110)
                    )
                    
                    return fig_license
                render_in_year_tabs(
                    _builder,
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
            def _builder(_df, _yr):
                if not ('metadata_standard' in _df.columns):
                    return None
                metadata_counts = _df['metadata_standard'].value_counts().head(10).to_dict()
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
                
                return fig_metadata
            render_in_year_tabs(
                _builder,
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
            st.markdown("## Implementation Matrix Analysis")
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if va_df is not None and not va_df.empty:
                try:
                    # Build the heatmap fresh per year tab using the matching
                    # historical snapshot.  the 2026 tab uses the live data.
                    _heatmap_tabs = st.tabs(list(YEAR_TAB_LABELS))
                    for _tab, _yr in zip(_heatmap_tabs, YEAR_TAB_KEYS):
                        with _tab:
                            year_df = VA_DATA_BY_YEAR.get(_yr)
                            if year_df is None or year_df.empty:
                                st.info(f"📂 No data available for **{_yr}**. "
                                        f"Drop the matching snapshot into `ILM_Old/` to populate this tab.")
                                continue
                            try:
                                fig_heatmap_y = create_enhanced_heatmap(year_df)
                            except Exception as e:
                                st.warning(f"Could not build heatmap for {_yr}: {e}")
                                continue
                            if not fig_heatmap_y:
                                st.info(f"Heatmap data not available for {_yr}.")
                                continue
                            st.pyplot(fig_heatmap_y, clear_figure=False, use_container_width=False)

                            # Single download button only on the 2026 (live) tab.
                            if _yr == LIVE_YEAR_KEY:
                                buf = io.BytesIO()
                                fig_heatmap_y.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                                buf.seek(0)
                                st.download_button(
                                    label="Download Implementation Matrix (High-Res PNG)",
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
                except Exception as e:
                    st.warning(f"Could not generate heatmap: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Virtual Access data available")
    
    else:  # Transnational Access
        if ta_df is not None and not ta_df.empty:
            # Work on the actual TA *projects* (rows with a project_id), not the
            # installation-definition rows that pad the sheet.
            ta_projects = ta_df.copy()
            if 'project_id' in ta_projects.columns:
                ta_projects = ta_projects[ta_projects['project_id'].notna()]

            # ── KPI row: outcomes & exposure focused ────────────────────────
            n_proj   = len(ta_projects)
            n_hosts  = ta_projects['ta_host'].nunique() if 'ta_host' in ta_projects.columns else 0
            n_users  = int(pd.to_numeric(ta_projects.get('number_of_users'), errors='coerce').fillna(0).sum()) if 'number_of_users' in ta_projects.columns else 0
            exposure = ta_projects.apply(ta_data_exposure_status, axis=1) if n_proj else pd.Series(dtype=str)
            n_linked = int((exposure == "Asset linked (DOI/URL)").sum()) if n_proj else 0
            n_doi_url = ta_count_asset_links(ta_projects)
            exposure_rate = round(100 * n_linked / n_proj, 0) if n_proj else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"<div class='kpi'><h3>TA Projects</h3><div class='val'>{n_proj}</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='kpi'><h3>Host Facilities</h3><div class='val'>{n_hosts}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='kpi'><h3>Users Served</h3><div class='val'>{n_users}</div></div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div class='kpi'><h3>Assets Exposed</h3><div class='val'>{int(exposure_rate)}%</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("## Outcomes & Access")
            st.caption(
                "TA projects are grouped by funding Call. These panels focus on what each "
                "access actually produced — delivered outcomes, where assets are exposed, "
                "the level of access granted, and how outputs integrate with the RIs."
            )

            # ── Row 1: Project-stage funnel | Data-exposure status ──────────
            col1, col2 = st.columns(2)
            with col1:
                def _builder(_df, _yr):
                    stage_clean = _df['project_stage'].dropna().astype(str).str.strip() if 'project_stage' in _df.columns else pd.Series(dtype=str)
                    stage_clean = stage_clean[~stage_clean.str.lower().isin(_TA_BOGUS)]
                    if stage_clean.empty:
                        return None
                    stage_data = (stage_clean.value_counts()
                                  .rename_axis('Stage').reset_index(name='Count'))
                    stage_color_map = {
                        'Visit/access exhausted': COLORS['exhausted'],
                        'Time window for the visit/access fixed': COLORS['fixed'],
                        'Data/products ready': COLORS['ready'],
                        'PI contacted': COLORS['contacted'],
                        'Project details negotiated': COLORS['negotiated'],
                    }
                    return create_professional_donut_chart(stage_data, 'Stage', 'Count',
                                                           'Project Stage (lifecycle)',
                                                           color_map=stage_color_map)
                render_in_call_tabs(_builder, figure_key="ta_stage",
                                    ta_dataframe=ta_df, source_cols=["project_stage"],
                                    download_label_base="ta_stage",
                                    figure_title="Project Stage")
            with col2:
                def _builder(_df, _yr):
                    if _df.empty:
                        return None
                    exp = _df.apply(ta_data_exposure_status, axis=1)
                    exp_data = exp.value_counts().rename_axis('Status').reset_index(name='Count')
                    color_map = {
                        'Asset linked (DOI/URL)': COLORS['success'],
                        'In progress':            COLORS['warning'],
                        'Described, no link':     COLORS['accent'],
                        'Not reported':           COLORS['unknown'],
                    }
                    return create_professional_donut_chart(exp_data, 'Status', 'Count',
                                                           'Data Exposure of Produced Assets',
                                                           color_map=color_map)
                render_in_call_tabs(_builder, figure_key="ta_exposure",
                                    ta_dataframe=ta_df,
                                    source_cols=["delivered_outcomes", "outcome_metadata"],
                                    download_label_base="ta_exposure",
                                    figure_title="Data Exposure")

            st.markdown("---")

            # ── Row 2: Access level | Integration strategy ──────────────────
            col1, col2 = st.columns(2)
            with col1:
                def _builder(_df, _yr):
                    if 'access_level' not in _df.columns:
                        return None
                    lvl = _df['access_level'].apply(ta_normalize_access_level).dropna()
                    if lvl.empty:
                        return None
                    lvl_data = lvl.value_counts().rename_axis('Level').reset_index(name='Count')
                    color_map = {
                        'Open access':       COLORS['success'],
                        'Embargoed':         COLORS['warning'],
                        'Restricted':        COLORS['danger'],
                        'To be determined':  COLORS['unknown'],
                        'Other':             COLORS['accent'],
                    }
                    return create_professional_donut_chart(lvl_data, 'Level', 'Count',
                                                           'Level of Access',
                                                           color_map=color_map)
                render_in_call_tabs(_builder, figure_key="ta_access",
                                    ta_dataframe=ta_df, source_cols=["access_level"],
                                    download_label_base="ta_access",
                                    figure_title="Level of Access")
            with col2:
                def _builder(_df, _yr):
                    if 'integration_strategy' not in _df.columns:
                        return None
                    integ = _df['integration_strategy'].apply(ta_normalize_integration).dropna()
                    if integ.empty:
                        return None
                    integ_data = (integ.value_counts()
                                  .rename_axis('Strategy').reset_index(name='Count')
                                  .sort_values('Count', ascending=True))
                    return create_professional_bar_chart(integ_data, 'Count', 'Strategy',
                                                         'Integration Strategy (asset destination)',
                                                         orientation='h',
                                                         color_palette=COLORS['blue_palette'])
                render_in_call_tabs(_builder, figure_key="ta_integration",
                                    ta_dataframe=ta_df, source_cols=["integration_strategy"],
                                    download_label_base="ta_integration",
                                    figure_title="Integration Strategy")

            st.markdown("---")

            # ── Row 3: Reporting / metadata completeness (full width) ───────
            st.markdown("### Reporting & Metadata Completeness")
            st.caption(
                "How completely each stage of the TA lifecycle is recorded, as a share of "
                "projects in the selected Call — a proxy for metadata quality and follow-up."
            )
            def _builder(_df, _yr):
                comp = ta_reporting_completeness(_df)
                if comp.empty or comp['Completeness %'].sum() == 0:
                    return None
                comp = comp.sort_values('Completeness %', ascending=True)
                fig = create_professional_bar_chart(comp, 'Completeness %', 'Field',
                                                    'Lifecycle Field Completeness (%)',
                                                    orientation='h',
                                                    color_palette=COLORS['green_palette'])
                fig.update_layout(xaxis=dict(range=[0, 100]))
                return fig
            render_in_call_tabs(_builder, figure_key="ta_completeness",
                                ta_dataframe=ta_df,
                                source_cols=["expected_outcomes", "delivered_outcomes",
                                             "outcome_metadata"],
                                download_label_base="ta_completeness",
                                figure_title="Reporting Completeness")
        else:
            st.warning("No Transnational Access data available")

elif selected == "Analytics":
    st.markdown("<span class='small'>Home → Analytics</span>", unsafe_allow_html=True)
    st.header("Detailed Analytics")
    
    if project_label == "Virtual Access":
        # ORIGINAL VA ANALYTICS CODE
        if va_df is not None and not va_df.empty:
            va_stats = compute_va_statistics(va_df)
            
            st.markdown("## Implementation Level 1")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('service_running' in _stats):
                        return None
                    running_data = pd.DataFrame(list(_stats['service_running'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_running = create_professional_donut_chart(running_data, 'Status', 'Count',
                                                                 'Service Running Status',
                                                                 color_map=color_map)
                    return fig_running
                render_in_year_tabs(
                    _builder,
                    figure_key="service_running",
                    source_cols=["service_running"],
                    access_type="VA",
                    download_label_base="service_running",
                    figure_title="Service Running",
                )
            st.markdown("---")
            
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('api_standard' in _df.columns):
                        return None
                    api_counts = _df['api_standard'].value_counts().head(8).to_dict()
                    api_data = pd.DataFrame(list(api_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                    fig_api = create_professional_bar_chart(api_data, 'Standard', 'Count',
                                                           'API Standards Distribution',
                                                           orientation='v',
                                                           color_palette=COLORS['blue_palette'])
                    return fig_api
                render_in_year_tabs(
                    _builder,
                    figure_key="api_standards",
                    source_cols=["api_standard"],
                    access_type="VA",
                    download_label_base="api_standards",
                    figure_title="Api Standards",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('metadata_standard' in _df.columns):
                        return None
                    meta_counts = _df['metadata_standard'].value_counts().head(6).to_dict()
                    meta_data = pd.DataFrame(list(meta_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                    fig_meta = create_professional_pie_chart(meta_data, 'Standard', 'Count',
                                                            'Metadata Standards')
                    return fig_meta
                render_in_year_tabs(
                    _builder,
                    figure_key="metadata_standards",
                    source_cols=["metadata_standard"],
                    access_type="VA",
                    download_label_base="metadata_standards",
                    figure_title="Metadata Standards",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("## Implementation Level 2")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('parametrization' in _stats):
                        return None
                    param_data = pd.DataFrame(list(_stats['parametrization'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_param = create_professional_donut_chart(param_data, 'Status', 'Count',
                                                               'Service Parametrization',
                                                               color_map=color_map)
                    return fig_param
                render_in_year_tabs(
                    _builder,
                    figure_key="parametrization",
                    source_cols=["parametrization"],
                    access_type="VA",
                    download_label_base="parametrization",
                    figure_title="Parametrization",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('license' in _df.columns):
                        return None
                    license_counts = _df['license'].value_counts().head(6).to_dict()
                    license_data = pd.DataFrame(list(license_counts.items()), columns=['License', 'Count']).sort_values('Count', ascending=False)
                    fig_license = create_professional_pie_chart(license_data, 'License', 'Count',
                                                                'License Distribution')
                    return fig_license
                render_in_year_tabs(
                    _builder,
                    figure_key="license_types",
                    source_cols=["license"],
                    access_type="VA",
                    download_label_base="license_types",
                    figure_title="License Types",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('fully_described' in _stats):
                        return None
                    desc_data = pd.DataFrame(list(_stats['fully_described'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_desc = create_professional_donut_chart(desc_data, 'Status', 'Count',
                                                              'Full Description Status',
                                                              color_map=color_map)
                    return fig_desc
                render_in_year_tabs(
                    _builder,
                    figure_key="fully_described",
                    source_cols=["fully_described"],
                    access_type="VA",
                    download_label_base="fully_described",
                    figure_title="Fully Described",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("## Implementation Level 3")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('documentation' in _stats):
                        return None
                    doc_data = pd.DataFrame(list(_stats['documentation'].items()), columns=['Status', 'Count']).sort_values('Count', ascending=False)
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
                    return fig_doc
                render_in_year_tabs(
                    _builder,
                    figure_key="documentation",
                    source_cols=["documentation_status"],
                    access_type="VA",
                    download_label_base="documentation",
                    figure_title="Documentation",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('payloads' in _stats):
                        return None
                    payload_data = pd.DataFrame(list(_stats['payloads'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_payload = create_professional_donut_chart(payload_data, 'Status', 'Count',
                                                                 'Payload Support',
                                                                 color_map=color_map)
                    return fig_payload
                render_in_year_tabs(
                    _builder,
                    figure_key="payloads",
                    source_cols=["payloads"],
                    access_type="VA",
                    download_label_base="payloads",
                    figure_title="Payloads",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('auth' in _stats):
                        return None
                    auth_data = pd.DataFrame(list(_stats['auth'].items()), columns=['Method', 'Count']).sort_values('Count', ascending=False)
                    fig_auth = create_professional_pie_chart(auth_data, 'Method', 'Count',
                                                            'Authentication Methods')
                    return fig_auth
                render_in_year_tabs(
                    _builder,
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
                def _builder(_df, _yr):
                    _stats = compute_va_statistics(_df)
                    if not ('converter' in _stats):
                        return None
                    conv_data = pd.DataFrame(list(_stats['converter'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_conv = create_professional_donut_chart(conv_data, 'Status', 'Count',
                                                              'Converter Plugin Availability',
                                                              color_map=color_map)
                    return fig_conv
                render_in_year_tabs(
                    _builder,
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
            st.markdown("## Comprehensive Transnational Access Analytics")
            st.markdown("---")
            
            # Row 1
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('pi_gender' in _df.columns):
                        return None
                    gender_counts = _df['pi_gender'].value_counts().to_dict()
                    gender_data = pd.DataFrame(list(gender_counts.items()), columns=['Gender', 'Count'])
                    color_map = {'Female': COLORS['danger'], 'Male': COLORS['accent'], 'Other': COLORS['unknown']}
                    fig_gender = create_professional_pie_chart(gender_data, 'Gender', 'Count',
                                                              'Principal Investigator Gender Distribution',
                                                              color_map=color_map)
                    return fig_gender
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_gender_distribution",
                    ta_dataframe=ta_df,
                    source_cols=["pi_gender"],
                    download_label_base="ta_gender_distribution",
                    figure_title="Gender Distribution",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('ta_host' in _df.columns):
                        return None
                    host_counts = _df['ta_host'].value_counts().head(10).to_dict()
                    host_data = pd.DataFrame(list(host_counts.items()), columns=['Host', 'Count']).sort_values('Count', ascending=True)
                    fig_host = create_professional_bar_chart(host_data, 'Count', 'Host',
                                                            'Top 10 TA Host Distribution',
                                                            orientation='h',
                                                            color_palette=COLORS['green_palette'])
                    return fig_host
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_host_distribution",
                    ta_dataframe=ta_df,
                    source_cols=["ta_host"],
                    download_label_base="ta_host_distribution",
                    figure_title="Host Distribution",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 2
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('unit_of_access' in _df.columns):
                        return None
                    unit_counts = _df['unit_of_access'].value_counts().to_dict()
                    unit_data = pd.DataFrame(list(unit_counts.items()), columns=['Unit', 'Count'])
                    fig_unit = create_professional_pie_chart(unit_data, 'Unit', 'Count',
                                                            'Access Unit Types')
                    return fig_unit
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_access_units",
                    ta_dataframe=ta_df,
                    source_cols=["unit_of_access"],
                    download_label_base="ta_access_units",
                    figure_title="Access Units",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('number_of_users' in _df.columns):
                        return None
                    user_counts = _df['number_of_users'].value_counts().head(8).to_dict()
                    user_data = pd.DataFrame(list(user_counts.items()), columns=['Users', 'Count']).sort_values('Users')
                    fig_users = create_professional_bar_chart(user_data, 'Users', 'Count',
                                                             'Number of Users Distribution',
                                                             orientation='v',
                                                             color_palette=['#8E44AD'] * len(user_data))
                    return fig_users
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_number_of_users",
                    ta_dataframe=ta_df,
                    source_cols=["number_of_users"],
                    download_label_base="ta_number_of_users",
                    figure_title="Number Of Users",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 3: Call-Based Analysis
            st.markdown("### Call-Based Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('call' in _df.columns and 'pi_gender' in _df.columns):
                        return None
                    call_gender = _df.groupby(['call', 'pi_gender']).size().reset_index(name='count')
                    fig_call_gender = px.bar(
                        call_gender,
                        x='call',
                        y='count',
                        color='pi_gender',
                        title='Gender Distribution by Call',
                        labels={'count': 'Number of Applications', 'call': 'Call', 'pi_gender': 'Gender'},
                        color_discrete_map={'Female': COLORS['danger'], 'Male': COLORS['accent'], 'Other': COLORS['unknown']},
                        height=400
                    )
                    fig_call_gender.update_layout(
                        font=dict(family=FONT_FAMILY, size=12),
                        title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                        margin=dict(l=60, r=60, t=60, b=100)
                    )
                    return fig_call_gender
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_call_gender",
                    ta_dataframe=ta_df,
                    source_cols=["call", "pi_gender"],
                    download_label_base="ta_call_gender",
                    figure_title="Call Gender",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('call' in _df.columns and 'ta_host' in _df.columns):
                        return None
                    top_hosts = _df['ta_host'].value_counts().head(5).index
                    call_host_filtered = _df[_df['ta_host'].isin(top_hosts)]
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
                    return fig_call_host
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_call_host",
                    ta_dataframe=ta_df,
                    source_cols=["call", "ta_host"],
                    download_label_base="ta_call_host",
                    figure_title="Call Host",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 4: Temporal Analysis
            st.markdown("### Temporal Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'visit_start' in ta_df.columns:
                    ta_temporal = ta_df[ta_df['visit_start'].notna()].copy()
                    def _builder(_df, _yr):
                        if not (not ta_temporal.empty):
                            return None
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
                        
                        return fig_monthly
                    render_in_call_tabs(
                        _builder,
                        figure_key="ta_monthly_distribution",
                        ta_dataframe=ta_df,
                        source_cols=["visit_start"],
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
                        
                        def _builder(_df, _yr):
                            if not (not units_comparison.empty):
                                return None
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
                            
                            return fig_units
                        render_in_call_tabs(
                            _builder,
                            figure_key="ta_units_comparison",
                            ta_dataframe=ta_df,
                            source_cols=["units_requested", "units_used"],
                            download_label_base="ta_units_comparison",
                            figure_title="Units Comparison",
                        )
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 5: Geographic/Institutional
            st.markdown("### Geographic and Institutional Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('pi_affiliation' in _df.columns):
                        return None
                    affil_counts = _df['pi_affiliation'].value_counts().head(10)
                    affil_data = pd.DataFrame({
                        'Institution': affil_counts.index,
                        'Applications': affil_counts.values
                    }).sort_values('Applications', ascending=True)
                    
                    fig_affil = create_professional_bar_chart(
                        affil_data, 'Applications', 'Institution',
                        'Top 10 PI Institutions',
                        orientation='h',
                        color_palette=[COLORS['warning']] * len(affil_data)
                    )
                    return fig_affil
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_top_institutions",
                    ta_dataframe=ta_df,
                    source_cols=["pi_affiliation"],
                    download_label_base="ta_top_institutions",
                    figure_title="Top Institutions",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                def _builder(_df, _yr):
                    if not ('associated_wp' in _df.columns):
                        return None
                    wp_counts = _df['associated_wp'].value_counts().to_dict()
                    wp_data = pd.DataFrame(list(wp_counts.items()), columns=['Work Package', 'Count'])
                    fig_wp = create_professional_pie_chart(wp_data, 'Work Package', 'Count',
                                                           'Associated Work Packages')
                    return fig_wp
                render_in_call_tabs(
                    _builder,
                    figure_key="ta_work_packages",
                    ta_dataframe=ta_df,
                    source_cols=["associated_wp"],
                    download_label_base="ta_work_packages",
                    figure_title="Work Packages",
                )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Transnational Access data available")

elif selected == "KPI":
    # =========================================================================
    # KPI PAGE — intentionally a clean placeholder for now.
    #
    # The KPI framework is being defined in the context of the Geo-INQUIRE
    # reporting obligations (TRL progression, test users, datasets served, …).
    # Rather than ship half-finished charts, this page shows a clear
    # "under development" state.  When the indicator set is finalised, replace
    # the placeholder block below with the real KPI computations.
    # =========================================================================
    st.markdown("<span class='small'>Home → KPI</span>", unsafe_allow_html=True)
    st.header("Key Performance Indicators")
    st.caption(f"Project context: {project_label}")

    # Centred "under development" card.
    st.markdown("""
    <div style="margin-top:2.5rem; padding:3rem 2rem; border-radius:16px;
                background:linear-gradient(135deg,#f8fafc 0%,#eef2f6 100%);
                border:1px solid #e2e8f0; text-align:center;">
        <div style="font-size:0.8rem; font-weight:700; letter-spacing:1.5px;
                    text-transform:uppercase; color:#2563eb; margin-bottom:0.8rem;">
            Under Development
        </div>
        <div style="font-size:1.6rem; font-weight:800; color:#1f3a5f; margin-bottom:0.6rem;">
            KPI dashboard coming soon
        </div>
        <div style="font-size:0.95rem; color:#64748b; max-width:620px; margin:0 auto; line-height:1.6;">
            This section is reserved for the project's Key Performance Indicators.
            The indicator set is being finalised against the Geo-INQUIRE reporting
            framework. Planned indicators include:
        </div>
        <div style="margin-top:1.5rem; display:flex; gap:0.75rem; justify-content:center; flex-wrap:wrap;">
            <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                         padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                TRL progression
            </span>
            <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                         padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                Test users
            </span>
            <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                         padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                Users served
            </span>
            <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                         padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                Datasets accessible
            </span>
            <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                         padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                Service uptime
            </span>
        </div>
        <div style="margin-top:2rem; font-size:0.8rem; color:#94a3b8;">
            Indicators will be added here once the analysis is complete.
        </div>
    </div>
    """, unsafe_allow_html=True)

elif selected == "Data":
    # Breadcrumb-style header line
    st.markdown("<span class='small'>Home → Data</span>", unsafe_allow_html=True)
    st.header("Data")

    # ── Two views of the ILM data: the human-readable table (today) and a ──
    #    reserved space for the machine-readable / API-style representation ──
    #    the team is planning to add. ───────────────────────────────────────
    data_tab_table, data_tab_machine = st.tabs(
        ["Table view", "Machine-readable (in progress)"]
    )

    with data_tab_table:
        # A short note explaining the 4-row header to anyone unfamiliar with the
        # Excel layout — keeps the table self-documenting.
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
                    "Download VA CSV (original column names)",
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
                    "Download TA CSV (original column names)",
                    data=ta_raw.to_csv(index=False).encode("utf-8"),
                    file_name="TA_data.csv",
                    mime="text/csv",
                    key="ta_csv_download",
                )
            else:
                st.warning("No Transnational Access data available")



    with data_tab_machine:
        # ── RESERVED SPACE for the machine-readable ILM ────────────────────
        # The team plans to publish the ILM as machine-readable data (e.g. a
        # tidy long-format table, JSON-LD, or a small API) rather than the
        # rigid wide spreadsheet.  This tab is the placeholder for that work.
        st.markdown("""
        <div style="margin-top:1rem; padding:2.5rem 2rem; border-radius:16px;
                    background:linear-gradient(135deg,#f8fafc 0%,#eef2f6 100%);
                    border:1px solid #e2e8f0; text-align:center;">
            <div style="font-size:0.8rem; font-weight:700; letter-spacing:1.5px;
                        text-transform:uppercase; color:#2563eb; margin-bottom:0.8rem;">
                In Progress
            </div>
            <div style="font-size:1.5rem; font-weight:800; color:#1f3a5f; margin-bottom:0.6rem;">
                Machine-readable ILM
            </div>
            <div style="font-size:0.95rem; color:#64748b; max-width:640px; margin:0 auto; line-height:1.6;">
                This space is reserved for a FAIR, machine-readable version of the
                Implementation Level Matrix — replacing the rigid wide table with a
                tidy long-format dataset that downstream tools and the EOSC landscape
                can consume directly. Planned outputs:
            </div>
            <div style="margin-top:1.5rem; display:flex; gap:0.75rem; justify-content:center; flex-wrap:wrap;">
                <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                             padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                    Tidy long-format CSV
                </span>
                <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                             padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                    JSON / JSON-LD
                </span>
                <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                             padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                    Controlled vocabularies
                </span>
                <span style="background:#ffffff; border:1px solid #cbd5e1; border-radius:999px;
                             padding:0.5rem 1.1rem; font-size:0.85rem; font-weight:600; color:#1f3a5f;">
                    Per-column metadata
                </span>
            </div>
            <div style="margin-top:2rem; font-size:0.8rem; color:#94a3b8;">
                Drop the transformed dataset in here when ready — this tab is the home for it.
            </div>
        </div>
        """, unsafe_allow_html=True)

elif selected == "Contact":
    st.markdown("<span class='small'>Home → Contact</span>", unsafe_allow_html=True)
    st.header("Contact & Project Information")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("""
        <div style="background:#ffffff; padding:1.5rem; border-radius:14px;
                    border:1px solid #e2e8f0; border-left:4px solid #2563eb;
                    line-height:1.7;">
            <div style="font-size:1.1rem; font-weight:800; color:#1f3a5f; margin-bottom:0.6rem;">
                Dashboard team
            </div>
            <div style="color:#334155; font-size:0.95rem;">
                <strong>Conceived by:</strong> Jan Michalek &amp; Juliano Ramanantsoa<br>
                <strong>Affiliation:</strong> University of Bergen, Norway<br>
                <strong>Contact:</strong>
                <a href="mailto:heriniaina.j.ramanantsoa@uib.no"
                   style="color:#2563eb; text-decoration:none; font-weight:600;">
                   heriniaina.j.ramanantsoa@uib.no</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background:#ffffff; padding:1.5rem; border-radius:14px;
                    border:1px solid #e2e8f0; border-left:4px solid #0e9f6e;
                    line-height:1.7;">
            <div style="font-size:1.1rem; font-weight:800; color:#1f3a5f; margin-bottom:0.6rem;">
                Geo-INQUIRE project
            </div>
            <div style="color:#334155; font-size:0.95rem;">
                <strong>Full name:</strong> Geosphere INfrastructures for QUestions
                into Integrated REsearch<br>
                <strong>Programme:</strong> Horizon Europe — Research Infrastructures<br>
                <strong>Grant agreement:</strong> 101058518<br>
                <strong>Call:</strong> HORIZON-INFRA-2021-SERV-01<br>
                <strong>Duration:</strong> 1 Oct 2022 – 30 Sep 2026<br>
                <strong>EU contribution:</strong> €13,923,475.77<br>
                <strong>Coordinator:</strong> GFZ Helmholtz Centre for Geosciences
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1.2rem; font-size:0.85rem; color:#64748b; line-height:1.6;">
        <strong>Acknowledgement:</strong> Geo-INQUIRE is funded by the European
        Commission under project number 101058518 within the
        HORIZON-INFRA-2021-SERV-01 call.<br>
        Project website:
        <a href="https://www.geo-inquire.eu/" target="_blank"
           style="color:#2563eb; text-decoration:none; font-weight:600;">www.geo-inquire.eu</a>
    </div>
    """, unsafe_allow_html=True)


# ===============================================================================================
# PAGE FOOTER — EU funding acknowledgement on every page
# ===============================================================================================
# This runs at module level after the page-routing if/elif chain above, so the
# acknowledgement banner appears at the bottom of whichever page is selected.
# (Skipped implicitly on the login screen because the app returns early there.)
render_eu_acknowledgement(variant="footer")

