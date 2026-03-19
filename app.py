import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import pandas as pd
import io
import json

# --- CẤU HÌNH ---
st.set_page_config(page_title="Khai thác dữ liệu", layout="wide")
st.title("📊 Công cụ Khai thác Chỉ đạo")

# Khởi tạo AI với cơ chế thử nhiều tên model khác nhau
def get_response_ai(prompt):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Danh sách các tên model có thể khả dụng
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.0-pro']
    
    last_error = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            return model.generate_content(prompt)
        except Exception as e:
            last_error = e
            continue
    raise last_error

# --- HÀM ĐỌC FILE ---
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
        return ""

# --- GIAO DIỆN ---
uploaded_file = st.file_uploader("Tải file", type=["pdf", "docx"])

if uploaded_file:
    raw_text = get_content(uploaded_file)
    if st.button("🚀 Phân tích & Trích xuất"):
        with st.spinner("AI đang xử lý..."):
            prompt = f"""
            Phân tích văn bản và trả về DUY NHẤT định dạng JSON list (không giải thích thêm):
            [{{"STT": 1, "Nhiệm vụ": "...", "Chủ trì": "...", "Thời hạn": "..."}}]
            Văn bản: {raw_text[:10000]}
            """
            try:
                response = get_response_ai(prompt)
                # Làm sạch chuỗi JSON
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)
                df = pd.DataFrame(data)
                
                st.subheader("📋 Kết quả")
                st.dataframe(df, use_container_width=True)
                
                # Xuất Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 Tải về Excel", output.getvalue(), "chidao.xlsx")
            except Exception as e:
                st.error(f"Lỗi: {e}")
                if 'response' in locals(): st.info(response.text)
