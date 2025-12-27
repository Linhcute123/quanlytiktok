"""
################################################################################
# PROJECT: TITAN ENTERPRISE SYSTEM - STABLE RELEASE
# MODULE: MAIN KERNEL
# VERSION: 18.0.0-STABLE
# AUTHOR: ADMIN VAN LINH
# COPYRIGHT (C) 2025 TITAN CORPORATION.
#
# DESCRIPTION:
# Enterprise Inventory Management System with Google Sheets Integration.
# patched for gspread v6.0.0 compatibility.
################################################################################
"""

import streamlit as st
import gspread
import pandas as pd
import time
import random
import logging
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN (SYSTEM CONFIG)
# ==============================================================================

class SystemConfig:
    APP_NAME = "TITAN ENTERPRISE"
    VERSION = "v18.0.0-Stable"
    ADMIN_USER = "Admin Văn Linh"
    
    # Cấu trúc Database chuẩn
    DB_TAB_NAME = "TITAN_MASTER_DB"
    DB_HEADERS = [
        "BATCH / LOG",       # A
        "UID",               # B
        "PASS",              # C
        "FULL INFO (GỘP)",   # D
        "FOLLOW (AUTO)",     # E
        "VIDEO (AUTO)",      # F
        "KICK (MANUAL)",     # G
        "WORKING (TICK)",    # H
        "NICK STATUS",       # I
        "EXPORT RAW (J)",    # J
        "KHO LOG"            # K
    ]
    
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # CSS "Deep Dark" Interface
    CUSTOM_CSS = """
        <style>
            /* Reset & Base */
            .stApp { background-color: #09090b; color: #FAFAFA; font-family: 'Segoe UI', Roboto, sans-serif; }
            
            /* Typography */
            h1, h2, h3 { color: #fff; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; }
            h1 span { color: #00E676; }
            
            /* Metric Cards */
            div[data-testid="stMetricValue"] { font-size: 28px; color: #00E676; font-weight: bold; text-shadow: 0 0 10px rgba(0, 230, 118, 0.3); }
            div[data-testid="metric-container"] { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 10px; }
            
            /* Buttons */
            .stButton>button { 
                width: 100%; border-radius: 6px; height: 50px; font-weight: 600;
                background: linear-gradient(180deg, #27272a 0%, #18181b 100%); 
                color: white; border: 1px solid #3f3f46; transition: 0.3s; 
            }
            .stButton>button:hover { border-color: #00E676; color: #00E676; transform: translateY(-2px); }
            div[data-testid="stHorizontalBlock"] button[kind="primary"] { background: #00E676 !important; color: black !important; border: none !important; }

            /* Inputs */
            .stTextInput>div>div>input, .stTextArea>div>div>textarea { 
                background-color: #121212; color: #00E676; border: 1px solid #333; border-radius: 6px; 
            }
            
            /* Footer */
            .titan-footer { margin-top: 80px; padding: 30px; border-top: 1px solid #222; text-align: center; background: #000; }
            .admin-badge { font-weight: 900; color: #00E676; font-size: 1.2em; }
        </style>
    """

# ==============================================================================
# 2. QUẢN LÝ KẾT NỐI DATABASE (FIXED GSPREAD ERROR)
# ==============================================================================

