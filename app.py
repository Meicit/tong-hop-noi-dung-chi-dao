import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import pandas as pd
import io
import json

# --- CẤU HÌNH ---
st.set_page_config(page_title="Khai thác Chỉ đạo AI", layout="wide")
st.title("📊 Khai thác & Quản lý Dữ liệu Chỉ đạo")

def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# --- HÀM ĐỌC FILE ---
def extract_text(file):
    text = ""
    if file.type == "application/pdf":
        for page in PdfReader(file).pages: text += page.extract_text() + "\n"
    else:
        text = "\n".join([p.text for p in Document(file).paragraphs])
    return text

# --- GIAO DIỆN ---
file = st.file_uploader("Tải văn bản để khai thác dữ liệu", type=["pdf", "docx"])

if file:
    raw_text = extract_text(file)
    
    if st.button("🚀 Phân tích & Tạo file Excel"):
        with st.spinner("AI đang cấu trúc hóa dữ liệu..."):
            # Prompt yêu cầu AI trả về định dạng JSON chuẩn để làm bảng
            prompt = f"""
            Phân tích văn bản sau và trích xuất các nhiệm vụ. 
            Trả về DUY NHẤT một định dạng JSON list như sau:
            [{{"stt": 1, "nhiem_vu": "nội dung", "don_vi": "tên đơn vị", "thoi_han": "ngày/tháng"}}]
            
            Văn bản: {raw_text}
            """
            
            try:
                response = model.generate_content(prompt)
                # Làm sạch phản hồi để lấy JSON
                clean_json = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                
                # Tạo Bảng (Pandas DataFrame)
                df = pd.DataFrame(data)
                df.columns = ['STT', 'Nội dung nhiệm vụ', 'Đơn vị thực hiện', 'Thời hạn']
                
                st.subheader("📋 Bảng nhiệm vụ đã trích xuất")
                st.dataframe(df, use_container_width=True)
                
                # --- TẠO FILE EXCEL ĐỂ TẢI VỀ ---
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='NhiemVu')
                
                st.download_button(
                    label="📥 Tải về file Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Danh_sach_nhiem_vu_{file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Lỗi khi cấu trúc hóa dữ liệu: {e}")
                st.info("AI có thể không trả về đúng định dạng bảng, hãy thử lại.")
