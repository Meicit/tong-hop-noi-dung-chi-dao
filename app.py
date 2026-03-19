import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import pandas as pd
import io

st.set_page_config(page_title="AI Hành Chính", layout="wide")
st.title("📊 Trợ lý Trích xuất & Xuất Excel")

# Cấu hình AI - Dùng đúng tên model chuẩn
def get_model():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Thiếu API Key trong Secrets!")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# Đọc file
uploaded_file = st.file_uploader("Tải file PDF/Word", type=["pdf", "docx"])

if uploaded_file:
    text = ""
    if uploaded_file.type == "application/pdf":
        for page in PdfReader(uploaded_file).pages:
            text += page.extract_text() + "\n"
    else:
        doc = Document(uploaded_file)
        text = "\n".join([p.text for p in doc.paragraphs])

    if st.button("🚀 Phân tích & Tạo Excel"):
        with st.spinner("AI đang xử lý..."):
            # Prompt yêu cầu trả về định dạng bảng Markdown để dễ xử lý
            prompt = f"Trích xuất danh sách nhiệm vụ từ văn bản này thành bảng gồm: STT, Nội dung nhiệm vụ, Đơn vị chủ trì, Thời hạn. Trình bày dạng bảng Markdown:\n\n{text[:10000]}"
            
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
                # Tạo file Excel mẫu từ nội dung văn bản (Dạng đơn giản)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Tạo dataframe tạm thời từ kết quả (hoặc cho tải txt nếu muốn nhanh)
                    pd.DataFrame([{"Kết quả": response.text}]).to_excel(writer, index=False)
                
                st.download_button("📥 Tải kết quả về", response.text, "ket_qua.txt")
            except Exception as e:
                st.error(f"Lỗi: {e}")
