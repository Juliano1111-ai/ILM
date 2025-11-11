# =====================================================================================
# ILM Geo-INQUIRE Dashboard - Professional Implementation Level Matrix
# =====================================================================================
#
# Copyright (c) 2024-2025 Geo-INQUIRE Project
# University of Bergen, Norway
#
# Developed by: Juliano Ramanantsoa (Assisted by Claude)
# Project: Geo-INQUIRE - Implementation Level Matrix (ILM) Dashboard
# Purpose: Interactive visualization and analytics for Virtual Access (VA) and 
#          Transnational Access (TA) project data
#
# This dashboard provides:
# - Real-time data integration with Google Sheets
# - Comprehensive analytics and KPI tracking
# - Professional visualizations (300 DPI export capable)
# - Multi-dimensional analysis (gender, hosts, temporal trends)
# - Secure password-protected access
#
# License: Internal use - Geo-INQUIRE Project
# Contact: Geo-INQUIRE Project Administration, University of Bergen
#
# Version: 1.0
# Last Updated: November 11, 2025
#
# =====================================================================================
# INSTALLATION REQUIREMENTS:

# - streamlit: pip install streamlit
# - plotly: pip install plotly
# - pandas: pip install pandas
# - numpy: pip install numpy
# - matplotlib: pip install matplotlib
# - seaborn: pip install seaborn
# - streamlit-option-menu: pip install streamlit-option-menu
# - streamlit-antd-components: pip install streamlit-antd-components (optional)
# - kaleido: pip install -U kaleido (for PNG export of charts)
# - gspread: pip install gspread (for Google Sheets integration)
# - oauth2client: pip install oauth2client (for Google Sheets authentication)
# - openpyxl: pip install openpyxl (for Excel file reading)
#
# =====================================================================================

