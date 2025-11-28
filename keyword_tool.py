import yake
from functools import lru_cache

# --------------------------
# Cache YAKE extractor để tăng tốc
# --------------------------
@lru_cache(maxsize=16)
def get_yake_extractor(language: str, keyphrase_len: int, top_n: int):
    return yake.KeywordExtractor(
        lan=language,
        n=keyphrase_len,
        top=top_n
    )

def extract_keywords_yake(doc, top_n=10, keyphrase_len=3, language="en", first_words_count=3):
    # Ưu tiên các từ khóa
    priority_keywords = ["CGV"]
    
    # Lấy các từ đầu dòng
    lines = doc.split("\n")
    for line in lines:
        words = line.strip().split()
        if not words:
            continue
        selected = words[:first_words_count]
        priority_keywords.extend(selected)

    # Sử dụng extractor cache
    kw_extractor = get_yake_extractor(language, keyphrase_len, top_n)
    raw = kw_extractor.extract_keywords(doc)

    # Làm sạch kết quả YAKE
    cleaned = []
    for item in raw:
        a, b = item
        if isinstance(a, (float, int)) and isinstance(b, str):
            cleaned.append((b, float(a)))
        elif isinstance(b, (float, int)) and isinstance(a, str):
            cleaned.append((a, float(b)))
        else:
            continue

    # Gộp ưu tiên + YAKE
    seen = set()
    final_keywords = []
    for w in priority_keywords:
        w = w.strip()
        if w and w not in seen:
            final_keywords.append((w, 0.0))
            seen.add(w)
    for kw, score in cleaned:
        if kw not in seen:
            final_keywords.append((kw, score))
            seen.add(kw)

    return final_keywords[:top_n]
