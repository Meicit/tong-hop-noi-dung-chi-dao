import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import pandas as pd
import io
import json

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Khai thác dữ liệu văn bản", layout="wide")
st.title("📊 Công cụ Khai thác & Xuất dữ liệu Chỉ đạo")

# Khởi tạo AI
def init_ai():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Chưa cấu hình API Key trong Secrets!")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_ai()

# --- 2. HÀM ĐỌC FILE ---
def get_content(file):
    text = ""
    try:
        if file.type == "application/pdf":
            pdf = PdfReader(file)
            for page in pdf.pages: text += page.extract_text() + "\n"
        else:
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return ""

# --- 3. GIAO DIỆN ---
uploaded_file = st.file_uploader("Tải lên file văn bản", type=["pdf", "docx"])

if uploaded_file:
    raw_text = get_content(uploaded_file)
    
    if st.button("🚀 Phân tích và Trích xuất dữ liệu"):
        if not raw_text:
            st.warning("Không tìm thấy nội dung trong file.")
        else:
            with st.spinner("AI đang xử lý dữ liệu..."):
                # Prompt yêu cầu JSON để dễ khai thác
                prompt = f"""
                Phân tích văn bản hành chính sau và trả về danh sách nhiệm vụ.
                Yêu cầu trả về DUY NHẤT định dạng JSON (không kèm văn bản khác) theo mẫu:
                [
                  {{"STT": 1, "Nhiệm vụ": "nội dung", "Chủ trì": "đơn vị", "Thời hạn": "ngày tháng"}}
                ]
                Văn bản: {raw_text[:8000]}
                """
                
                try:
                    response = model.generate_content(prompt)
                    res_text = response.text.replace('```json', '').replace('```', '').strip()
                    
                    # Chuyển đổi sang DataFrame
                    data = json.loads(res_text)
                    df = pd.DataFrame(data)
                    
                    st.subheader("📋 Danh mục nhiệm vụ trích xuất")
                    st.dataframe(df, use_container_width=True)
                    
                    # --- XỬ LÝ XUẤT EXCEL ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='ChiDao')
                    
                    st.download_button(
                        label="📥 Tải về file Excel (.xlsx)",
                        data=output.getvalue(),
                        file_name=f"Trich_xuat_{uploaded_file.name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                except Exception as e:
                    st.error("AI không trả về định dạng bảng chuẩn. Dưới đây là nội dung chi tiết:")
                    st.info(response.text)
