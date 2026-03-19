import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Phân Tích Văn Bản", layout="wide")
st.title("🏛️ Hệ thống Trích xuất Chỉ đạo Văn bản")

# --- KẾT NỐI AI (CƠ CHẾ TỰ QUÉT MODEL) ---
def get_working_model():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ Thiếu API Key! Hãy thêm vào mục Settings > Secrets.")
        return None
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # Tự động lấy danh sách model mà Key của bạn được phép dùng
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Thứ tự ưu tiên model ổn định nhất
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.0-pro']
        for p in priority:
            if p in available_models:
                return genai.GenerativeModel(p)
        
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception as e:
        st.error(f"❌ Lỗi kết nối API: {e}")
        return None

model = get_working_model()

# --- HÀM ĐỌC FILE ---
def extract_text(file):
    text = ""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except: return ""

# --- GIAO DIỆN NGƯỜI DÙNG ---
uploaded_file = st.file_uploader("Tải lên file PDF hoặc Word", type=["pdf", "docx"])

if uploaded_file and model:
    content = extract_text(uploaded_file)
    if st.button("🚀 Bắt đầu Phân tích"):
        with st.spinner("AI đang xử lý..."):
            prompt = f"""
            Bạn là trợ lý hành chính. Hãy đọc văn bản sau và trích xuất thành bảng gồm: 
            STT, Nội dung nhiệm vụ, Đơn vị thực hiện, Thời hạn. 
            Văn bản: {content}
            """
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi thực thi: {e}")
