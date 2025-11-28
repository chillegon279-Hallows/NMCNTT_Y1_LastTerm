import streamlit as st
import io
import time
from PIL import Image
import concurrent.futures
import base64

from serpapi import GoogleSearch
from ocr_tool import run_ocr
from keyword_tool import extract_keywords_yake

SERPAPI_API_KEY = "4a96eebb221cc9bb3d15b30830f09ed4634270f90a2a6183f324450abd09ae1a"

st.set_page_config(page_title="OCR → Keyword → Search", layout="wide")

# ---------------------------
# Background offline (base64)
# ---------------------------
with open("background.jpg", "rb") as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)),
                    url("data:image/jpg;base64,{b64}") no-repeat center center;
        background-size: cover;
        color: white;
    }}
    .stTextArea>div>textarea {{
        background-color: rgba(255,255,255,0.1);
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

st.title("Đồ ÁN NHÓM 9: OCR → Keywords → Search Engine")

col1, col2, col3 = st.columns(3)

# ---------------------------
# State OCR
# ---------------------------
if 'ocr_text' not in st.session_state:
    st.session_state['ocr_text'] = ""

ocr_text = st.session_state['ocr_text']
keyword_query = ""

# ---------------------------
# CỘT 1 — OCR
# ---------------------------
with col1:
    st.header("PADDLE OCR")
    uploaded = st.file_uploader("Tải ảnh lên:", type=["png", "jpg", "jpeg"])
    lang_select = st.selectbox("Ngôn ngữ OCR:", ["en", "ch", "vi"], key="ocr_lang") 

    if uploaded:
        image = Image.open(io.BytesIO(uploaded.read())).convert("RGB")
        st.image(image, caption="Ảnh đã tải", use_container_width=True)

        with st.spinner("Đang chạy OCR..."):
            ocr_text = run_ocr(image, lang=lang_select)
            st.session_state['ocr_text'] = ocr_text
            
        if ocr_text.strip() == "":
            st.warning("Không tìm thấy văn bản")
        else:
            st.success("POSTER PHIM ƯU TIẾN LẤY BIG->SMALL")

    st.text_area("Result :", st.session_state['ocr_text'], height=300)

# ---------------------------
# CỘT 2 — YAKE
# ---------------------------
with col2:
    st.header("YAKE! KEYWORDS")

    if not st.session_state['ocr_text'].strip():
        st.info("Chưa có văn bản OCR — tải ảnh ở cột bên trái.")
        keyword_query = ""
    else:
        ocr_word_count = len(st.session_state['ocr_text'].split())

        if ocr_word_count < 10:
            st.info("Văn bản quá ngắn (<10 từ), bỏ qua YAKE và dùng OCR text để tìm kiếm trực tiếp.")
            keyword_query = st.session_state['ocr_text'].strip()
        else:
            current_ocr_text = st.session_state['ocr_text']
            top_n = st.slider("Số từ khóa", 1, 10, 4, key="kw_top_n")
            keyphrase_n = st.slider("Độ dài cụm từ", 1, 5, 3, key="kw_phrase_n")
            current_lang = st.session_state.get('ocr_lang', 'en')

            kws = extract_keywords_yake(current_ocr_text, top_n, keyphrase_n, language=current_lang)

            st.subheader("Danh sách từ khóa:")
            for kw, score in kws:
                st.markdown(f"• **{kw}** — {score:.4f}")

            top_n_to_use = min(8, len(kws))
            selected_keywords = [kw for kw, _ in kws[:top_n_to_use]]
            keyword_query = " ".join(selected_keywords)

# ---------------------------
# CỘT 3 — SEARCH API
# ---------------------------
with col3:
    st.header("SEARCH ENGINE API (Google + Yahoo)")
    
    if not st.session_state['ocr_text'].strip():
        st.info("Cần OCR trước khi tự động tìm kiếm.")
    else:
        st.write("*Dùng từ khóa YAKE hoặc văn bản OCR để tìm kiếm trên Google & Yahoo*")
        final_query = keyword_query if keyword_query.strip() else st.session_state['ocr_text'].strip()
        st.code(final_query)

        if final_query.strip():
            results_container = st.container()
            with results_container:
                with st.spinner("LOADING Google & Yahoo..."):
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future_google = executor.submit(lambda q: GoogleSearch({'api_key': SERPAPI_API_KEY, 'engine':'google', 'q':q, 'num':5}).get_dict(), final_query)
                        future_yahoo = executor.submit(lambda q: GoogleSearch({'api_key': SERPAPI_API_KEY, 'engine':'yahoo', 'p':q, 'num':5}).get_dict(), final_query)
                        google_data = future_google.result()
                        yahoo_data = future_yahoo.result()

                def parse_results(data, engine_name=""):
                    if "error" in data:
                        return [{"title": f"Lỗi từ {engine_name}: {data['error']}", "link":"", "snippet":""}], 0
                    items = data.get("organic_results", [])
                    results = [{"title": i.get("title","Không có tiêu đề"), "link":i.get("link","#"), "snippet":i.get("snippet","Không có đoạn trích.")} for i in items]
                    return results, len(results)

                google_results, google_n = parse_results(google_data, "Google")
                yahoo_results, yahoo_n = parse_results(yahoo_data, "Yahoo")

                # Hiển thị kết quả dạng card
                for r in google_results:
                    st.markdown(f"""
                    <div style='background-color: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; margin-bottom:10px;'>
                        <h3 style='color:#FFD700;'>{r['title']}</h3>
                        <p style='color:white;'>{r['snippet']}</p>
                        <a href='{r['link']}' style='color:#1E90FF;'>Link</a>
                    </div>
                    """, unsafe_allow_html=True)

                for r in yahoo_results:
                    st.markdown(f"""
                    <div style='background-color: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; margin-bottom:10px;'>
                        <h3 style='color:#FFD700;'> {r['title']}</h3>
                        <p style='color:white;'>{r['snippet']}</p>
                        <a href='{r['link']}' style='color:#1E90FF;'>Link</a>
                    </div>
                    """, unsafe_allow_html=True)
