from typing import Optional
from PyPDF2 import PdfReader

def read_pdf_text(path: str, max_pages: Optional[int] = None) -> str:
    reader = PdfReader(path)
    texts = []
    for i, p in enumerate(reader.pages):
        if max_pages is not None and i >= max_pages:
            break
        try:
            texts.append(p.extract_text() or "")
        except Exception:
            texts.append("")
    return "\n".join(texts)
