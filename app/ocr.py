from pathlib import Path

from PIL import Image, ImageOps
import pytesseract

from app.config import OCR_LANG


def read_image_text(file_path: str, lang: str = OCR_LANG) -> str:
    image_path = Path(file_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")

    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
