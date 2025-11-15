import re
from typing import Dict, Optional

# -----------------------------
#  Basit yardımcı fonksiyonlar
# -----------------------------

def _find(regex: re.Pattern, text: str, group: int = 1) -> Optional[str]:
    """İlk eşleşmeyi döndür (yoksa None)."""
    m = regex.search(text)
    if not m:
        return None
    try:
        return m.group(group).strip()
    except IndexError:
        return None


def _clean_doi(doi: Optional[str]) -> Optional[str]:
    """DOI içindeki fazlalıkları (sondaki noktalama vb.) temizle."""
    if not doi:
        return None
    doi = doi.strip()
    doi = doi.rstrip(").,;\"'")
    return doi


def _extract_year(text: str) -> Optional[str]:
    """
    Metindeki yıllar arasından makul olanı seç.

    - 1970–2035 arası dört haneli yılları toplar.
    - En küçük yılı döndürür (genelde makale yılı ilk geçendir).
    """
    years = [int(m.group(0)) for m in RE_YEAR.finditer(text)]
    years = [y for y in years if 1970 <= y <= 2035]
    if not years:
        return None
    return str(min(years))


def _extract_bandgap(text: str) -> Optional[float]:
    """
    Band aralığı değerini bulmaya çalış.

    - 'bulk' kelimesinin çok yakınında geçen band gap değerlerini öncelikle eler.
    - İlk uygun (bulk olmayan) değeri döndürür, yoksa ilk bulduğunu döndürür.
    """
    candidates = []
    for m in RE_BG.finditer(text):
        full_span = text[max(0, m.start() - 40):m.end() + 40]
        try:
            val = float(m.group(2))
        except Exception:
            continue
        candidates.append((full_span, val))

    if not candidates:
        return None

    # Önce 'bulk' içermeyenleri tercih et
    non_bulk = [v for ctx, v in candidates if "bulk" not in ctx.lower()]
    if non_bulk:
        return non_bulk[0]
    return candidates[0][1]


def _extract_passivation(text: str) -> Optional[str]:
    """
    Kenar pasivasyonunu/terminasyonunu daha muhafazakâr bir şekilde bul.

    - Önce 'hydrogen/fluorine/sulfur' kelimelerine bakar.
    - H/F/S sembollerini ancak yakın çevrede 'passivat', 'terminate' vb. varsa kabul eder.
    """
    # Kelime bazlı: hydrogen / fluorine / sulfur
    m = RE_PASS_WORD.search(text)
    if m:
        word = m.group(1).lower()
        mapping = {"hydrogen": "H", "fluorine": "F", "sulfur": "S"}
        return mapping.get(word)

    # Sembol bazlı: H, F, S ama yakınında 'passivated', 'termination' vs. olsun
    for m in RE_PASS_SYMBOL.finditer(text):
        symbol = m.group(2).upper()
        # Sadece bağlamda 'passiv'/'terminat' vb. geçtiyse kabul et
        ctx = m.group(1).lower()
        if any(k in ctx for k in ("passiv", "terminat", "edge")):
            if symbol in ("H", "F", "S"):
                return symbol

    return None


def _extract_doi(text: str) -> Optional[str]:
    """Metinden DOI’yi yakala ve temizle."""
    m = RE_DOI.search(text)
    if not m:
        return None
    return _clean_doi(m.group(1))


# -----------------------------
#  Regex tanımları
# -----------------------------

# --- Basit metadata desenleri ---
# Başlık için fallback: büyük harfle başlayan, makul uzunlukta bir satır,
# hemen altında isim gibi duran satırlar olsun.
RE_TITLE_FALLBACK = re.compile(
    r"(?m)^([A-Z][^\n]{10,150})\n"
    r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*[, ]*){1,6}\n",  # yazar satır(lar)ı
)

# Yazarlar fallback: "Soyad, İsim" biçimli bir satır grubu
RE_AUTH_FALLBACK = re.compile(
    r"(?m)^((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*[, ]*){1,6})\n",
)

# Abstract için fallback: 'Abstract' kelimesinden sonra gelen parça
RE_ABS_FALLBACK = re.compile(
    r"(?is)\babstract\b[:\s]*([^\n].+?)(?:\n\s*\bkeywords?\b|\n\s*1\.\s*introduction\b|\n\s*introduction\b)",
)

RE_TITLE = re.compile(
    r"(?m)^(?:title|paper title)[:\s]*([^\n]{10,200})$",
    re.IGNORECASE,
)

