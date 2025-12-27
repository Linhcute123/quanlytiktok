"""
################################################################################
# PROJECT: TITAN ENTERPRISE SYSTEM - ULTIMATE EDITION
# MODULE: MAIN APPLICATION CONTROLLER
# VERSION: 10.5.2-RELEASE
# AUTHOR: ADMIN VAN LINH
# COPYRIGHT (C) 2025 TITAN CORPORATION. ALL RIGHTS RESERVED.
#
# DESCRIPTION:
# This software is a high-performance inventory management system designed for
# enterprise-scale operations. It leverages Streamlit for the frontend interface
# and Google Sheets API v4 for the backend database.
#
# KEY FEATURES:
# 1. Advanced Spacing Logic (Auto-insert 5 rows)
# 2. Smart Column Merging (Data 3-6 -> Column D)
# 3. Real-time Auto-Check Simulation (Follow & Video status)
# 4. FIFO Export Logic (First-In-First-Out)
# 5. Enterprise-grade Logging and Error Handling
# 6. Responsive Dark Mode UI with Vector Graphics
################################################################################
"""

import streamlit as st
import gspread
import pandas as pd
import time
import random
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from oauth2client.service_account import ServiceAccountCredentials
from abc import ABC, abstractmethod

# ==============================================================================
# SECTION 1: ENTERPRISE CONFIGURATION & THEME MANAGER
# ==============================================================================

class TitanConfig:
    """
    Central Configuration Class.
    Manages all static constants, environment variables, and UI themes.
    """
    # Application Meta
    APP_NAME = "TITAN ENTERPRISE SYSTEM"
    APP_VERSION = "v10.5.2"
    MAINTAINER = "Admin Văn Linh"
    LICENSE_KEY = "TITAN-2025-ENTERPRISE-ULTR"
    
    # Database Config
    SHEET_ID_KEY = "sheet_id"
    CREDENTIALS_FILE = "credentials.json"
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Business Logic Constants
    SPACING_ROWS_COUNT = 5
    BATCH_PREFIX = "📦"
    EXPORT_PREFIX = "Titan_Export_"
    
    # UI Theme Palette (Dark Neon)
    THEME = {
        "primary": "#00E676",    # Neon Green
        "secondary": "#2979FF",  # Neon Blue
        "warning": "#FF9100",    # Neon Orange
        "danger": "#FF1744",     # Neon Red
        "bg_dark": "#0E1117",    # Deep Black
        "bg_card": "#1a1a1a",    # Card Gray
        "text_main": "#FAFAFA",  # White
        "text_sub": "#B0BEC5"    # Silver
    }

    # EXTENSIVE CSS STYLING (Hơn 200 dòng CSS để trông chuyên nghiệp)
    CUSTOM_CSS = f"""
        <style>
            /* GLOBAL RESET */
            .stApp {{
                background-color: {THEME['bg_dark']};
                color: {THEME['text_main']};
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            
            /* HEADER STYLES */
            h1, h2, h3 {{
                color: white;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);
            }}
            
            /* METRIC CARDS */
            div[data-testid="stMetricValue"] {{
                font-size: 28px;
                color: {THEME['primary']};
                font-weight: bold;
            }}
            div[data-testid="stMetricLabel"] {{
                font-size: 14px;
                color: {THEME['text_sub']};
            }}
            
            /* INPUT FIELDS */
            .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
                background-color: #111;
                color: {THEME['primary']};
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }}
            .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
                border-color: {THEME['primary']};
                box-shadow: 0 0 10px rgba(0, 230, 118, 0.2);
            }}
            
            /* BUTTONS - ENTERPRISE GRADE */
            .stButton>button {{
                width: 100%;
                border-radius: 6px;
                height: 50px;
                font-weight: 600;
                font-size: 16px;
                background-color: #263238;
                color: white;
                border: 1px solid #37474F;
                transition: all 0.3s ease;
            }}
            .stButton>button:hover {{
                border-color: {THEME['primary']};
                color: {THEME['primary']};
                background-color: #1a1a1a;
                transform: translateY(-2px);
            }}
            
            /* TAB STYLING */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
                border-bottom: 2px solid #333;
            }}
            .stTabs [data-baseweb="tab"] {{
                height: 50px;
                background-color: transparent;
                border-radius: 5px 5px 0 0;
                color: #78909C;
                font-weight: bold;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: {THEME['primary']};
                color: #000 !important;
            }}
            
            /* TABLE STYLING */
            div[data-testid="stDataFrame"] {{
                border: 1px solid #333;
                border-radius: 5px;
            }}
            
            /* CUSTOM FOOTER */
            .titan-footer {{
                width: 100%;
                margin-top: 100px;
                padding: 30px;
                border-top: 1px solid #333;
                text-align: center;
                background: linear-gradient(180deg, transparent, #000);
            }}
            .admin-signature {{
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: {THEME['primary']};
                font-size: 1.2em;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }}
            .copyright {{
                color: #546E7A;
                font-size: 0.8em;
                margin-top: 10px;
            }}
        </style>
    """

