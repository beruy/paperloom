import re, unicodedata

LIGATURES = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u00ad": "",   # soft hyphen
}

def normalize_text(text: str) -> str:
    # Unicode normalize
    text = unicodedata.normalize("NFKC", text or "")
    # Replace common ligatures/soft hyphens
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    # Join hyphenated line breaks: e.g., "nano-\nbon" -> "nanobon"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    # Normalize k-point separator to x
    text = re.sub(r"(\d)\s*×\s*(\d)", r"\1x\2", text)
    text = re.sub(r"(\d)\s*[xX]\s*(\d)\s*[xX]\s*(\d)", r"\1x\2x\3", text)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()
