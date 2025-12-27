"""
################################################################################
# HỆ THỐNG: TITAN QUẢN LÝ KHO - PHIÊN BẢN VIỆT NAM
# PHIÊN BẢN: 2025.1-VN-STABLE
# TÁC GIẢ: ADMIN VĂN LINH
# MÔ TẢ: Giao diện tiếng Việt hoàn toàn, tối ưu cho người dùng Việt Nam.
################################################################################
"""

import streamlit as st
import gspread
import pandas as pd
import time
import random
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & MÀU SẮC (THEME VIỆT NAM)
# ==============================================================================

class TitanConfig:
    APP_NAME = "QUẢN LÝ KHO TITAN"
    ADMIN_USER = "Admin Văn Linh"
    VERSION = "v2025.1 (Tiếng Việt)"
    
    # Tên Tab trong Google Sheet
    TAB_NAME = "TITAN_MASTER_DB"
    
    # Tiêu đề cột (Tiếng Việt cho dễ quản lý)
    HEADERS = [
        "TÊN LÔ / LOG",     # Cột A
        "UID",              # Cột B
        "MẬT KHẨU",         # Cột C
        "THÔNG TIN GỘP",    # Cột D (Mail|PassMail|2FA)
        "FOLLOW (AUTO)",    # Cột E
        "VIDEO (AUTO)",     # Cột F
        "TRẠNG THÁI",       # Cột G (Active/Kick)
        "NHÂN VIÊN",        # Cột H
        "TÌNH TRẠNG",       # Cột I (Live/Die)
        "DỮ LIỆU GỐC",      # Cột J
        "GHI CHÚ KHO"       # Cột K (New/Sold)
    ]
    
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # CSS TÙY CHỈNH CHO ĐẸP VÀ DỄ NHÌN
    @staticmethod
    def inject_css():
        st.markdown("""
        <style>
            /* Font chữ dễ đọc */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
            
            .stApp {
                background-color: #121212; /* Nền đen dịu */
                color: #E0E0E0;
                font-family: 'Roboto', sans-serif;
            }

            /* Tiêu đề */
            h1, h2, h3 {
                color: #00E676; /* Xanh lá Titan */
                font-weight: 700;
                text-transform: uppercase;
            }

            /* Ô nhập liệu */
            .stTextInput input, .stTextArea textarea, .stNumberInput input {
                background-color: #1E1E1E !important;
                border: 1px solid #333 !important;
                color: #FFF !important;
                border-radius: 8px !important;
            }
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #00E676 !important;
            }

            /* Nút bấm */
            .stButton button {
                background-color: #00E676;
                color: #000;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                height: 45px;
                transition: 0.3s;
            }
            .stButton button:hover {
                background-color: #00C853;
                color: #FFF;
                box-shadow: 0 4px 12px rgba(0, 230, 118, 0.4);
            }

            /* Bảng dữ liệu */
            div[data-testid="stDataFrame"] {
                border: 1px solid #333;
                border-radius: 8px;
            }

            /* Thông báo lỗi/thành công */
            .stToast {
                background-color: #333 !important;
                color: #fff !important;
                border: 1px solid #00E676;
            }
            
            /* Footer */
            .titan-footer {
                text-align: center;
                padding: 20px;
                margin-top: 50px;
                border-top: 1px solid #333;
                color: #666;
                font-size: 14px;
            }
        </style>
        """, unsafe_allow_html=True)

# ==============================================================================
# 2. XỬ LÝ KẾT NỐI (BACKEND) - ĐÃ FIX LỖI GSPREAD
# ==============================================================================