import os
import io
import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from streamlit_option_menu import option_menu
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

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
            content: "✓";
            position: absolute;
            left: 0;
            font-weight: bold;
            color: #27AE60;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
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
# STREAMLIT PAGE CONFIGURATION
# ===============================================================================================
# Sets up the initial page layout, title, and sidebar state
# ===============================================================================================
st.set_page_config(page_title="ILM Geo-INQUIRE Dashboard", layout="wide", initial_sidebar_state="expanded")

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
    st.markdown("### Project")
    try:
        import streamlit_antd_components as sac
        project_label = sac.segmented(items=['Virtual Access', 'Transnational Access'], align='left', size='sm', color='blue')
    except Exception:
        project_label = st.radio(" ", ["Virtual Access", "Transnational Access"], horizontal=True, label_visibility="collapsed")
    
    st.caption(f"Active: **{project_label}**")

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
    """Load data from local Excel file"""
    try:
        excel_path = "ILM_Python_2.xlsx"
        if not os.path.exists(excel_path):
            st.error(f"Excel file not found: {excel_path}")
            return None, None
        
        # Load VA data
        df_va = pd.read_excel(excel_path, sheet_name='ILM_Connector', header=3, skiprows=[4])
        
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
        
        # Load TA data
        df_ta = pd.read_excel(excel_path, sheet_name='ILM_Connector_TA', header=3, skiprows=[4])
        
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
        
        return df_va, df_ta
        
    except Exception as e:
        st.error(f"Error loading Excel data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None


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
        
        # Try Streamlit Cloud secrets first, then fall back to local JSON file
        try:
            if "gcp_service_account" in st.secrets:
                # Running on Streamlit Cloud - use secrets
                import json
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                client = gspread.authorize(creds)
            else:
                # Running locally - use JSON file
                json_keyfile_path = "valiant-splicer-409609-e34abed30cc1.json"
                if not os.path.exists(json_keyfile_path):
                    st.error(f"❌ Credentials file not found: {json_keyfile_path}")
                    st.info("📝 Place your Google service account JSON file in the same directory as this app")
                    return None, None, "Credentials file missing"
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
                client = gspread.authorize(creds)
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")
            return None, None, f"Auth error: {str(e)}"
        
        # Use the correct spreadsheet URL
        sheet_url = "https://docs.google.com/spreadsheets/d/1noNhzwKOp1_t9RfgJc__zvXs-23t_BofigcZBjTnADM/edit?gid=1373546546#gid=1373546546"
        spreadsheet = client.open_by_url(sheet_url)
        
        # Load Virtual Access data
        try:
            worksheet_va = spreadsheet.worksheet("ILM_Connector")
            data_va = worksheet_va.get_all_values()
            if len(data_va) < 4:
                st.warning("⚠️ Virtual Access worksheet has insufficient data")
                df_va = pd.DataFrame()
            else:
                df_va = pd.DataFrame(data_va[4:], columns=data_va[3])
                
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
            st.info(f"📝 Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
            return None, None, "VA worksheet not found"
        except Exception as e:
            import traceback
            st.error(f"❌ Error loading VA data: {str(e)}")
            st.code(traceback.format_exc())
            return None, None, f"VA data error: {str(e)}"
        
        # Load Transnational Access data
        try:
            worksheet_ta = spreadsheet.worksheet("ILM_Connector_TA")
            data_ta = worksheet_ta.get_all_values()
            if len(data_ta) < 4:
                df_ta = pd.DataFrame()
            else:
                df_ta = pd.DataFrame(data_ta[4:], columns=data_ta[3])
                
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
        except Exception as e:
            st.warning(f"⚠️ Error loading TA data: {str(e)}")
            df_ta = pd.DataFrame()
        
        return df_va, df_ta, None
        
    except gspread.exceptions.APIError as e:
        error_msg = f"Google Sheets API Error: {str(e)}"
        st.error(f"❌ {error_msg}")
        st.info("💡 Make sure the sheet is shared with your service account email")
        return None, None, error_msg
    except gspread.exceptions.SpreadsheetNotFound:
        error_msg = "Spreadsheet not found or not accessible"
        st.error(f"❌ {error_msg}")
        st.info("💡 Check: 1) Sheet URL is correct, 2) Sheet is shared with service account")
        return None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        st.error(f"❌ {error_msg}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, error_msg

# Load data from Google Sheets (PRIMARY SOURCE - REAL-TIME)
va_df_gs, ta_df_gs, error = load_google_sheets_data()

if va_df_gs is not None and not va_df_gs.empty:
    # SUCCESS: Using Google Sheets (real-time data)
    va_df, ta_df = va_df_gs, ta_df_gs
    data_source = "Google Sheets ✅ (Real-time)"
else:
    # FALLBACK: Try Excel file as backup
    st.warning("⚠️ Google Sheets not available - trying Excel backup...")
    if error:
        st.error(f"Error details: {error}")
    va_df, ta_df = load_excel_data()
    data_source = "Excel File (Backup)"
    
    if va_df is None or va_df.empty:
        st.error("❌ No data available! Please check:")
        st.markdown("""
        1. **Google Sheets Setup:**
           - Credentials file: `valiant-splicer-409609-e34abed30cc1.json` in same folder
           - Sheet shared with service account email
           - Worksheet names: `ILM_Connector` and `ILM_Connector_TA`
        
        2. **Or Excel Backup:**
           - Place `ILM_Python_2.xlsx` in same folder
           
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

# SIMPLIFIED PNG EXPORT - Just PNG, no HTML
def create_download_button(fig, filename_base):
    """Create download button using HTML export (no kaleido needed)"""
    if fig is None:
        return
    
    try:
        # Export as HTML (works without kaleido)
        html_bytes = fig.to_html(
            include_plotlyjs='cdn',
            config={
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': filename_base,
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                },
                'displayModeBar': True,
                'displaylogo': False
            }
        ).encode()
        
        st.download_button(
            label="📥 Download HTML (Open in browser, use camera icon to save PNG)",
            data=html_bytes,
            file_name=f"{filename_base}.html",
            mime="text/html",
            key=f"html_{filename_base}"
        )
            
    except Exception as e:
        st.caption(f"⚠️ Export error: {str(e)}")

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
            # Count services for this RI and data representation
            mask = (df['compliant_ri'] == ri)
            if 'data_repr' in df.columns:
                mask = mask & (df['data_repr'].astype(str).str.contains(dr, na=False, case=False))
            
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
    st.markdown(f"<span class='small'>Home ▸ Dashboard ({data_source})</span>", unsafe_allow_html=True)
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
                if 'compliant_ri' in va_df.columns:
                    ri_counts = va_df['compliant_ri'].value_counts().to_dict()
                    ri_data = pd.DataFrame(list(ri_counts.items()), columns=['RI', 'Count']).sort_values('Count', ascending=False)
                    
                    # Create professional bar chart for RI
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
                    
                    st.plotly_chart(fig_ri, use_container_width=False)
                    create_download_button(fig_ri, "ri_distribution")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
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
                    
                    st.plotly_chart(fig_impl, use_container_width=False)
                    create_download_button(fig_impl, "implementation_status")
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
                    
                    st.plotly_chart(fig_repr, use_container_width=False)
                    create_download_button(fig_repr, "data_representations")
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
                    
                    st.plotly_chart(fig_license, use_container_width=False)
                    create_download_button(fig_license, "license_distribution")
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
                
                st.plotly_chart(fig_metadata, use_container_width=False)
                create_download_button(fig_metadata, "metadata_standards")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            # Implementation Matrix Heatmap (full width)
            st.markdown("## 📊 Implementation Matrix Analysis")
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if va_df is not None and not va_df.empty:
                try:
                    fig_heatmap = create_enhanced_heatmap(va_df)
                    if fig_heatmap:
                        st.pyplot(fig_heatmap, clear_figure=True, use_container_width=False)
                        
                        # Offer download
                        buf = io.BytesIO()
                        fig_heatmap.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                        buf.seek(0)
                        
                        st.download_button(
                            label="📥 Download Implementation Matrix (High-Res PNG)",
                            data=buf,
                            file_name="implementation_matrix_heatmap.png",
                            mime="image/png",
                            key="heatmap_download"
                        )
                        
                        st.caption("**Legend:** Large numbers in center = Total services | Green boxes with ✓ = Implemented services")
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
                    st.plotly_chart(fig_stage, use_container_width=True)
                    create_download_button(fig_stage, "project_stages")
            
            with col2:
                if 'call' in ta_df.columns:
                    call_counts = ta_df['call'].value_counts().to_dict()
                    call_data = pd.DataFrame(list(call_counts.items()), columns=['Call', 'Count']).sort_values('Call')
                    fig_calls = create_professional_bar_chart(call_data, 'Call', 'Count',
                                                              'Applications by Call',
                                                              orientation='v',
                                                              color_palette=COLORS['blue_palette'])
                    st.plotly_chart(fig_calls, use_container_width=True)
                    create_download_button(fig_calls, "applications_by_call")
        else:
            st.warning("No Transnational Access data available")

elif selected == "Analytics":
    st.markdown("<span class='small'>Home ▸ Analytics</span>", unsafe_allow_html=True)
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
                    st.plotly_chart(fig_running, use_container_width=False)
                    create_download_button(fig_running, "service_running")
                
            
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
                    st.plotly_chart(fig_api, use_container_width=False)
                    create_download_button(fig_api, "api_standards")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'metadata_standard' in va_df.columns:
                    meta_counts = va_df['metadata_standard'].value_counts().head(6).to_dict()
                    meta_data = pd.DataFrame(list(meta_counts.items()), columns=['Standard', 'Count']).sort_values('Count', ascending=False)
                    fig_meta = create_professional_pie_chart(meta_data, 'Standard', 'Count',
                                                            'Metadata Standards')
                    st.plotly_chart(fig_meta, use_container_width=False)
                    create_download_button(fig_meta, "metadata_standards")
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
                    st.plotly_chart(fig_param, use_container_width=False)
                    create_download_button(fig_param, "parametrization")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'license' in va_df.columns:
                    license_counts = va_df['license'].value_counts().head(6).to_dict()
                    license_data = pd.DataFrame(list(license_counts.items()), columns=['License', 'Count']).sort_values('Count', ascending=False)
                    fig_license = create_professional_pie_chart(license_data, 'License', 'Count',
                                                                'License Distribution')
                    st.plotly_chart(fig_license, use_container_width=False)
                    create_download_button(fig_license, "license_types")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'fully_described' in va_stats:
                    desc_data = pd.DataFrame(list(va_stats['fully_described'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_desc = create_professional_donut_chart(desc_data, 'Status', 'Count',
                                                              'Full Description Status',
                                                              color_map=color_map)
                    st.plotly_chart(fig_desc, use_container_width=False)
                    create_download_button(fig_desc, "fully_described")
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
                    st.plotly_chart(fig_doc, use_container_width=False)
                    create_download_button(fig_doc, "documentation")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'payloads' in va_stats:
                    payload_data = pd.DataFrame(list(va_stats['payloads'].items()), columns=['Status', 'Count'])
                    color_map = {'Yes': COLORS['yes'], 'No': COLORS['no'], 'N/A': COLORS['unknown']}
                    fig_payload = create_professional_donut_chart(payload_data, 'Status', 'Count',
                                                                 'Payload Support',
                                                                 color_map=color_map)
                    st.plotly_chart(fig_payload, use_container_width=False)
                    create_download_button(fig_payload, "payloads")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'auth' in va_stats:
                    auth_data = pd.DataFrame(list(va_stats['auth'].items()), columns=['Method', 'Count']).sort_values('Count', ascending=False)
                    fig_auth = create_professional_pie_chart(auth_data, 'Method', 'Count',
                                                            'Authentication Methods')
                    st.plotly_chart(fig_auth, use_container_width=False)
                    create_download_button(fig_auth, "authentication")
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
                    st.plotly_chart(fig_conv, use_container_width=False)
                    create_download_button(fig_conv, "converter")
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
                    st.plotly_chart(fig_gender, use_container_width=False)
                    create_download_button(fig_gender, "ta_gender_distribution")
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
                    st.plotly_chart(fig_host, use_container_width=False)
                    create_download_button(fig_host, "ta_host_distribution")
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
                    st.plotly_chart(fig_unit, use_container_width=False)
                    create_download_button(fig_unit, "ta_access_units")
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
                    st.plotly_chart(fig_users, use_container_width=False)
                    create_download_button(fig_users, "ta_number_of_users")
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
                    st.plotly_chart(fig_call_gender, use_container_width=False)
                    create_download_button(fig_call_gender, "ta_call_gender")
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
                    st.plotly_chart(fig_call_host, use_container_width=False)
                    create_download_button(fig_call_host, "ta_call_host")
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
                        
                        st.plotly_chart(fig_monthly, use_container_width=False)
                        create_download_button(fig_monthly, "ta_monthly_distribution")
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
                            
                            st.plotly_chart(fig_units, use_container_width=False)
                            create_download_button(fig_units, "ta_units_comparison")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 5: Geographic/Institutional
            st.markdown("### 🌍 Geographic and Institutional Analysis")
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
                    st.plotly_chart(fig_affil, use_container_width=False)
                    create_download_button(fig_affil, "ta_top_institutions")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                if 'associated_wp' in ta_df.columns:
                    wp_counts = ta_df['associated_wp'].value_counts().to_dict()
                    wp_data = pd.DataFrame(list(wp_counts.items()), columns=['Work Package', 'Count'])
                    fig_wp = create_professional_pie_chart(wp_data, 'Work Package', 'Count',
                                                           'Associated Work Packages')
                    st.plotly_chart(fig_wp, use_container_width=False)
                    create_download_button(fig_wp, "ta_work_packages")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No Transnational Access data available")

# TRANSNATIONAL ACCESS COMPREHENSIVE DASHBOARD (only when TA is selected)
elif selected == "Transnational Access":
    st.markdown("<span class='small'>Home ▸ Transnational Access Dashboard</span>", unsafe_allow_html=True)
    st.header("🌍 Transnational Access Comprehensive Dashboard")
    
    if ta_df is not None and not ta_df.empty:
        st.markdown("### 📊 TA Applications Status Overview")
        st.markdown("---")
        
        ta_display = ta_df.copy()
        
        if 'project_id' in ta_display.columns:
            ta_display['call_display'] = ta_display['call']
            ta_display['app_num'] = ta_display['application_number']
        
        # Main visualization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if 'call' in ta_display.columns and 'ta_host' in ta_display.columns and 'project_stage' in ta_display.columns:
                fig_status = px.sunburst(
                    ta_display,
                    path=['call', 'ta_host', 'project_stage'],
                    title='TA Applications: Hierarchical View (Call â†’ Host â†’ Status)',
                    color='project_stage',
                    color_discrete_map={
                        'Visit/access exhausted': COLORS['exhausted'],
                        'Time window for the visit/access fixed': COLORS['fixed'],
                        'Data/products ready': COLORS['ready'],
                        'PI contacted': COLORS['contacted'],
                        'Project details negotiated': COLORS['negotiated']
                    },
                    height=600
                )
                
                fig_status.update_layout(
                    font=dict(family=FONT_FAMILY, size=12),
                    title=dict(font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark'])),
                    margin=dict(l=20, r=20, t=80, b=20)
                )
                
                st.plotly_chart(fig_status, use_container_width=True)
                create_download_button(fig_status, "ta_status_sunburst")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 📊 Key Metrics")
            
            total_apps = len(ta_display)
            total_calls = ta_display['call'].nunique() if 'call' in ta_display.columns else 0
            total_hosts = ta_display['ta_host'].nunique() if 'ta_host' in ta_display.columns else 0
            
            st.metric("Total Applications", total_apps)
            st.metric("Number of Calls", total_calls)
            st.metric("TA Hosts", total_hosts)
            
            if 'project_stage' in ta_display.columns:
                st.markdown("#### 📊 Status Breakdown")
                status_counts = ta_display['project_stage'].value_counts()
                for status, count in status_counts.items():
                    percentage = (count / total_apps) * 100
                    st.caption(f"**{status}**: {count} ({percentage:.1f}%)")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Matrix views
        st.markdown("### 📊 Detailed Application Matrix")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if 'call' in ta_display.columns and 'ta_host' in ta_display.columns:
                call_host_matrix = ta_display.groupby(['call', 'ta_host']).size().reset_index(name='Applications')
                call_host_pivot = call_host_matrix.pivot(index='ta_host', columns='call', values='Applications').fillna(0)
                
                fig_matrix = go.Figure(data=go.Heatmap(
                    z=call_host_pivot.values,
                    x=call_host_pivot.columns,
                    y=call_host_pivot.index,
                    colorscale='Blues',
                    text=call_host_pivot.values,
                    texttemplate='%{text:.0f}',
                    textfont={"size": 12},
                    hoverongaps=False,
                    hovertemplate='<b>%{y}</b><br>%{x}<br>Applications: %{z}<extra></extra>'
                ))
                
                fig_matrix.update_layout(
                    title='Applications Matrix: TA Host vs Call',
                    xaxis_title='<b>Call</b>',
                    yaxis_title='<b>TA Host</b>',
                    font=dict(family=FONT_FAMILY, size=12),
                    title_font=dict(size=TITLE_FONT_SIZE, color=COLORS['dark']),
                    height=500,
                    margin=dict(l=150, r=20, t=80, b=80)
                )
                
                st.plotly_chart(fig_matrix, use_container_width=True)
                create_download_button(fig_matrix, "ta_call_host_matrix")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            if 'call' in ta_display.columns and 'project_stage' in ta_display.columns:
                call_status = ta_display.groupby(['call', 'project_stage']).size().reset_index(name='count')
                
                fig_call_status = px.bar(
                    call_status,
                    x='call',
                    y='count',
                    color='project_stage',
                    title='Application Status by Call',
                    labels={'count': 'Number of Applications', 'call': 'Call', 'project_stage': 'Status'},
                    color_discrete_map={
                        'Visit/access exhausted': COLORS['exhausted'],
                        'Time window for the visit/access fixed': COLORS['fixed'],
                        'Data/products ready': COLORS['ready'],
                        'PI contacted': COLORS['contacted'],
                        'Project details negotiated': COLORS['negotiated']
                    },
                    height=500
                )
                
                fig_call_status.update_layout(
                    font=dict(family=FONT_FAMILY, size=12),
                    title_font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY, color=COLORS['dark']),
                    xaxis=dict(title='Call', tickfont=dict(size=TICK_FONT_SIZE)),
                    yaxis=dict(title='Number of Applications', tickfont=dict(size=TICK_FONT_SIZE)),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(size=10)),
                    margin=dict(l=60, r=60, t=80, b=120)
                )
                
                st.plotly_chart(fig_call_status, use_container_width=True)
                create_download_button(fig_call_status, "ta_status_by_call")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Timeline
        st.markdown("### 📊 Application Timeline")
        
        if 'visit_start' in ta_display.columns and 'visit_end' in ta_display.columns:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            
            timeline_df = ta_display[ta_display['visit_start'].notna() | ta_display['visit_end'].notna()].copy()
            
            if not timeline_df.empty:
                fig_timeline = go.Figure()
                
                for idx, row in timeline_df.iterrows():
                    if pd.notna(row['visit_start']) and pd.notna(row['visit_end']):
                        try:
                            start = pd.to_datetime(row['visit_start'])
                            end = pd.to_datetime(row['visit_end'])
                            
                            status = row.get('project_stage', 'Unknown')
                            if 'exhausted' in str(status).lower():
                                color = COLORS['exhausted']
                            elif 'fixed' in str(status).lower():
                                color = COLORS['fixed']
                            elif 'ready' in str(status).lower():
                                color = COLORS['ready']
                            else:
                                color = COLORS['contacted']
                            
                            fig_timeline.add_trace(go.Scatter(
                                x=[start, end],
                                y=[row.get('project_id', idx), row.get('project_id', idx)],
                                mode='lines+markers',
                                line=dict(color=color, width=10),
                                marker=dict(size=8),
                                name=row.get('ta_host', 'Unknown'),
                                hovertemplate=f"<b>{row.get('project_id', 'N/A')}</b><br>" +
                                            f"Host: {row.get('ta_host', 'N/A')}<br>" +
                                            f"Status: {status}<br>" +
                                            f"Start: {start.strftime('%Y-%m-%d')}<br>" +
                                            f"End: {end.strftime('%Y-%m-%d')}<extra></extra>",
                                showlegend=False
                            ))
                        except:
                            pass
                
                fig_timeline.update_layout(
                    title='TA Visit Timeline',
                    xaxis_title='<b>Date</b>',
                    yaxis_title='<b>Project ID</b>',
                    font=dict(family=FONT_FAMILY, size=11),
                    title_font=dict(size=TITLE_FONT_SIZE, color=COLORS['dark']),
                    height=max(400, len(timeline_df) * 25),
                    margin=dict(l=120, r=20, t=80, b=60),
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_timeline, use_container_width=True)
                create_download_button(fig_timeline, "ta_timeline")
            else:
                st.info("No timeline data available with valid start/end dates")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed table
        st.markdown("### 📊 Detailed Application Information")
        
        display_cols = ['project_id', 'installation_id', 'call', 'application_number', 'ta_host', 
                       'project_stage', 'pi_gender', 'unit_of_access', 'number_of_users']
        display_cols = [col for col in display_cols if col in ta_display.columns]
        
        if display_cols:
            display_table = ta_display[display_cols].copy()
            
            column_names = {
                'project_id': 'Project ID',
                'installation_id': 'Installation',
                'call': 'Call',
                'application_number': 'App #',
                'ta_host': 'TA Host',
                'project_stage': 'Status',
                'pi_gender': 'PI Gender',
                'unit_of_access': 'Access Unit',
                'number_of_users': 'Users'
            }
            display_table = display_table.rename(columns=column_names)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'Call' in display_table.columns:
                    calls = ['All'] + sorted(display_table['Call'].unique().tolist())
                    selected_call = st.selectbox('Filter by Call', calls)
            
            with col2:
                if 'TA Host' in display_table.columns:
                    hosts = ['All'] + sorted(display_table['TA Host'].unique().tolist())
                    selected_host = st.selectbox('Filter by TA Host', hosts)
            
            with col3:
                if 'Status' in display_table.columns:
                    statuses = ['All'] + sorted(display_table['Status'].unique().tolist())
                    selected_status = st.selectbox('Filter by Status', statuses)
            
            # Apply filters
            filtered_table = display_table.copy()
            if selected_call != 'All' and 'Call' in filtered_table.columns:
                filtered_table = filtered_table[filtered_table['Call'] == selected_call]
            if selected_host != 'All' and 'TA Host' in filtered_table.columns:
                filtered_table = filtered_table[filtered_table['TA Host'] == selected_host]
            if selected_status != 'All' and 'Status' in filtered_table.columns:
                filtered_table = filtered_table[filtered_table['Status'] == selected_status]
            
            st.dataframe(filtered_table, use_container_width=True, height=400)
            
            csv = filtered_table.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Filtered Data (CSV)",
                data=csv,
                file_name="ta_applications_filtered.csv",
                mime="text/csv",
            )
    else:
        st.warning("No Transnational Access data available")


# ===============================================================================================
# =================================== KPI SECTION (UNDER DEVELOPMENT) ==========================
# ===============================================================================================


# ===============================================================================================
# =================================== KPI SECTION ==============================================
# ===============================================================================================
# This section provides Key Performance Indicators for both Virtual Access and
# Transnational Access projects. KPIs track usage, datasets, and performance metrics.
# ===============================================================================================

if selected == "KPI":
    st.title("🎯 Key Performance Indicators (KPI)")
    st.markdown("---")
    
    if project_label == "Virtual Access":
        # ==================== VIRTUAL ACCESS KPI - FULL IMPLEMENTATION ====================
        st.header("📊 Virtual Access KPIs")
        
        # Load raw data to access KPI columns by index
        try:
            # Use Google Sheets via Streamlit secrets (works on cloud) or local JSON
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Try Streamlit Cloud secrets first, then fall back to local JSON file
            if "gcp_service_account" in st.secrets:
                # Running on Streamlit Cloud - use secrets
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            else:
                # Running locally - use JSON file
                json_keyfile_path = "valiant-splicer-409609-e34abed30cc1.json"
                if not os.path.exists(json_keyfile_path):
                    st.error("❌ Credentials not found. Cannot load KPI data.")
                    raise Exception("Credentials missing")
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            
            client = gspread.authorize(creds)
            sheet_url = "https://docs.google.com/spreadsheets/d/1noNhzwKOp1_t9RfgJc__zvXs-23t_BofigcZBjTnADM/edit?gid=1373546546#gid=1373546546"
            spreadsheet = client.open_by_url(sheet_url)
            worksheet_va = spreadsheet.worksheet("ILM_Connector")
            data_va = worksheet_va.get_all_values()
            df_raw = pd.DataFrame(data_va[4:], columns=data_va[3])
            
            # ==================== KPI 1: USAGE LOGGING SYSTEM ====================
            # Column 35 (AJ): Does your installation have Usage Logging system in place?
            col_35 = df_raw.iloc[:, 35]  # Usage Logging (yes/no)
            
            st.subheader("🔍 KPI-1: Usage Logging System")
            st.caption("Tracks installations with active usage logging capabilities")
            
            # Calculate usage logging statistics
            usage_logging_counts = col_35.value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Display metrics
                total_installations = len(col_35.dropna())
                yes_count = usage_logging_counts.get('YES', 0) + usage_logging_counts.get('yes', 0) + usage_logging_counts.get('Yes', 0)
                no_count = usage_logging_counts.get('NO', 0) + usage_logging_counts.get('no', 0) + usage_logging_counts.get('No', 0)
                
                st.metric("Total Installations", total_installations)
                st.metric("With Usage Logging", yes_count, 
                         delta=f"{yes_count/total_installations*100:.1f}%" if total_installations > 0 else "N/A")
                st.metric("Without Usage Logging", no_count)
            
            with col2:
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['With Logging', 'Without Logging'],
                    values=[yes_count, no_count],
                    hole=0.4,
                    marker=dict(colors=[COLORS['success'], COLORS['danger']]),
                    textfont=dict(size=14, family=FONT_FAMILY)
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
            
            # ==================== KPI 2: NUMBER OF USERS SERVED ====================
            # Column 37 (AL): Number of users served
            st.markdown("---")
            st.subheader("👥 KPI-3: Number of Users Served")
            st.caption("Distribution of users across all installations")
            
            col_37 = df_raw.iloc[:, 37]  # Number of users served
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate user statistics
                users_served = pd.to_numeric(col_37, errors='coerce').dropna()
                
                if len(users_served) > 0:
                    st.metric("Total Users Served", f"{int(users_served.sum()):,}")
                    st.metric("Average per Installation", f"{users_served.mean():.0f}")
                    st.metric("Median Users", f"{users_served.median():.0f}")
                    st.metric("Max Users (Single Installation)", f"{int(users_served.max()):,}")
                else:
                    st.info("No user data available")
            
            with col2:
                # Create histogram
                if len(users_served) > 0:
                    fig = go.Figure(data=[go.Histogram(
                        x=users_served,
                        nbinsx=20,
                        marker=dict(color=COLORS['accent'], line=dict(color='white', width=1)),
                        name='Installations'
                    )])
                    
                    fig.update_layout(
                        title=dict(
                            text="<b>Distribution of Users Served</b>",
                            font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                        ),
                        xaxis_title="<b>Number of Users</b>",
                        yaxis_title="<b>Number of Installations</b>",
                        height=400,
                        showlegend=False,
                        font=dict(family=FONT_FAMILY)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # ==================== KPI 3: DATASETS - START VS NEW ====================
            # Columns: AN (39), AO (40), AQ (42), AR (43)
            st.markdown("---")
            st.subheader("📚 Accessible Datasets and New Datasets")
            st.caption("Comparison of datasets at project start versus new datasets added")
            
            # Extract dataset columns
            col_39 = df_raw.iloc[:, 39]  # Datasets at start
            col_40 = df_raw.iloc[:, 40]  # Volume at start
            col_42 = df_raw.iloc[:, 42]  # New datasets
            col_43 = df_raw.iloc[:, 43]  # New volume
            
            # Convert to numeric
            datasets_at_start = pd.to_numeric(col_39, errors='coerce').dropna()
            volume_at_start = pd.to_numeric(col_40, errors='coerce').dropna()
            new_datasets = pd.to_numeric(col_42, errors='coerce').dropna()
            new_volume = pd.to_numeric(col_43, errors='coerce').dropna()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Display metrics
                st.markdown("**At Project Start:**")
                st.metric("Total Datasets", f"{int(datasets_at_start.sum()):,}" if len(datasets_at_start) > 0 else "N/A")
                st.metric("Total Volume (TB)", f"{volume_at_start.sum():.2f}" if len(volume_at_start) > 0 else "N/A")
                
                st.markdown("**New Datasets:**")
                st.metric("New Datasets Added", f"{int(new_datasets.sum()):,}" if len(new_datasets) > 0 else "N/A")
                st.metric("New Volume (TB)", f"{new_volume.sum():.2f}" if len(new_volume) > 0 else "N/A")
            
            with col2:
                # Create grouped bar chart
                if len(datasets_at_start) > 0 or len(new_datasets) > 0:
                    fig = go.Figure()
                    
                    # Add bars for datasets at start
                    fig.add_trace(go.Bar(
                        name='Datasets at Start',
                        x=['Count', 'Volume (TB)'],
                        y=[datasets_at_start.sum() if len(datasets_at_start) > 0 else 0, 
                           volume_at_start.sum() if len(volume_at_start) > 0 else 0],
                        marker=dict(color=COLORS['blue_palette'][0]),
                        text=[f"{int(datasets_at_start.sum()):,}" if len(datasets_at_start) > 0 else "0", 
                              f"{volume_at_start.sum():.2f}" if len(volume_at_start) > 0 else "0"],
                        textposition='auto',
                        textfont=dict(size=12, family=FONT_FAMILY)
                    ))
                    
                    # Add bars for new datasets
                    fig.add_trace(go.Bar(
                        name='New Datasets',
                        x=['Count', 'Volume (TB)'],
                        y=[new_datasets.sum() if len(new_datasets) > 0 else 0, 
                           new_volume.sum() if len(new_volume) > 0 else 0],
                        marker=dict(color=COLORS['success']),
                        text=[f"{int(new_datasets.sum()):,}" if len(new_datasets) > 0 else "0", 
                              f"{new_volume.sum():.2f}" if len(new_volume) > 0 else "0"],
                        textposition='auto',
                        textfont=dict(size=12, family=FONT_FAMILY)
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text="<b>Datasets: Start vs New</b>",
                            font=dict(size=TITLE_FONT_SIZE, family=FONT_FAMILY)
                        ),
                        xaxis_title="<b>Metric Type</b>",
                        yaxis_title="<b>Value</b>",
                        barmode='group',
                        height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        font=dict(family=FONT_FAMILY)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # ==================== DETAILED KPI SUMMARY TABLE ====================
            st.markdown("---")
            st.subheader("📋 Detailed KPI Summary")
            
            # Create summary dataframe
            kpi_summary = pd.DataFrame({
                'Metric': [
                    'Installations with Usage Logging',
                    'Total Users Served',
                    'Datasets at Start',
                    'Volume at Start (TB)',
                    'New Datasets',
                    'New Volume (TB)',
                    'Total Datasets',
                    'Total Volume (TB)'
                ],
                'Value': [
                    f"{yes_count} / {total_installations} ({yes_count/total_installations*100:.1f}%)" if total_installations > 0 else "N/A",
                    f"{int(users_served.sum()):,}" if len(users_served) > 0 else "N/A",
                    f"{int(datasets_at_start.sum()):,}" if len(datasets_at_start) > 0 else "N/A",
                    f"{volume_at_start.sum():.2f}" if len(volume_at_start) > 0 else "N/A",
                    f"{int(new_datasets.sum()):,}" if len(new_datasets) > 0 else "N/A",
                    f"{new_volume.sum():.2f}" if len(new_volume) > 0 else "N/A",
                    f"{int(datasets_at_start.sum() + new_datasets.sum()):,}" if (len(datasets_at_start) > 0 and len(new_datasets) > 0) else "N/A",
                    f"{volume_at_start.sum() + new_volume.sum():.2f}" if (len(volume_at_start) > 0 and len(new_volume) > 0) else "N/A"
                ]
            })
            
            st.dataframe(kpi_summary, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"Error loading KPI data: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    else:  # Transnational Access
        # ==================== TRANSNATIONAL ACCESS KPI - UNDER DEVELOPMENT ====================
        st.info("🚧 This section is currently under development. KPI metrics and visualizations will be available soon.")
        
        # Show preview of coming features
        st.subheader("Coming Soon:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #3498DB;">
                <h4>📊 Project Metrics</h4>
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
                <h4>👥 User Metrics</h4>
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
                <h4>📈 Outcomes</h4>
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
# This section displays raw data tables for both Virtual Access and Transnational Access
# Users can view and download the complete datasets as CSV files
# ===============================================================================================

elif selected == "Data":
    st.markdown("<span class='small'>Home ▸ Data</span>", unsafe_allow_html=True)
    st.header("Data Table")
    
    if project_label == "Virtual Access":
        # Display Virtual Access data table
        if va_df is not None and not va_df.empty:
            # Fix any duplicate column names before display
            va_df_display = va_df.copy()
            cols = pd.Series(va_df_display.columns)
            for dup in cols[cols.duplicated()].unique():
                dup_indices = [i for i, x in enumerate(cols) if x == dup]
                for i, idx in enumerate(dup_indices[1:], start=1):
                    cols[idx] = f"{dup}_{i}"
            va_df_display.columns = cols
            
            st.caption(f"**Virtual Access Data** - {len(va_df_display)} records")
            st.dataframe(va_df_display, use_container_width=True)
            
            # Provide CSV download button (using cleaned dataframe)
            st.download_button(
                "📊 Download CSV", 
                data=va_df_display.to_csv(index=False).encode("utf-8"),
                file_name="VA_data.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No Virtual Access data available")
    else:
        # Display Transnational Access data table
        if ta_df is not None and not ta_df.empty:
            st.caption(f"**Transnational Access Data** - {len(ta_df)} records")
            st.dataframe(ta_df, use_container_width=True)
            
            # Provide CSV download button
            st.download_button(
                "📊 Download CSV", 
                data=ta_df.to_csv(index=False).encode("utf-8"),
                file_name="TA_data.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No Transnational Access data available")


elif selected == "Contact":
    st.markdown("<span class='small'>Home ▸ Contact</span>", unsafe_allow_html=True)
    st.header("Contact")
    st.write("• Conception: Jan Michalek and Juliano Ramanantsoa")
    st.write("• Reach out: heriniaina.j.ramanantsoa@uib.no")

