import re
from typing import Dict, Optional

# --- Simple metadata patterns ---
RE_TITLE = re.compile(r"(?m)^(?:title|paper title)[:\s]*([^\n]{10,200})$", re.I)
RE_DOI   = re.compile(r"\bdoi[:\s]*([0-9.]{2,}/\S+)", re.I)
RE_YEAR  = re.compile(r"\b(20[0-5][0-9]|19[7-9][0-9])\b")
RE_AUTH  = re.compile(r"(?m)^(?:authors?)[:\s]*([^\n]{5,200})$", re.I)
RE_KEYS  = re.compile(r"(?m)^(?:keywords?)[:\s]*([^\n]{5,300})$", re.I)
RE_ABS   = re.compile(r"(?s)(?:^abstract\b[:\s]*)(.+?)(?:\n\s*\b(?:keywords?|introduction|1\.|I\.)\b)", re.I)

# --- ZnO & methods ---
RE_SYS  = re.compile(r"ZnO\s+(nanoribbon|cluster|nanocluster|thin\s*film)s?", re.I)
RE_EDGE = re.compile(r"\b(zigzag|armchair|ZZ|AC)\b", re.I)
RE_PASS = re.compile(r"\b(passivated?\s+with\s+)?(S|F|H|hydrogen|fluorine|sulfur)\b", re.I)
RE_DOP  = re.compile(r"\b(Co|Mn|Fe|Ni|Cu|Al|Ga|In|B|N|P|S|F)\s*(-?doped|doping)\b", re.I)
RE_VAC  = re.compile(r"\b(V[_\- ]?Zn|V[_\- ]?O|zinc\s+vacancy|oxygen\s+vacancy)\b", re.I)
RE_FUNC = re.compile(r"\b(PBE|LDA|GGA|HSE|PBE0|SCAN|B3LYP|LDA\+U|GGA\+U)\b", re.I)
RE_UVAL = re.compile(r"\bU\s*(?:\(Zn\s*[-_]?d\)|Zn[-_ ]?d)\s*=\s*([0-9.]+)\s*eV.*?(?:U\s*(?:\(O\s*[-_]?p\)|O[-_ ]?p)\s*=\s*([0-9.]+)\s*eV)?", re.I)
RE_KPTS = re.compile(r"\b(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)\b")
RE_BG   = re.compile(r"\b(band\s*gap|bandgap)\b[^\n]{0,40}?(\d\.\d{1,2})\s*eV", re.I)
RE_BGTP = re.compile(r"\b(direct|indirect)\s+(?:band\s*gap|bandgap)\b", re.I)
RE_MM   = re.compile(r"\b([0-9]+\.?[0-9]*)\s*(?:μB|muB|mu_B|Bohr\s*magneton)\b", re.I)
RE_NDR  = re.compile(r"negative\s+differential\s+resistance", re.I)

def _find(rex,text: str) -> Optional[str]:
    m = rex.search(text)
    return m.group(1).strip() if m else None

def extract_all(text: str) -> Dict[str, object]:
    out: Dict[str, object] = {}
    out["title"]    = _find(RE_TITLE, text)
    out["doi"]      = _find(RE_DOI, text)
    out["year"]     = _find(RE_YEAR, text)
    out["authors"]  = _find(RE_AUTH, text)
    out["keywords"] = _find(RE_KEYS, text)

    mabs = RE_ABS.search(text)
    if mabs:
        out["abstract"] = mabs.group(1).strip()

    # ZnO specifics
    sysm = RE_SYS.search(text)
    out["system"] = sysm.group(0) if sysm else None

    edge = _find(RE_EDGE, text)
    if edge and edge.upper() in ("ZZ", "AC"):
        out["edge"] = edge.upper()
    elif edge:
        out["edge"] = edge.lower()

    pm = RE_PASS.search(text)
    if pm:
        pv = pm.group(2).lower()
        mapping = {"hydrogen": "H", "fluorine": "F", "sulfur": "S"}
        out["passivation"] = mapping.get(pv, pv.upper())

    dm = RE_DOP.search(text)
    out["doping"] = dm.group(1) if dm else None

    vm = RE_VAC.search(text)
    if vm:
        v = vm.group(1).upper().replace(" ", "").replace("-", "_")
        if v in ("VZN", "V_ZN"): v = "V_Zn"
        if v in ("VO", "V_O"):   v = "V_O"
        out["vacancy"] = v

    out["functional"] = _find(RE_FUNC, text)

    um = RE_UVAL.search(text)
    if um:
        u_zn, u_o = um.group(1), um.group(2)
        out["u_values"] = f"U_Zn-d={u_zn} eV" + (f"; U_O-p={u_o} eV" if u_o else "")

    km = RE_KPTS.search(text)
    if km:
        out["kpoints"] = "x".join(km.groups())

    bgm = RE_BG.search(text)
    if bgm:
        try:
            out["bandgap_ev"] = float(bgm.group(2))
        except Exception:
            pass

    bgt = RE_BGTP.search(text)
    out["bandgap_type"] = bgt.group(1).lower() if bgt else None

    mm = RE_MM.search(text)
    out["magnetic_moment"] = (mm.group(1) + " μB") if mm else None

    out["ndr"] = bool(RE_NDR.search(text))

    return out
    