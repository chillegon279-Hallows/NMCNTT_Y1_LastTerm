import numpy as np
from paddleocr import PaddleOCR

# =============================
# Cache OCR model để không load lại
# =============================
_ocr_cache = {}

def load_ocr(lang="en"):
    """
    Load mô hình OCR với PaddleOCR.
    Cache để tái sử dụng, tránh load nhiều lần.
    """
    if lang not in _ocr_cache:
        _ocr_cache[lang] = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=True)
    return _ocr_cache[lang]

# =============================
# Tính diện tích box
# =============================
def box_area(poly):
    """
    poly = [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    width = distance giữa điểm 0 và 1
    height = distance giữa điểm 0 và 3
    """
    w = np.linalg.norm(np.array(poly[1]) - np.array(poly[0]))
    h = np.linalg.norm(np.array(poly[3]) - np.array(poly[0]))
    return w * h

# =============================
# OCR chính (tối ưu)
# =============================
def run_ocr(image, lang="en", resize_max_dim=1024):
    """
    Chạy OCR trên ảnh đã preprocess.
    Trả về text sắp xếp theo kích thước box (chữ to → nhỏ).
    - resize_max_dim: tối ưu ảnh lớn để tăng tốc OCR
    """
    ocr = load_ocr(lang)

    # Resize ảnh nếu quá lớn để giảm thời gian tính toán
    w, h = image.size
    scale = 1.0
    if max(w, h) > resize_max_dim:
        scale = resize_max_dim / max(w, h)
        new_size = (int(w * scale), int(h * scale))
        image = image.resize(new_size)

    img_array = np.array(image)
    result = ocr.ocr(img_array, cls=True)

    if not result or not result[0]:
        return ""

    boxes = result[0]

    # Tính diện tích box nhanh bằng numpy
    areas = np.array([box_area(box[0]) for box in boxes])
    texts = [box[1][0] for box in boxes]

    # Sắp xếp giảm dần theo diện tích
    indices = np.argsort(-areas)
    paragraph = " ".join([texts[i] for i in indices])

    return paragraph.strip()
