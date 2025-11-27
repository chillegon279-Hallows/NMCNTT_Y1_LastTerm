import streamlit as st
import io
import time
import requests
from PIL import Image

from ocr_tool import run_ocr
from keyword_tool import extract_keywords_yake

# =============================
# API Keys
# =============================
# KHUYẾN NGHỊ: Thay thế bằng Key và CX thực tế của bạn
GOOGLE_API_KEY = "AIzaSyAFT6w_Sg2GZbkIQfZreQgpwvUZIYWo6lM" 
GOOGLE_CSE_ID = "f334466b1bc93448f"
YAHOO_API_KEY = "bf048418215d39d737962b39e42f051498764ec0db73e9a7e5cbd38d80f0c0d3"
SERPAPI_BASE_URL = "https://serpapi.com/search"    

# =============================
# Search Functions
# =============================

def search_google(query: str):
    # SỬ DỤNG ENDPOINT API CHÍNH XÁC (KHẮC PHỤC LỖI KHÔNG TÌM THẤY JSON)
    url = "https://www.googleapis.com/customsearch/v1" 
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query,
        'num': 5
    }

    start = time.time()
    try:
        r = requests.get(url, params=params)
        end = time.time()

        # 1. Xử lý lỗi HTTP status code (4xx, 5xx)
        if r.status_code != 200:
            error_text = r.text[:100]
            msg = f"⚠️ Google API lỗi {r.status_code}. Nội dung: {error_text}..."
            return [{"title": msg, "link": "", "snippet": ""}], end-start, 0
        
        # 2. Xử lý lỗi JSON Decode (ví dụ: phản hồi không phải JSON)
        try:
            data = r.json()
        except requests.exceptions.JSONDecodeError as json_e:
            error_text = r.text[:100]
            msg = f"❗ Lỗi JSON: {str(json_e)}. Phản hồi: {error_text}..."
            return [{"title": msg, "link": "", "snippet": ""}], end-start, 0
        
        # 3. Xử lý lỗi Google trả về trong JSON (ví dụ: hết quota)
        if "error" in data:
            error_message = data["error"].get("message", "Lỗi không xác định từ Google JSON.")
            status_code = data["error"].get("code", "N/A")
            msg = f"❌ Lỗi từ Google API ({status_code}): {error_message}"
            return [{"title": msg, "link": "", "snippet": ""}], end-start, 0

        # Trích xuất kết quả
        items = data.get("items", [])

        results = [{
            "title": i.get("title"),
            "link": i.get("link"),
            "snippet": i.get("snippet", "")
        } for i in items]

        return results, end - start, len(results)

    except Exception as e:
        return [{"title": "Lỗi kết nối mạng/chung", "link": "", "snippet": str(e)}], 0, 0

def search_yahoo(query: str):
    params = {
        "api_key": YAHOO_API_KEY,
        "engine": "yahoo",
        "p": query,
        "gl": "us",
        "num": 5
    }

    start = time.time()
    try:
        r = requests.get(SERPAPI_BASE_URL, params=params)
        end = time.time()

        if r.status_code != 200:
            msg = f"⚠️ Yahoo API (SerpApi) lỗi {r.status_code}"
            return [{"title": msg, "link": "", "snippet": ""}], end-start, 0

        data = r.json()
        organic = data.get("organic_results", [])

        results = [{
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        } for item in organic]

        return results, end - start, len(results)

    except Exception as e:
        return [{"title": "Lỗi kết nối Yahoo (SerpApi)", "link": "", "snippet": str(e)}], 0, 0



# ======================================================================
#                             STREAMLIT UI
# ======================================================================

st.set_page_config(page_title="OCR → Keyword → Search", layout="wide")

st.title("📄 OCR → Keywords → Search Engine")

col1, col2, col3 = st.columns(3)

# ---------------------------
# 🧩 CỘT 1 — TOOL OCR
# ---------------------------
with col1:
    st.header("1️⃣ OCR")

    uploaded = st.file_uploader("Tải ảnh lên:", type=["png", "jpg", "jpeg"])
    lang_select = st.selectbox("Ngôn ngữ OCR:", ["en", "ch", "vi"])

    ocr_text = ""

    if uploaded:
        image = Image.open(io.BytesIO(uploaded.read())).convert("RGB")
        st.image(image, caption="Ảnh đã tải", use_container_width=True)

        with st.spinner("Đang chạy OCR..."):
            ocr_text = run_ocr(image, lang=lang_select)

        if ocr_text.strip() == "":
            st.warning("❗ Không tìm thấy văn bản")
        else:
            st.success("✔ OCR thành công!")

            st.text_area("📌 Kết quả OCR:", ocr_text, height=300)


# ---------------------------
# 🧩 CỘT 2 — YAKE KEYWORDS
# ---------------------------
with col2:
    st.header("2️⃣ Trích Xuất Từ Khóa (YAKE)")

    if ocr_text.strip() == "":
        st.info("🔹 Chưa có văn bản OCR — tải ảnh ở cột bên trái.")
    else:
        top_n = st.slider("Số từ khóa", 5, 20, 10)
        keyphrase_n = st.slider("Độ dài cụm từ", 1, 5, 3)

        kws = extract_keywords_yake(ocr_text, top_n, keyphrase_n, language=lang_select)

        st.subheader("🔑 Danh sách từ khóa:")
        for kw, score in kws:
            st.write(f"• **{kw}** — {score:.4f}")

        # lưu để Search Engine dùng
        keyword_query = ", ".join([kw for kw, _ in kws])


# ---------------------------
# 🧩 CỘT 3 — SEARCH API (Tự Động)
# ---------------------------
with col3:
    st.header("3️⃣ Search Engine API (Google + Yahoo)")

    if ocr_text.strip() == "":
        st.info("🔹 Cần OCR trước khi tự động tìm kiếm.")
    else:
        st.write("💡 *Dùng từ khóa YAKE để tự động tìm kiếm trên Google & Yahoo*")
        st.code(keyword_query)

        with st.spinner("Đang truy vấn Google & Yahoo..."):
            google_results, google_delay, google_n = search_google(keyword_query)
            yahoo_results, yahoo_delay, yahoo_n = search_yahoo(keyword_query)

        # --- GOOGLE ---
        st.subheader(f"🔎 Google Search — {google_n} kết quả ({google_delay:.2f}s)")
        for r in google_results:
            st.markdown(f"### [{r['title']}]({r['link']})")
            st.write(r["snippet"])
            st.write("---")

        # --- YAHOO ---
        st.subheader(f"🟣 Yahoo Search — {yahoo_n} kết quả ({yahoo_delay:.2f}s)")
        for r in yahoo_results:
            st.markdown(f"### [{r['title']}]({r['link']})")
            st.write(r["snippet"])
            st.write("---")