RE_DOI = re.compile(
    r"""
    (?:doi[:\s]*|https?://doi\.org/)?   # opsiyonel 'doi:' ya da doi.org
    (                                   # grup 1: asıl DOI
        10\.\d{4,9}/\S+?                # DOI çekirdeği
    )
    (?=[\s\)\].,;\"']|$)                # ardından boşluk / noktalama / satır sonu
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 1970–2059 aralığını hedefleyen kaba filtre; sonradan _extract_year ile daraltıyoruz.
RE_YEAR = re.compile(r"\b(19[7-9]\d|20[0-5]\d)\b")

RE_AUTH = re.compile(
    r"(?m)^(?:authors?)[:\s]*([^\n]{5,200})$",
    re.IGNORECASE,
)

RE_KEYS = re.compile(
    r"(?m)^(?:keywords?)[:\s]*([^\n]{5,300})$",
    re.IGNORECASE,
)

RE_ABS = re.compile(
    r"(?s)(?:^abstract\b[:\s]*)(.+?)(?:\n\s*\b(?:keywords?|introduction|1\.|I\.)\b)",
    re.IGNORECASE,
)

# --- ZnO & yöntemler ---
RE_SYS = re.compile(
    r"ZnO\s+(nanoribbon|cluster|nanocluster|thin\s*film)s?",
    re.IGNORECASE,
)

RE_EDGE = re.compile(
    r"\b(zigzag|armchair|ZZ|AC)\b",
    re.IGNORECASE,
)

# Kelime bazlı pasivasyon (hydrogen / fluorine / sulfur)
RE_PASS_WORD = re.compile(
    r"\b(hydrogen|fluorine|sulfur)\b",
    re.IGNORECASE,
)

# Sembol bazlı pasivasyon (H/F/S) – ama bağlamda 'passivated', 'termination' vb. aranacak
RE_PASS_SYMBOL = re.compile(
    r"([^.]{0,40}?(?:passivated?|passivation|terminated?|edge))[^A-Za-z]{0,10}\b(H|F|S)\b",
    re.IGNORECASE,
)

RE_DOP = re.compile(
    r"\b(Co|Mn|Fe|Ni|Cu|Al|Ga|In|B|N|P|S|F)\s*(-?doped|doping)\b",
    re.IGNORECASE,
)

RE_VAC = re.compile(
    r"\b(V[_\- ]?Zn|V[_\- ]?O|zinc\s+vacancy|oxygen\s+vacancy)\b",
    re.IGNORECASE,
)

RE_FUNC = re.compile(
    r"\b(PBE|LDA|GGA|HSE|PBE0|SCAN|B3LYP|LDA\+U|GGA\+U)\b",
    re.IGNORECASE,
)

RE_UVAL = re.compile(
    r"""
    \bU\s*(?:\(Zn\s*[-_]?d\)|Zn[-_ ]?d)\s*=\s*([0-9.]+)\s*eV
    .*?
    (?:U\s*(?:\(O\s*[-_]?p\)|O[-_ ]?p)\s*=\s*([0-9.]+)\s*eV)?
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

RE_KPTS = re.compile(
    r"\b(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)\b",
)

RE_BG = re.compile(
    r"\b(band\s*gap|bandgap)\b[^\n]{0,40}?(\d\.\d{1,2})\s*eV",
    re.IGNORECASE,
)

RE_BGTP = re.compile(
    r"\b(direct|indirect)\s+(?:band\s*gap|bandgap)\b",
    re.IGNORECASE,
)

RE_MM = re.compile(
    r"\b([0-9]+\.?[0-9]*)\s*(?:μB|muB|mu_B|Bohr\s*magneton)\b",
    re.IGNORECASE,
)

RE_NDR = re.compile(
    r"negative\s+differential\s+resistance",
    re.IGNORECASE,
)


# -----------------------------
#  Ana çıkarım fonksiyonu
# -----------------------------

def extract_all(text: str) -> Dict[str, object]:
    """
    PDF’ten normalize edilmiş metni alır, metadata ve ZnO odaklı
    bilimsel özellikleri sözlük olarak döndürür.
    """
    out: Dict[str, object] = {}

    # --- Metadata ----
    out["title"] = _find(RE_TITLE, text)
    if not out["title"]:
        out["title"] = _find(RE_TITLE_FALLBACK, text)

    out["doi"] = _extract_doi(text)
    out["year"] = _extract_year(text)

    out["authors"] = _find(RE_AUTH, text)
    if not out["authors"]:
        out["authors"] = _find(RE_AUTH_FALLBACK, text)

    out["keywords"] = _find(RE_KEYS, text)

    mabs = RE_ABS.search(text)
    if not mabs:
        mabs = RE_ABS_FALLBACK.search(text)
    if mabs:
        out["abstract"] = mabs.group(1).strip()

    # --- ZnO sistem bilgisi ---
    sysm = RE_SYS.search(text)
    out["system"] = sysm.group(0) if sysm else None

    edge = _find(RE_EDGE, text)
    if edge:
        if edge.upper() in ("ZZ", "AC"):
            out["edge"] = edge.upper()
        else:
            out["edge"] = edge.lower()

    out["passivation"] = _extract_passivation(text)

    dm = RE_DOP.search(text)
    out["doping"] = dm.group(1) if dm else None

    vm = RE_VAC.search(text)
    if vm:
        v = vm.group(1).upper().replace(" ", "").replace("-", "_")
        if v in ("VZN", "V_ZN"):
            v = "V_Zn"
        if v in ("VO", "V_O"):
            v = "V_O"
        out["vacancy"] = v

    out["functional"] = _find(RE_FUNC, text)

    um = RE_UVAL.search(text)
    if um:
        u_zn, u_o = um.group(1), um.group(2)
        out["u_values"] = f"U_Zn-d={u_zn} eV" + (f"; U_O-p={u_o} eV" if u_o else "")

    km = RE_KPTS.search(text)
    if km:
        out["kpoints"] = "x".join(km.groups())

    # Band gap (bulk bağlamını mümkün olduğunca ele)
    bg_val = _extract_bandgap(text)
    if bg_val is not None:
        out["bandgap_ev"] = bg_val

    bgt = RE_BGTP.search(text)
    out["bandgap_type"] = bgt.group(1).lower() if bgt else None

    mm = RE_MM.search(text)
    out["magnetic_moment"] = (mm.group(1) + " μB") if mm else None

    out["ndr"] = bool(RE_NDR.search(text))

    return out