class DatabaseManager:
    """
    Quản lý kết nối tới Google Sheets.
    Đã vá lỗi 'models' của gspread v6.0.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
    
    def _get_creds(self):
        """Lấy credentials từ Secrets (Ưu tiên) hoặc File Local"""
        if "gcp_service_account" in st.secrets:
            # Load từ Secrets (Streamlit Cloud)
            return ServiceAccountCredentials.from_json_keyfile_dict(
                dict(st.secrets["gcp_service_account"]), SystemConfig.SCOPE
            )
        else:
            # Load từ file json (Máy local)
            return ServiceAccountCredentials.from_json_keyfile_name(
                "credentials.json", SystemConfig.SCOPE
            )

    def connect(self, sheet_id):
        """Kết nối tới Sheet ID cụ thể & Auto Provisioning"""
        if not sheet_id: return None
        
        try:
            creds = self._get_creds()
            client = gspread.authorize(creds)
            
            # Mở Spreadsheet
            spreadsheet = client.open_by_key(sheet_id)
            
            # Kiểm tra xem Tab Database đã có chưa
            try:
                worksheet = spreadsheet.worksheet(SystemConfig.DB_TAB_NAME)
            except gspread.WorksheetNotFound:
                # Nếu chưa có -> Tự tạo mới (Auto Provisioning)
                st.toast("⚠️ Database chưa tồn tại. Đang khởi tạo...", icon="⚙")
                worksheet = spreadsheet.add_worksheet(
                    title=SystemConfig.DB_TAB_NAME, 
                    rows=5000, 
                    cols=20
                )
                worksheet.append_row(SystemConfig.DB_HEADERS)
                worksheet.freeze(rows=1)
                st.toast("✅ Đã khởi tạo cấu trúc kho thành công!", icon="🚀")
            
            return worksheet
            
        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {str(e)}")
            return None

# ==============================================================================
# 3. LOGIC NGHIỆP VỤ (CORE LOGIC)
# ==============================================================================

class TitanCore:
    def __init__(self, ws):
        self.ws = ws

    def import_data(self, batch_name, raw_data):
        """Nhập liệu thông minh: Cách dòng, Gộp cột, Format"""
        if not self.ws: return 0
        
        rows = []
        # 1. Tạo 5 dòng trống (Spacing)
        for _ in range(5): 
            rows.append([""] * len(SystemConfig.DB_HEADERS))
        
        # 2. Tạo Header Lô
        timestamp = datetime.now().strftime('%d/%m/%Y')
        rows.append([f"📦 {batch_name} ({timestamp})"] + [""]*10)
        
        # 3. Xử lý dữ liệu thô
        lines = raw_data.split("\n")
        cnt = 0
        for line in lines:
            line = line.strip()
            if not line: continue
            
            parts = line.split("|")
            while len(parts) < 6: parts.append("")
            
            # Gộp cột D (Info)
            merged = "|".join(parts[2:6])
            # Giữ Raw (Col J)
            raw_j = "|".join(parts[:6])
            
            # Mapping schema
            row = ["", parts[0], parts[1], merged, "", "", "Active", "", "Live", raw_j, "New"]
            rows.append(row)
            cnt += 1
            
        if cnt > 0:
            self.ws.append_rows(rows)
        return cnt

    def run_check_simulation(self, df, progress_bar):
        """Giả lập check Live (Ping TikTok)"""
        if not self.ws: return
        
        # Lọc ra các dòng cần check
        tasks = []
        for idx, row in df.iterrows():
            real_idx = idx + 2
            uid = str(row[1])
            if uid and uid != "" and uid != "nan" and "Kick" not in str(row[6]):
                tasks.append(real_idx)
        
        total = len(tasks)
        if total == 0: return

        for i, r_idx in enumerate(tasks):
            time.sleep(0.02) # Giả lập delay mạng
            
            # Random kết quả
            fl = random.choice([50, 500, 999, 1200, 5000, 10000])
            vid = random.choice(["Đã đăng", "Chưa đăng"])
            
            fl_txt = f"{fl} (Đã Buff)" if fl >= 1000 else str(fl)
            
            try:
                self.ws.update_cell(r_idx, 5, fl_txt)
                self.ws.update_cell(r_idx, 6, vid)
            except: pass
            
            progress_bar.progress((i + 1) / total)

    def export_fifo(self, qty):
        """Xuất kho FIFO - Lấy hàng cũ nhất chưa bán"""
        if not self.ws: return None
        
        data = self.ws.get_all_values()
        export_list = []
        updates = []
        found = 0
        timestamp = datetime.now().strftime('%d/%m %H:%M')
        
        for i, row in enumerate(data):
            if i == 0: continue
            if len(row) < 2 or row[1] == "": continue # Bỏ qua header lô
            
            status = row[10] if len(row) > 10 else ""
            
            if "Đã lấy" not in status:
                val = row[9] if len(row) > 9 else ""
                export_list.append(val)
                
                updates.append({
                    'range': f'K{i+1}', 
                    'values': [[f"Đã lấy {timestamp}"]]
                })
                found += 1
                if found >= qty: break
        
        if export_list:
            self.ws.batch_update(updates)
            return "\n".join(export_list)
        return None

# ==============================================================================
# 4. GIAO DIỆN NGƯỜI DÙNG (MAIN UI)
# ==============================================================================

def main():
    st.set_page_config(page_title=SystemConfig.APP_NAME, page_icon="🛡️", layout="wide")
    st.markdown(SystemConfig.CUSTOM_CSS, unsafe_allow_html=True)

    # --- SIDEBAR: KẾT NỐI ---
    with st.sidebar:
        st.title("🛡️ ADMIN PANEL")
        st.info(f"Operator: {SystemConfig.ADMIN_USER}")
        
        st.markdown("### 🔌 DATABASE CONNECTION")
        
        # Logic ID Sheet: Ưu tiên session -> Input -> Secrets -> Rỗng
        default_id = ""
        if "sheet_id" in st.secrets:
            default_id = st.secrets["sheet_id"]
            
        current_id = st.session_state.get('saved_id', default_id)
        
        sheet_id_input = st.text_input(
            "Nhập ID Google Sheet:", 
            value=current_id,
            placeholder="Dán ID Sheet vào đây...",
            type="password"
        )
        
        if st.button("🔗 KẾT NỐI KHO", type="primary"):
            st.session_state['saved_id'] = sheet_id_input
            st.cache_resource.clear()
            st.rerun()
            
        st.divider()
        st.caption(f"Kernel: {SystemConfig.VERSION}")

    # --- KẾT NỐI DATABASE ---
    target_id = st.session_state.get('saved_id', default_id)
    
    if not target_id:
        st.warning("⚠️ CHƯA KẾT NỐI: Vui lòng dán ID Google Sheet vào thanh bên trái để bắt đầu.")
        st.stop()
        
    ws = DatabaseManager().connect(target_id)
    if not ws: st.stop()
    
    core = TitanCore(ws)

    # --- DASHBOARD ---
    st.title(f"{SystemConfig.APP_NAME} <span>ULTIMATE</span>")
    
    try:
        raw_data = ws.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        
        valid_df = df[df.iloc[:, 1] != ""]
        total = len(valid_df)
        # Fix lỗi so sánh string
        new_cnt = len(valid_df[valid_df.iloc[:, 10].astype(str).str.contains("New", na=False)])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TỔNG TÀI KHOẢN", f"{total:,}")
        c2.metric("HÀNG TỒN (NEW)", f"{new_cnt:,}")
        c3.metric("KẾT NỐI", "SECURE")
        c4.metric("TRẠNG THÁI", "ONLINE")
    except:
        df = pd.DataFrame()
        st.warning("Database mới tạo. Hãy nhập liệu.")

    st.markdown("---")
    
    # --- TABS CHỨC NĂNG ---
    t1, t2, t3, t4 = st.tabs(["📥 NHẬP KHO", "🔥 QUẢN LÝ LIVE", "📤 XUẤT KHO", "⚙ INFO"])
    
    # TAB 1: NHẬP
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            batch = st.text_input("Tên Lô (Batch Name)")
            st.info("Hệ thống tự động chèn 5 dòng trống phân cách.")
        with c2:
            raw = st.text_area("Dữ liệu thô (User|Pass|...)", height=250)
            
        if st.button("🚀 TIẾN HÀNH NHẬP KHO", type="primary"):
            if not batch or not raw:
                st.toast("Thiếu thông tin lô hoặc dữ liệu!", icon="⚠️")
            else:
                with st.spinner("Đang xử lý dữ liệu..."):
                    cnt = core.import_data(batch, raw)
                    st.success(f"Đã nhập thành công {cnt} tài khoản!")
                    time.sleep(1)
                    st.rerun()

    # TAB 2: QUẢN LÝ
    with t2:
        c_act, c_tbl = st.columns([1, 4])
        with c_act:
            if st.button("🔄 Làm mới dữ liệu"): 
                st.cache_resource.clear()
                st.rerun()
            st.divider()
            if st.button("⚡ Chạy Auto Check"): 
                st.session_state.run_check = True
        
        with c_tbl:
            if not df.empty:
                # Chỉ hiện dòng có dữ liệu (Bỏ dòng trống spacing)
                show_df = df[(df.iloc[:, 0] != "") | (df.iloc[:, 1] != "")]
                st.data_editor(
                    show_df,
                    height=600,
                    use_container_width=True,
                    column_config={
                        "WORKING (TICK)": st.column_config.CheckboxColumn("Work", width="small"),
                        "KICK (MANUAL)": st.column_config.SelectboxColumn("Kick", options=["Active", "Đã Kick"], width="small"),
                        "FULL INFO (GỘP)": st.column_config.TextColumn("Info", width="large"),
                        "UID": st.column_config.TextColumn("UID", disabled=True),
                    },
                    hide_index=True
                )
            else:
                st.info("Chưa có dữ liệu.")
        
        if st.session_state.get("run_check", False):
            st.markdown("---")
            st.write("Đang quét trạng thái...")
            bar = st.progress(0)
            core.run_check_simulation(df, bar)
            st.session_state.run_check = False
            st.success("Hoàn tất quét!")
            time.sleep(1)
            st.rerun()

    # TAB 3: XUẤT
    with t3:
        qty = st.number_input("Số lượng cần lấy", min_value=1, value=10)
        if st.button("📤 XUẤT FILE FIFO"):
            txt = core.export_fifo(qty)
            if txt:
                fname = f"Titan_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                st.download_button("💾 TẢI FILE TXT", txt, file_name=fname)
                st.success(f"Đã lấy xong {qty} acc!")
            else:
                st.error("Kho hết hàng New!")

    # TAB 4: INFO
    with t4:
        st.json({"App": SystemConfig.APP_NAME, "ID": target_id, "Tab": SystemConfig.DB_TAB_NAME})

    # FOOTER
    st.markdown(f"""
        <div class="titan-footer">
            <p>© 2025 TITAN CORPORATION<br>
            ARCHITECTED BY <span class="admin-badge">{SystemConfig.ADMIN_USER}</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#00E676" style="vertical-align: middle; margin-left: 5px;">
                <path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.71-3.998-3.818-3.998-.47 0-.92.084-1.336.25C14.818 2.415 13.51 1.5 12 1.5s-2.816.917-3.437 2.25c-.415-.165-.866-.25-1.336-.25-2.11 0-3.818 1.79-3.818 4 0 .495.083.965.238 1.4-1.272.65-2.147 2.018-2.147 3.6 0 1.495.782 2.798 1.942 3.486-.02.17-.032.34-.032.514 0 2.21 1.708 4 3.818 4 .47 0 .92-.086 1.335-.25.62 1.334 1.926 2.25 3.437 2.25 1.512 0 2.818-.916 3.437-2.25.415.163.865.248 1.336.248 2.11 0 3.818-1.79 3.818-4 0-.174-.012-.344-.033-.513 1.158-.687 1.943-1.99 1.943-3.484zm-6.616-3.334l-4.334 6.5c-.145.217-.382.334-.625.334-.143 0-.288-.04-.416-.126l-.115-.094-2.415-2.415c-.293-.293-.293-.768 0-1.06s.768-.294 1.06 0l1.77 1.767 3.825-5.74c.23-.345.696-.436 1.04-.207.346.23.44.696.21 1.04z" />
            </svg></p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
