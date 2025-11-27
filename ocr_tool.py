import numpy as np
from paddleocr import PaddleOCR

def load_ocr(lang="en"):
    return PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=True)

def run_ocr(image, lang="en"):
    ocr = load_ocr(lang)
    result = ocr.ocr(np.array(image), cls=True)

    if result and result[0]:
        texts = [line[-1][0] for line in result[0]]
        return "\n".join(texts)
    return ""