class DatabaseDriver:
    @staticmethod
    def _get_creds():
        # Lấy chìa khóa từ Secrets (Web) hoặc File JSON (Máy tính)
        if "gcp_service_account" in st.secrets:
            return ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), TitanConfig.SCOPE)
        return ServiceAccountCredentials.from_json_keyfile_name("credentials.json", TitanConfig.SCOPE)

    @staticmethod
    def connect(sheet_id):
        if not sheet_id: return None
        try:
            creds = DatabaseDriver._get_creds()
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(sheet_id)
            
            # Tự động tạo Sheet nếu chưa có (Auto Provisioning)
            try:
                ws = spreadsheet.worksheet(TitanConfig.TAB_NAME)
            except gspread.WorksheetNotFound:
                ws = spreadsheet.add_worksheet(title=TitanConfig.TAB_NAME, rows=5000, cols=20)
                ws.append_row(TitanConfig.HEADERS)
                ws.freeze(rows=1)
            return ws
        except Exception as e:
            st.error(f"⚠️ LỖI KẾT NỐI: {str(e)}")
            st.info("Gợi ý: Kiểm tra lại ID Sheet hoặc xem đã Share quyền cho email Robot chưa.")
            return None

# ==============================================================================
# 3. XỬ LÝ NGHIỆP VỤ (LOGIC)
# ==============================================================================

class TitanController:
    def __init__(self, ws):
        self.ws = ws

    def nhap_kho(self, ten_lo, du_lieu_tho):
        """Xử lý nhập dữ liệu đầu vào"""
        if not self.ws: return 0
        
        # 1. Tạo 5 dòng trống cho thoáng
        rows_to_add = [[""] * len(TitanConfig.HEADERS) for _ in range(5)]
        
        # 2. Tạo dòng tiêu đề lô hàng
        ngay_gio = datetime.now().strftime('%d/%m/%Y %H:%M')
        header = [f"📦 LÔ HÀNG: {ten_lo} ({ngay_gio})"] + [""] * (len(TitanConfig.HEADERS)-1)
        rows_to_add.append(header)
        
        # 3. Xử lý từng dòng dữ liệu
        lines = du_lieu_tho.split("\n")
        count = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            parts = line.split("|")
            # Điền thêm rỗng nếu thiếu cột
            while len(parts) < 6: parts.append("")
            
            # Gộp thông tin (Mail|Pass|2FA...) vào cột D
            thong_tin_gop = "|".join(parts[2:6])
            # Giữ nguyên dữ liệu gốc vào cột J
            du_lieu_goc = "|".join(parts[:6])
            
            # Sắp xếp đúng thứ tự cột
            row = [
                "",                 # A: Tên lô (để trống cho dòng data)
                parts[0],           # B: UID
                parts[1],           # C: Pass
                thong_tin_gop,      # D: Thông tin gộp
                "",                 # E: Follow
                "",                 # F: Video
                "Active",           # G: Trạng thái
                "",                 # H: Nhân viên
                "Live",             # I: Tình trạng
                du_lieu_goc,        # J: Gốc
                "New"               # K: Ghi chú (Mới)
            ]
            rows_to_add.append(row)
            count += 1
            
        # Ghi vào Sheet một lần (cho nhanh)
        if count > 0:
            self.ws.append_rows(rows_to_add)
            
        return count

    def xuat_kho_fifo(self, so_luong):
        """Lấy hàng cũ nhất trước (FIFO)"""
        if not self.ws: return None
        
        # Lấy toàn bộ dữ liệu về
        all_data = self.ws.get_all_values()
        
        ket_qua = []
        updates = []
        dem = 0
        ngay_gio = datetime.now().strftime('%d/%m %H:%M')
        
        # Duyệt từng dòng (bỏ dòng đầu tiên là Header bảng)
        for i, row in enumerate(all_data):
            if i == 0: continue
            # Bỏ qua dòng trống hoặc dòng tiêu đề lô
            if len(row) < 2 or row[1] == "": continue
            
            # Kiểm tra cột K (Ghi chú kho) - index 10
            trang_thai_kho = row[10] if len(row) > 10 else ""
            
            # Nếu chưa có chữ "Đã lấy" thì lấy
            if "Đã lấy" not in trang_thai_kho:
                # Lấy cột J (Dữ liệu gốc) - index 9
                du_lieu = row[9] if len(row) > 9 else ""
                ket_qua.append(du_lieu)
                
                # Đánh dấu là đã lấy
                updates.append({
                    'range': f'K{i+1}', # Cột K dòng tương ứng
                    'values': [[f"Đã lấy {ngay_gio}"]]
                })
                
                dem += 1
                if dem >= so_luong: break # Đủ số lượng thì dừng
                
        if ket_qua:
            # Cập nhật trạng thái trên Sheet
            self.ws.batch_update(updates)
            return "\n".join(ket_qua)
        
        return None

