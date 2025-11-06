import os, glob, logging
from typing import List
from .models import PaperRecord
from .parse_pdf import read_pdf_text
from .normalize import normalize_text
from .extract_rules import extract_all
from .io_utils import write_json, write_csv, write_excel

IMPORTANT_FIELDS = [
    "functional", "u_values", "kpoints", "bandgap_ev", "bandgap_type",
    "doping", "vacancy", "passivation", "ndr"
]

def _confidence(feats: dict) -> float:
    if not IMPORTANT_FIELDS:
        return 0.0
    present = sum(1 for k in IMPORTANT_FIELDS if feats.get(k) not in (None, "", []))
    return round(present / len(IMPORTANT_FIELDS), 3)

def _setup_logger(output_dir: str, level: int) -> logging.Logger:
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "extraction.log")
    logger = logging.getLogger("paperloom.extract")
    logger.setLevel(level)
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

def extract_pdfs(input_dir: str, output_dir: str,
                 json_name: str = "znr_dataset.json",
                 csv_name: str = "znr_dataset.csv",
                 excel_name: str = "znr_dataset.xlsx",
                 log_level: str = "INFO") -> None:
    os.makedirs(output_dir, exist_ok=True)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = _setup_logger(output_dir, level)

    pdfs = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    records: List[PaperRecord] = []
    logger.info("Starting extraction on %d PDF(s).", len(pdfs))

    for path in pdfs:
        try:
            raw = read_pdf_text(path)
            norm = normalize_text(raw)
            feats = extract_all(norm)
            conf = _confidence(feats)

            rec = PaperRecord(
                source_path=os.path.basename(path),
                title=feats.get("title"),
                authors=feats.get("authors"),
                year=int(feats["year"]) if feats.get("year") else None,
                doi=feats.get("doi"),
                keywords=feats.get("keywords"),
                abstract=feats.get("abstract"),
                system=feats.get("system"),
                edge=feats.get("edge"),
                passivation=feats.get("passivation"),
                doping=feats.get("doping"),
                vacancy=feats.get("vacancy"),
                functional=feats.get("functional"),
                u_values=feats.get("u_values"),
                kpoints=feats.get("kpoints"),
                bandgap_ev=feats.get("bandgap_ev"),
                bandgap_type=feats.get("bandgap_type"),
                magnetic_moment=feats.get("magnetic_moment"),
                ndr=feats.get("ndr"),
                confidence=conf,
                extras=None
            )
            records.append(rec)
            logger.info("Processed %s (confidence=%.3f)", os.path.basename(path), conf)
        except Exception as e:
            logger.exception("Failed on %s: %s", path, e)

    write_json(os.path.join(output_dir, json_name), records)
    write_csv(os.path.join(output_dir, csv_name), records)
    write_excel(os.path.join(output_dir, excel_name), records)
    logger.info("Wrote outputs: %s, %s, %s", json_name, csv_name, excel_name)
