import yake

def extract_keywords_yake(doc, top_n=10, keyphrase_len=3, language="en"):

    kw = yake.KeywordExtractor(
        lan=language,
        n=keyphrase_len,
        top=top_n
    )

    raw = kw.extract_keywords(doc)
    cleaned = []

    for item in raw:
        # item có thể là (score, keyword) hoặc (keyword, score)
        a, b = item

        # TH1: dạng YAKE chuẩn → (score:float, keyword:str)
        if isinstance(a, (float, int)) and isinstance(b, str):
            cleaned.append((b, float(a)))

        # TH2: dạng YAKE lỗi → (keyword:str, score:float)
        elif isinstance(b, (float, int)) and isinstance(a, str):
            cleaned.append((a, float(b)))

        # TH3: lỗi hoàn toàn → bỏ qua
        else:
            continue

    return cleaned