# ==============================================================================
# 4. GIAO DIỆN NGƯỜI DÙNG (FRONTEND)
# ==============================================================================

def main():
    st.set_page_config(page_title="Titan Việt Nam", page_icon="🇻🇳", layout="wide")
    TitanConfig.inject_css()

    # --- THANH BÊN (SIDEBAR) ---
    with st.sidebar:
        st.markdown(f"## 🛡️ {TitanConfig.APP_NAME}")
        st.caption(f"Phiên bản: {TitanConfig.VERSION}")
        st.markdown("---")
        
        st.markdown("### 🔌 CẤU HÌNH KẾT NỐI")
        
        # Lấy ID mặc định nếu có trong Secrets
        id_mac_dinh = st.secrets.get("sheet_id", "") if "sheet_id" in st.secrets else ""
        # Lấy ID đang lưu trong phiên làm việc
        id_hien_tai = st.session_state.get('saved_id', id_mac_dinh)
        
        nhap_id = st.text_input("Nhập ID Google Sheet:", value=id_hien_tai, type="password", help="Dán đoạn mã ID của Sheet vào đây")
        
        if st.button("🔗 KẾT NỐI NGAY"):
            st.session_state.saved_id = nhap_id
            st.cache_resource.clear() # Xóa bộ nhớ đệm để kết nối lại
            st.success("Đã lưu ID!")
            time.sleep(0.5)
            st.rerun() # Tải lại trang
            
        st.markdown("---")
        st.info(f"Người điều hành: {TitanConfig.ADMIN_USER}")

    # --- KIỂM TRA ID ---
    target_id = st.session_state.get('saved_id', id_mac_dinh)
    
    if not target_id:
        # Màn hình chào mừng khi chưa nhập ID
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.info("👋 Chào Sếp! Vui lòng nhập **ID Google Sheet** ở thanh bên trái để bắt đầu làm việc.")
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Google_Sheets_logo_%282014-2020%29.svg/1200px-Google_Sheets_logo_%282014-2020%29.svg.png", width=100)
        st.stop()
        
    # --- KẾT NỐI DATABASE ---
    ws = DatabaseDriver.connect(target_id)
    if not ws: st.stop() # Dừng nếu lỗi kết nối
    
    controller = TitanController(ws)
    
    # --- MÀN HÌNH CHÍNH (DASHBOARD) ---
    st.title(f"{TitanConfig.APP_NAME} 🇻🇳")
    
    # Thống kê nhanh
    try:
        raw = ws.get_all_values()
        df = pd.DataFrame(raw[1:], columns=raw[0])
        
        # Đếm tổng số dòng có UID (Cột B khác rỗng)
        tong_acc = len(df[df.iloc[:, 1] != ""])
        # Đếm số dòng có chữ "New" ở cột K
        acc_moi = len(df[df.iloc[:, 10].astype(str).str.contains("New", na=False)])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 TỔNG TÀI KHOẢN", f"{tong_acc:,}")
        c2.metric("✅ HÀNG MỚI (NEW)", f"{acc_moi:,}")
        c3.metric("⚡ TRẠNG THÁI", "ĐANG HOẠT ĐỘNG")
        c4.metric("📅 NGÀY", datetime.now().strftime("%d/%m"))
        
    except Exception:
        st.warning("Kho dữ liệu mới. Vui lòng nhập lô hàng đầu tiên.")
        df = pd.DataFrame()

    st.markdown("---")
    
    # --- CÁC TAB CHỨC NĂNG ---
    tab1, tab2, tab3, tab4 = st.tabs(["📥 NHẬP KHO", "📋 DANH SÁCH", "📤 XUẤT ĐƠN", "⚙️ HỆ THỐNG"])
    
    # TAB 1: NHẬP KHO
    with tab1:
        col_trai, col_phai = st.columns([1, 2])
        with col_trai:
            st.subheader("1. Thông tin Lô hàng")
            ten_lo = st.text_input("Tên Lô (Ví dụ: Via Ngoại 27/12)")
            st.info("💡 Hệ thống sẽ tự động thêm 5 dòng trống để phân cách các lô.")
            
        with col_phai:
            st.subheader("2. Dữ liệu đầu vào")
            du_lieu = st.text_area("Dán dữ liệu vào đây (User|Pass|...)", height=250, placeholder="Định dạng: UID|Pass|2FA|Mail|PassMail|...")
            
        if st.button("🚀 TIẾN HÀNH NHẬP KHO", type="primary"):
            if ten_lo and du_lieu:
                with st.spinner("Đang xử lý dữ liệu, vui lòng đợi..."):
                    so_luong = controller.nhap_kho(ten_lo, du_lieu)
                    st.toast(f"✅ Đã nhập thành công {so_luong} tài khoản!", icon="🎉")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Vui lòng nhập đầy đủ Tên lô và Dữ liệu!")

    # TAB 2: DANH SÁCH (QUẢN LÝ)
    with tab2:
        c_tacvu, c_bang = st.columns([1, 4])
        with c_tacvu:
            st.subheader("Tác vụ")
            if st.button("🔄 Tải lại dữ liệu"):
                st.cache_resource.clear()
                st.rerun()
            st.caption("Bấm nút trên để cập nhật danh sách mới nhất từ Google Sheet.")
                
        with c_bang:
            if not df.empty:
                # Lọc bỏ các dòng trống
                df_hien_thi = df[(df.iloc[:, 0] != "") | (df.iloc[:, 1] != "")]
                st.data_editor(
                    df_hien_thi,
                    height=500,
                    use_container_width=True,
                    column_config={
                        "TRẠNG THÁI": st.column_config.SelectboxColumn("Trạng thái", options=["Active", "Kicked", "Die"], width="small"),
                        "NHÂN VIÊN": st.column_config.CheckboxColumn("Đã giao", width="small"),
                        "UID": st.column_config.TextColumn("UID", disabled=True),
                    },
                    hide_index=True
                )
            else:
                st.info("Chưa có dữ liệu nào trong kho.")

    # TAB 3: XUẤT ĐƠN (FIFO)
    with tab3:
        st.subheader("Xuất hàng theo nguyên tắc Cũ Nhất - Ra Trước (FIFO)")
        c1, c2 = st.columns(2)
        with c1:
            so_luong_xuat = st.number_input("Nhập số lượng cần lấy:", min_value=1, value=10)
            
            if st.button("📦 LẤY HÀNG & TẢI FILE"):
                ket_qua = controller.xuat_kho_fifo(so_luong_xuat)
                if ket_qua:
                    file_name = f"DonHang_{datetime.now().strftime('%d%m_%H%M')}.txt"
                    st.download_button("💾 BẤM ĐỂ TẢI XUỐNG (.TXT)", ket_qua, file_name=file_name)
                    st.success(f"Đã trích xuất xong {so_luong_xuat} tài khoản!")
                else:
                    st.error("Kho đã hết hàng 'New' (Mới)!")
        
        with c2:
            st.markdown("""
            **Nguyên tắc hoạt động:**
            1. Hệ thống tìm các dòng có ghi chú **'New'**.
            2. Lấy hàng từ trên xuống dưới (Hàng nhập trước lấy trước).
            3. Tự động đổi ghi chú thành **'Đã lấy [Giờ/Ngày]'**.
            4. Xuất ra file TXT.
            """)

    # TAB 4: HỆ THỐNG
    with tab4:
        st.json({
            "Ứng dụng": TitanConfig.APP_NAME,
            "Phiên bản": TitanConfig.VERSION,
            "ID Sheet đang kết nối": target_id,
            "Trạng thái": "Hoạt động tốt"
        })

    # CHÂN TRANG
    st.markdown(f"""
    <div class="titan-footer">
        <p>Được phát triển bởi <b>{TitanConfig.ADMIN_USER}</b><br>
        Bản quyền thuộc về Titan Enterprise © 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
