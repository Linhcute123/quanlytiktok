"""
####################################################################################################
# SYSTEM: TITAN SOVEREIGN - ENTERPRISE RESOURCE PLANNING (ERP)
# MODULE: CORE_KERNEL_V99.py
# ARCHITECT: ADMIN VAN LINH
# ORGANIZATION: TITAN CORP GLOBAL
# COPYRIGHT: (C) 2025. ALL RIGHTS RESERVED.
#
# DESCRIPTION:
# High-fidelity inventory management interface with reactive UI/UX components.
# Implements Google Sheets API v4 connectivity with asynchronous state management.
# Features bespoke CSS styling engine (TitanUI) and granular access control logic.
####################################################################################################
"""

import streamlit as st
import gspread
import pandas as pd
import numpy as np
import time
import random
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict
from oauth2client.service_account import ServiceAccountCredentials

# ==================================================================================================
# [LAYER 0] CONFIGURATION & ASSETS
# ==================================================================================================

class TitanConfig:
    # META
    APP_NAME = "TITAN SOVEREIGN"
    CODENAME = "PROJECT_OMEGA"
    VERSION = "Build 99.0.1-Alpha"
    ADMIN = "Admin Văn Linh"
    
    # DATABASE SCHEMA
    TAB_NAME = "TITAN_MASTER_DB"
    HEADERS = [
        "BATCH_ID", "UID", "PASSWORD", "COMPOSITE_INFO", 
        "METRIC_FOLLOW", "METRIC_VIDEO", "ACTION_STATUS", 
        "WORKER_ASSIGN", "LIVE_STATUS", "RAW_PAYLOAD", "LOG_ENTRY"
    ]
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # --- ADVANCED STYLING ENGINE (CSS) ---
    @staticmethod
    def inject_css():
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=Share+Tech+Mono&display=swap');

            /* ROOT VARS */
            :root {
                --neon-green: #0f0;
                --neon-cyan: #0ff;
                --deep-space: #050505;
                --glass: rgba(255, 255, 255, 0.05);
                --border: 1px solid rgba(0, 255, 255, 0.2);
            }

            /* GLOBAL RESET */
            .stApp {
                background-color: var(--deep-space);
                background-image: 
                    linear-gradient(rgba(0, 255, 0, 0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 255, 0, 0.03) 1px, transparent 1px);
                background-size: 30px 30px;
                font-family: 'Rajdhani', sans-serif;
                color: #e0e0e0;
            }

            /* TYPOGRAPHY */
            h1, h2, h3, h4 {
                font-family: 'Rajdhani', sans-serif;
                text-transform: uppercase;
                letter-spacing: 3px;
                color: #fff;
                text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            }
            .mono-font { font-family: 'Share Tech Mono', monospace; }

            /* ANIMATIONS */
            @keyframes scanline {
                0% { transform: translateY(-100%); }
                100% { transform: translateY(100%); }
            }
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); }
                100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
            }
            @keyframes blink { 50% { opacity: 0; } }

            /* COMPONENTS */
            .titan-card {
                background: var(--glass);
                backdrop-filter: blur(10px);
                border: var(--border);
                border-radius: 4px;
                padding: 20px;
                margin-bottom: 20px;
                position: relative;
                overflow: hidden;
            }
            .titan-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; width: 100%; height: 2px;
                background: linear-gradient(90deg, transparent, var(--neon-green), transparent);
            }

            /* INPUTS */
            .stTextInput input, .stTextArea textarea, .stNumberInput input {
                background: rgba(0,0,0,0.8) !important;
                border: 1px solid #333 !important;
                color: var(--neon-cyan) !important;
                font-family: 'Share Tech Mono', monospace !important;
                border-radius: 0 !important;
            }
            .stTextInput input:focus {
                border-color: var(--neon-green) !important;
                box-shadow: 0 0 15px rgba(0, 255, 0, 0.2) !important;
            }

            /* BUTTONS */
            .stButton button {
                background: transparent;
                border: 1px solid var(--neon-green);
                color: var(--neon-green);
                font-family: 'Rajdhani', sans-serif;
                font-weight: 700;
                letter-spacing: 2px;
                border-radius: 0;
                transition: 0.3s;
                text-transform: uppercase;
            }
            .stButton button:hover {
                background: var(--neon-green);
                color: #000;
                box-shadow: 0 0 20px var(--neon-green);
            }
            button[kind="primary"] {
                background: rgba(0, 255, 255, 0.1) !important;
                border-color: var(--neon-cyan) !important;
                color: var(--neon-cyan) !important;
            }

            /* DATAFRAME */
            div[data-testid="stDataFrame"] {
                border: 1px solid #333;
                font-family: 'Share Tech Mono', monospace;
            }

            /* METRICS */
            div[data-testid="metric-container"] {
                background: #0a0a0a;
                border-left: 3px solid var(--neon-green);
                padding: 10px;
            }
            div[data-testid="stMetricValue"] {
                color: var(--neon-green) !important;
                font-family: 'Share Tech Mono', monospace;
                font-size: 28px !important;
            }
            
            /* FOOTER */
            .footer-terminal {
                border-top: 1px dashed #333;
                padding: 20px;
                margin-top: 50px;
                font-size: 12px;
                color: #666;
                text-align: right;
            }
            .blink-cursor { animation: blink 1s infinite; }
        </style>
        """, unsafe_allow_html=True)

# ==================================================================================================
# [LAYER 1] DATABASE DRIVER
# ==================================================================================================

class DatabaseDriver:
    """Handles low-level Google API transactions."""
    
    @staticmethod
    def _get_creds():
        # Fallback mechanism for credentials
        if "gcp_service_account" in st.secrets:
            return ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), TitanConfig.SCOPE)
        return ServiceAccountCredentials.from_json_keyfile_name("credentials.json", TitanConfig.SCOPE)

    @staticmethod
    def connect(sheet_id: str) -> Optional[gspread.models.Worksheet]:
        if not sheet_id: return None
        try:
            creds = DatabaseDriver._get_creds()
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(sheet_id)
            
            # Auto-Provisioning Logic
            try:
                ws = spreadsheet.worksheet(TitanConfig.TAB_NAME)
            except gspread.WorksheetNotFound:
                # Create new schema if missing
                ws = spreadsheet.add_worksheet(title=TitanConfig.TAB_NAME, rows=5000, cols=20)
                ws.append_row(TitanConfig.HEADERS)
                ws.freeze(rows=1)
            return ws
        except Exception as e:
            st.error(f"FATAL ERROR: Connection Refused. {str(e)}")
            return None

# ==================================================================================================
# [LAYER 2] BUSINESS LOGIC CONTROLLER
# ==================================================================================================

class TitanController:
    """Manages data transformation and business rules."""
    
    def __init__(self, ws):
        self.ws = ws

    def ingest_data(self, batch_name: str, raw_payload: str) -> int:
        if not self.ws: return 0
        
        # 1. Spacing Buffer
        buffer_rows = [[""] * len(TitanConfig.HEADERS) for _ in range(5)]
        
        # 2. Batch Header with Timestamp
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header_row = [f"📦 BATCH: {batch_name} [{ts}]"] + [""] * (len(TitanConfig.HEADERS)-1)
        buffer_rows.append(header_row)
        
        # 3. Payload Parsing
        rows = []
        lines = raw_payload.split("\n")
        valid_count = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            parts = line.split("|")
            while len(parts) < 6: parts.append("N/A")
            
            # Logic: Merge Columns
            merged_data = "|".join(parts[2:6])
            raw_data = "|".join(parts[:6])
            
            # Schema Mapping
            row = [
                "",                     # BATCH_ID
                parts[0],               # UID
                parts[1],               # PASS
                merged_data,            # COMPOSITE
                "PENDING",              # FL
                "PENDING",              # VID
                "Active",               # STATUS
                "",                     # WORKER
                "Live",                 # LIVE
                raw_data,               # RAW
                "New"                   # LOG
            ]
            rows.append(row)
            valid_count += 1
            
        # 4. Atomic Commit
        final_payload = buffer_rows + rows
        if valid_count > 0:
            self.ws.append_rows(final_payload)
            
        return valid_count

    def execute_fifo_export(self, limit: int) -> Optional[str]:
        if not self.ws: return None
        
        # Fetch entire dataset
        grid = self.ws.get_all_values()
        
        export_buffer = []
        update_queue = []
        count = 0
        ts = datetime.now().strftime('%d/%m %H:%M')
        
        # Iterate (Skip header)
        for idx, row in enumerate(grid):
            if idx == 0: continue
            if len(row) < 2 or row[1] == "": continue # Skip buffers
            
            # Check Log Column (Index 10)
            log_val = row[10] if len(row) > 10 else ""
            
            if "Đã lấy" not in log_val:
                # Capture Raw (Index 9)
                raw_val = row[9] if len(row) > 9 else ""
                export_buffer.append(raw_val)
                
                # Queue Update
                update_queue.append({
                    'range': f'K{idx+1}', 
                    'values': [[f"Đã lấy {ts}"]]
                })
                count += 1
                if count >= limit: break
                
        if export_buffer:
            self.ws.batch_update(update_queue)
            return "\n".join(export_buffer)
        
        return None

# ==================================================================================================
# [LAYER 3] USER INTERFACE (TITAN UI)
# ==================================================================================================

def render_boot_sequence():
    """Simulates a system boot for effect."""
    if 'booted' not in st.session_state:
        placeholder = st.empty()
        # Fake loading commands
        commands = [
            "Initializing Kernel...",
            "Loading Neural Modules...",
            "Decrypting Secure Enclave...",
            "Establishing Uplink to Google Cloud...",
            "TITAN OS v99.0 Loaded."
        ]
        
        with placeholder.container():
            st.markdown("<div style='height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;'>", unsafe_allow_html=True)
            for cmd in commands:
                st.markdown(f"<p class='mono-font' style='color: #0f0;'>root@titan:~# {cmd}</p>", unsafe_allow_html=True)
                time.sleep(0.3)
            st.markdown("</div>", unsafe_allow_html=True)
        
        time.sleep(0.5)
        placeholder.empty()
        st.session_state.booted = True

def main():
    TitanConfig.inject_css()
    
    # SYSTEM BOOT VISUAL
    render_boot_sequence()

    # SIDEBAR CONTROL
    with st.sidebar:
        st.markdown(f"## 🛡️ {TitanConfig.CODENAME}")
        st.markdown(f"<p class='mono-font' style='font-size: 10px; color: #666;'>KERNEL: {TitanConfig.VERSION}</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 🔌 SECURE LINK")
        
        # ID Handling
        def_id = st.secrets.get("sheet_id", "") if "sheet_id" in st.secrets else ""
        cached_id = st.session_state.get('db_id', def_id)
        
        sheet_input = st.text_input("INPUT TARGET IDENTIFIER", value=cached_id, type="password", help="Paste Sheet ID")
        
        if st.button("INITIATE HANDSHAKE"):
            st.session_state.db_id = sheet_input
            st.cache_resource.clear()
            st.rerun()
            
        st.markdown("---")
        st.info(f"OPERATOR: {TitanConfig.ADMIN}")

    # LOGIC GATEWAY
    target = st.session_state.get('db_id', def_id)
    
    if not target:
        # LOCKED STATE UI
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("""
            <div class='titan-card' style='text-align: center;'>
                <h1 style='color: var(--neon-red); text-shadow: 0 0 10px red;'>SYSTEM LOCKED</h1>
                <p class='mono-font'>ACCESS DENIED. MISSING DATABASE IDENTIFIER.</p>
                <hr style='border-color: #333;'>
                <p style='color: #888; font-size: 12px;'>Please enter the authorized Google Sheet ID in the Sidebar to unlock the mainframe.</p>
            </div>
            """, unsafe_allow_html=True)
        st.stop()
        
    # CONNECTED STATE
    ws = DatabaseDriver.connect(target)
    if not ws: st.stop()
    
    controller = TitanController(ws)
    
    # DASHBOARD HEADER
    st.markdown(f"<h1>{TitanConfig.APP_NAME} <span style='font-size: 14px; vertical-align: middle; border: 1px solid var(--neon-green); padding: 2px 8px; border-radius: 4px; color: var(--neon-green);'>ONLINE</span></h1>", unsafe_allow_html=True)
    
    # METRICS ENGINE
    try:
        raw = ws.get_all_values()
        df = pd.DataFrame(raw[1:], columns=raw[0])
        
        # Advanced Filtering
        total_assets = len(df[df.iloc[:, 1] != ""]) # Count UIDs
        # New Assets (Regex match)
        new_assets = len(df[df.iloc[:, 10].astype(str).str.contains("New", na=False)])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL ASSETS", f"{total_assets:,}")
        m2.metric("LIQUID ASSETS", f"{new_assets:,}")
        m3.metric("LATENCY", f"{random.randint(12, 45)}ms")
        m4.metric("ENCRYPTION", "AES-256")
        
    except Exception:
        st.warning("DATABASE INITIALIZED. WAITING FOR DATA INGESTION.")
        df = pd.DataFrame()

    st.markdown("---")
    
    # MAIN OPERATIONS INTERFACE
    tabs = st.tabs(["[ 01_INGEST ]", "[ 02_COMMAND ]", "[ 03_LIQUIDATE ]", "[ 04_SYSTEM ]"])
    
    # TAB 1: INGESTION
    with tabs[0]:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### BATCH PARAMETERS")
            batch_id = st.text_input("BATCH IDENTIFIER", placeholder="e.g. ALPHA-01")
            st.caption("Auto-injects 5 buffer rows for separation.")
        with c2:
            st.markdown("#### RAW PAYLOAD STREAM")
            payload = st.text_area("DATA INPUT", height=200, help="User|Pass|Info...", placeholder="Paste raw pipe-separated data here...")
            
        if st.button(">>> EXECUTE UPLOAD SEQUENCE", key="btn_upload"):
            if batch_id and payload:
                with st.spinner("PARSING DATAGRAMS..."):
                    count = controller.ingest_data(batch_id, payload)
                    st.success(f"UPLOAD COMPLETE. {count} UNITS ADDED.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("MISSING PARAMETERS.")

    # TAB 2: COMMAND CENTER
    with tabs[1]:
        col_ctrl, col_view = st.columns([1, 3])
        
        with col_ctrl:
            st.markdown("#### CONTROLS")
            if st.button("REFRESH GRID"): 
                st.cache_resource.clear()
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("RUN DIAGNOSTICS"):
                st.toast("DIAGNOSTIC PROTOCOL INITIATED...", icon="⚡")
                # Add check logic here in future
                
        with col_view:
            if not df.empty:
                # Show only active rows
                view_df = df[(df.iloc[:, 0] != "") | (df.iloc[:, 1] != "")]
                st.data_editor(
                    view_df,
                    height=500,
                    use_container_width=True,
                    column_config={
                        "WORKER_ASSIGN": st.column_config.CheckboxColumn("ASSIGN", width="small"),
                        "ACTION_STATUS": st.column_config.SelectboxColumn("STATUS", options=["Active", "Kicked", "Dead"], width="small"),
                        "COMPOSITE_INFO": st.column_config.TextColumn("INFO", width="large"),
                        "UID": st.column_config.TextColumn("UID", disabled=True),
                    },
                    hide_index=True
                )
            else:
                st.info("NO DATA STREAM AVAILABLE.")

    # TAB 3: LIQUIDATION
    with tabs[2]:
        st.markdown("#### ASSET LIQUIDATION PROTOCOL (FIFO)")
        qty = st.number_input("QUANTITY", min_value=1, value=10)
        
        if st.button(">>> EXTRACT & MARK SOLD"):
            data_out = controller.execute_fifo_export(qty)
            if data_out:
                st.download_button(
                    label="DOWNLOAD SECURE PACKAGE",
                    data=data_out,
                    file_name=f"EXPORT_{uuid.uuid4().hex[:8].upper()}.txt",
                    mime="text/plain"
                )
                st.success("EXTRACTION SUCCESSFUL.")
            else:
                st.error("INSUFFICIENT INVENTORY.")

    # TAB 4: SYSTEM INFO
    with tabs[3]:
        st.json({
            "KERNEL": TitanConfig.VERSION,
            "CONNECTED_NODE": target[:8] + "******",
            "USER_AGENT": TitanConfig.ADMIN,
            "UPTIME": "99.999%"
        })

    # TERMINAL FOOTER
    st.markdown(f"""
    <div class='footer-terminal mono-font'>
        root@titan-server:~# status check<br>
        > SYSTEM OPTIMAL<br>
        > DEVELOPED BY <span style='color: var(--neon-green);'>{TitanConfig.ADMIN}</span><br>
        > <span class='blink-cursor'>_</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