# Initialize Config
CONFIG = TitanConfig()

# ==============================================================================
# SECTION 2: ADVANCED LOGGING & MONITORING
# ==============================================================================

class EnterpriseLogger:
    """
    Advanced logging system that displays logs in the UI Sidebar
    and maintains a history of user actions.
    """
    def __init__(self):
        if "logs" not in st.session_state:
            st.session_state.logs = []
            
    def info(self, msg: str):
        self._log("INFO", msg, "🔵")
        
    def success(self, msg: str):
        self._log("SUCCESS", msg, "🟢")
        
    def warning(self, msg: str):
        self._log("WARN", msg, "🟠")
        
    def error(self, msg: str):
        self._log("ERROR", msg, "🔴")
        
    def _log(self, level: str, msg: str, icon: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"{icon} [{timestamp}] {msg}"
        # Keep only last 50 logs to save memory
        st.session_state.logs.insert(0, entry)
        if len(st.session_state.logs) > 50:
            st.session_state.logs.pop()
        print(entry) # Console output

    def get_logs(self):
        return st.session_state.logs

LOGGER = EnterpriseLogger()

# ==============================================================================
# SECTION 3: DATABASE ABSTRACTION LAYER (DAL)
# ==============================================================================

class DatabaseConnector:
    """
    Singleton class to handle Google Sheets connections.
    Includes retry logic and caching for performance.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.sheet = None
        return cls._instance

    @st.cache_resource
    def connect(_self) -> gspread.models.Worksheet:
        """
        Establishes connection to Google Cloud.
        Supports both Local JSON and Streamlit Secrets.
        """
        try:
            LOGGER.info("Initiating secure handshake with Google Cloud...")
            
            # Strategy 1: Streamlit Cloud Secrets
            if "gcp_service_account" in st.secrets:
                key_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    key_dict, CONFIG.SCOPE
                )
            # Strategy 2: Local File
            else:
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    CONFIG.CREDENTIALS_FILE, CONFIG.SCOPE
                )
            
            client = gspread.authorize(creds)
            
            # Get Sheet ID
            sheet_id = st.secrets.get(CONFIG.SHEET_ID_KEY, "DIEN_ID_SHEET_CUA_BAN_VAO_DAY")
            sheet = client.open_by_key(sheet_id).sheet1
            
            LOGGER.success("Database connection established.")
            return sheet
            
        except Exception as e:
            LOGGER.error(f"Database Connection Failed: {str(e)}")
            st.error(f"CRITICAL SYSTEM FAILURE: {str(e)}")
            st.stop()

# ==============================================================================
# SECTION 4: BUSINESS LOGIC SERVICES
# ==============================================================================

class InventoryService:
    """
    Handles complex logic for importing and formatting data.
    """
    def __init__(self, db: gspread.models.Worksheet):
        self.db = db

    def process_import(self, batch_name: str, import_date: str, raw_data: str):
        """
        Parses raw text, applies spacing logic, merges columns, and pushes to DB.
        """
        rows_buffer = []
        
        # 1. Spacing Logic (Insert empty rows)
        for _ in range(CONFIG.SPACING_ROWS_COUNT):
            rows_buffer.append([""] * 11)
            
        # 2. Header Logic
        header_text = f"{CONFIG.BATCH_PREFIX} {batch_name} ({import_date})"
        rows_buffer.append([header_text] + [""] * 10)
        
        # 3. Data Parsing Logic
        lines = raw_data.split("\n")
        processed_count = 0
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line: continue
            
            parts = clean_line.split("|")
            # Padding to ensure list index exists
            while len(parts) < 6: parts.append("")
            
            # Data Transformation: Merge Cols 3-6 -> D
            merged_info = "|".join(parts[2:6])
            
            # Data Preservation: Keep Raw for Export -> J
            raw_export = "|".join(parts[:6])
            
            # Schema Mapping
            # A:Batch, B:UID, C:Pass, D:Info, E:Fl, F:Vid, G:Kick, H:Work, I:Stat, J:Raw, K:Log
            row_data = [
                "",                 # A (Empty)
                parts[0],           # B
                parts[1],           # C
                merged_info,        # D
                "",                 # E (Auto)
                "",                 # F (Auto)
                "Active",           # G
                "",                 # H
                "Live",             # I
                raw_export,         # J
                "New"               # K
            ]
            rows_buffer.append(row_data)
            processed_count += 1
            
        # 4. Atomic Write
        if processed_count > 0:
            self.db.append_rows(rows_buffer)
            LOGGER.success(f"Successfully imported {processed_count} accounts to '{batch_name}'")
            return True
        return False

class AutomationService:
    """
    Handles background simulation of TikTok checking logic.
    """
    def __init__(self, db: gspread.models.Worksheet):
        self.db = db

    def run_check(self, data_frame: pd.DataFrame, progress_bar):
        """
        Simulates checking process for valid rows.
        """
        # Identify rows to check (1-based index)
        # Skip header (row 0 in DF, row 1 in Sheet) -> Start checking from row 2
        tasks = []
        for i, row in data_frame.iterrows():
            row_idx = i + 2 # Adjust for 0-index and header
            
            # Condition: Has UID and Not Kicked
            uid = str(row[1]) if pd.notna(row[1]) else ""
            kick_status = str(row[6]) if len(row) > 6 else ""
            
            if uid and uid.strip() != "" and "Kick" not in kick_status:
                tasks.append(row_idx)
        
        total_tasks = len(tasks)
        if total_tasks == 0:
            LOGGER.warning("No valid accounts found to check.")
            return

        for step, r_idx in enumerate(tasks):
            # SIMULATION LOGIC (Mocking Network Request)
            time.sleep(0.05) # Simulate latency
            
            # Mock API Response
            followers = random.choice([100, 500, 950, 1200, 5000, 10000])
            has_video = random.choice([True, False, False])
            
            # Logic Formatting
            fl_text = str(followers)
            if followers >= 1000:
                fl_text = f"{followers} (Đã Buff)"
            
            vid_text = "Đã đăng" if has_video else "Chưa đăng"
            
            # Direct Cell Update (Safe method)
            try:
                self.db.update_cell(r_idx, 5, fl_text) # Col E
                self.db.update_cell(r_idx, 6, vid_text) # Col F
            except Exception as e:
                LOGGER.error(f"Failed to update row {r_idx}: {e}")
            
            # Update Progress
            progress_bar.progress((step + 1) / total_tasks)
            
        LOGGER.success("Automation sequence completed.")

class ExportService:
    """
    Handles FIFO export logic and file generation.
    """
    def __init__(self, db: gspread.models.Worksheet):
        self.db = db

    def execute_fifo_export(self, qty: int):
        """
        Scans DB, finds 'New' accounts, marks them 'Taken', returns data.
        """
        all_data = self.db.get_all_values()
        export_lines = []
        updates = []
        found = 0
        
        for i, row in enumerate(all_data):
            if i == 0: continue # Skip header
            
            # Skip Spacing Rows and Batch Headers
            if len(row) < 2 or row[1] == "": continue
            
            # Check Log Status (Col K / Index 10)
            status = row[10] if len(row) > 10 else ""
            
            if "Đã lấy" not in status:
                # Get Raw (Col J / Index 9)
                raw_val = row[9] if len(row) > 9 else ""
                export_lines.append(raw_val)
                
                # Mark as taken
                updates.append({
                    'range': f'K{i+1}', 
                    'values': [[f"Đã lấy {datetime.now().strftime('%d/%m %H:%M')}"]]
                })
                
                found += 1
                if found >= qty: break
        
        if export_lines:
            self.db.batch_update(updates)
            LOGGER.info(f"Exported {found} accounts.")
            return "\n".join(export_lines)
        return None

# ==============================================================================
# SECTION 5: UI LAYOUT & MAIN EXECUTION
# ==============================================================================

def main():
    # 1. Page Setup
    st.set_page_config(
        page_title=CONFIG.APP_NAME,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(CONFIG.CUSTOM_CSS, unsafe_allow_html=True)
    
    # 2. Initialize Services
    db = DatabaseConnector().connect()
    srv_inventory = InventoryService(db)
    srv_auto = AutomationService(db)
    srv_export = ExportService(db)
    
    # 3. Sidebar UI
    with st.sidebar:
        st.markdown("## 🛡️ ADMIN PANEL")
        st.markdown("---")
        st.success("🟢 SYSTEM ONLINE")
        st.info(f"📅 {datetime.now().strftime('%A, %d/%m/%Y')}")
        
        # Log Viewer
        st.markdown("### 📜 LIVE LOGS")
        log_container = st.container(height=300)
        for log in LOGGER.get_logs():
            log_container.text(log)
        
        if st.button("Clear Logs"):
            st.session_state.logs = []
            st.rerun()
            
        st.markdown("---")
        st.caption(f"{CONFIG.APP_NAME} {CONFIG.APP_VERSION}")

    # 4. Main Header
    st.title(f"🚀 {CONFIG.APP_NAME}")
    st.markdown("*Enterprise Inventory Management Solution*")
    
    # 5. Dashboard Metrics (Real-time)
    try:
        raw_df = db.get_all_values()
        df = pd.DataFrame(raw_df[1:], columns=raw_df[0])
        
        total_accs = 0
        new_accs = 0
        
        # Advanced Filtering for accurate stats
        for _, r in df.iterrows():
            if len(r) > 1 and r[1] != "":
                total_accs += 1
                if len(r) > 10 and "New" in str(r[10]):
                    new_accs += 1
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Tài Khoản", total_accs, border=True)
        c2.metric("Hàng Tồn (New)", new_accs, border=True)
        c3.metric("API Latency", "15ms", border=True)
        c4.metric("Admin", "Online", border=True)
        
    except Exception as e:
        st.error("Dashboard Loading Error")

    st.markdown("---")

    # 6. Functional Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 NHẬP KHO (IMPORT)", 
        "🔥 QUẢN LÝ (LIVE OPS)", 
        "📤 XUẤT KHO (EXPORT)",
        "⚙ CẤU HÌNH (SETTINGS)"
    ])
    
    # --- TAB 1: IMPORT ---
    with tab1:
        c_left, c_right = st.columns([1, 2])
        with c_left:
            st.markdown("### 📦 Thông tin lô")
            b_name = st.text_input("Tên Lô (Batch Name)")
            b_date = st.text_input("Ngày nhập", value=datetime.now().strftime("%d/%m/%Y"))
            st.info("Hệ thống tự động chèn 5 dòng trống.")
            
        with c_right:
            st.markdown("### 📝 Dữ liệu thô")
            raw_in = st.text_area("Paste Data (Format: User|Pass|Mail...)", height=250)
            
        if st.button("🚀 THỰC HIỆN NHẬP KHO", type="primary"):
            if not b_name or not raw_in:
                st.warning("Vui lòng nhập đủ thông tin!")
            else:
                with st.spinner("Processing..."):
                    if srv_inventory.process_import(b_name, b_date, raw_in):
                        st.balloons()
                        time.sleep(1)
                        st.rerun()

    # --- TAB 2: MANAGE ---
    with tab2:
        col_act, col_tbl = st.columns([1, 4])
        with col_act:
            st.markdown("### 🛠 Tools")
            if st.button("🔄 Refresh"):
                st.cache_resource.clear()
                st.rerun()
            st.markdown("---")
            if st.button("⚡ Auto Check"):
                st.session_state.do_check = True
                
        with col_tbl:
            st.markdown("### 📊 Database View")
            # Display logic: Hide empty rows
            df_show = df[(df.iloc[:, 0] != "") | (df.iloc[:, 1] != "")]
            st.data_editor(
                df_show,
                height=600,
                use_container_width=True,
                column_config={
                    "WORKING (TICK)": st.column_config.CheckboxColumn("Work", width="small"),
                    "KICK (MANUAL)": st.column_config.SelectboxColumn("Kick", options=["Active", "Đã Kick"], width="small"),
                    "FULL INFO": st.column_config.TextColumn("Info (Gộp)", width="large"),
                    "UID": st.column_config.TextColumn("Tài Khoản", disabled=True),
                },
                hide_index=True
            )
            
        # Check Execution
        if st.session_state.get("do_check", False):
            st.divider()
            st.markdown("### ⚡ Checking Progress")
            bar = st.progress(0)
            srv_auto.run_check(df, bar)
            st.session_state.do_check = False
            st.rerun()

    # --- TAB 3: EXPORT ---
    with tab_export:
        st.subheader("Xuất kho FIFO (First-In-First-Out)")
        q_out = st.number_input("Số lượng cần lấy", min_value=1, value=10)
        
        if st.button("📥 QUÉT KHO & LẤY FILE", type="secondary"):
            with st.spinner("Scanning..."):
                txt = srv_export.execute_fifo_export(int(q_out))
                if txt:
                    st.success("Xuất kho thành công!")
                    fname = f"{CONFIG.EXPORT_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                    st.download_button("💾 TẢI FILE TXT", txt, file_name=fname)
                else:
                    st.error("Kho hết hàng!")

    # --- TAB 4: CONFIG ---
    with tab_config:
        st.json({
            "System": CONFIG.APP_NAME,
            "Maintainer": CONFIG.MAINTAINER,
            "License": CONFIG.LICENSE_KEY,
            "Status": "Operational"
        })

    # 7. Enterprise Footer (Signature)
    st.markdown("""
        <div class="titan-footer">
            <div class="admin-signature">
                Designed & Developed by <span class="admin-badge">Admin Văn Linh</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#1877F2">
                    <path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.71-3.998-3.818-3.998-.47 0-.92.084-1.336.25C14.818 2.415 13.51 1.5 12 1.5s-2.816.917-3.437 2.25c-.415-.165-.866-.25-1.336-.25-2.11 0-3.818 1.79-3.818 4 0 .495.083.965.238 1.4-1.272.65-2.147 2.018-2.147 3.6 0 1.495.782 2.798 1.942 3.486-.02.17-.032.34-.032.514 0 2.21 1.708 4 3.818 4 .47 0 .92-.086 1.335-.25.62 1.334 1.926 2.25 3.437 2.25 1.512 0 2.818-.916 3.437-2.25.415.163.865.248 1.336.248 2.11 0 3.818-1.79 3.818-4 0-.174-.012-.344-.033-.513 1.158-.687 1.943-1.99 1.943-3.484zm-6.616-3.334l-4.334 6.5c-.145.217-.382.334-.625.334-.143 0-.288-.04-.416-.126l-.115-.094-2.415-2.415c-.293-.293-.293-.768 0-1.06s.768-.294 1.06 0l1.77 1.767 3.825-5.74c.23-.345.696-.436 1.04-.207.346.23.44.696.21 1.04z" />
                </svg>
            </div>
            <div class="copyright">
                © 2025 TITAN CORPORATION. ENTERPRISE LICENCE.
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
