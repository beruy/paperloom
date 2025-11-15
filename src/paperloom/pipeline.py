import os, glob, logging
from typing import List
from .models import PaperRecord
from .parse_pdf import read_pdf_text
from .normalize import normalize_text
from .extract_rules import extract_all

IMPORTANT_FIELDS = [
    "functional", "u_values", "kpoints", "bandgap_ev", "bandgap_type",
    "doping", "vacancy", "passivation", "ndr"
]


def _confidence(feats: dict) -> float:
    """Önemli alanların doluluk oranına göre basit bir güven skoru (0..1)."""
    if not IMPORTANT_FIELDS:
        return 0.0
    present = sum(
        1 for k in IMPORTANT_FIELDS
        if feats.get(k) not in (None, "", [], {})
    )
    return round(present / len(IMPORTANT_FIELDS), 3)


def _setup_logger(output_dir: str, level: int) -> logging.Logger:
    """Çıktı klasörüne extraction.log yazan logger kur."""
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "extraction.log")
    logger = logging.getLogger("paperloom.extract")
    logger.setLevel(level)

    # Aynı süreçte birden fazla kez çağrılırsa handler eklemeyi tekrarlama
    if not logger.handlers:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def _sanitize_record(rec: PaperRecord) -> PaperRecord:
    """
    Çıkarılan kaydı fiziksel olarak anlamsız değerlerden temizle.
    (2055 yılı, 50 eV bant aralığı, saçma pasivasyon vb.)
    """
    # Yıl: çok eski veya çok gelecekteyse None
    if rec.year is not None:
        if rec.year < 1970 or rec.year > 2035:
            rec.year = None

    # Band gap: negatif veya aşırı büyükse None
    if rec.bandgap_ev is not None:
        try:
            val = float(rec.bandgap_ev)
            if val < 0.0 or val > 10.0:
                rec.bandgap_ev = None
        except Exception:
            rec.bandgap_ev = None

    # Manyetik moment: makul aralığın dışındaysa None
    if rec.magnetic_moment is not None:
        try:
            num = float(str(rec.magnetic_moment).split()[0])
            if num < 0.0 or num > 10.0:
                rec.magnetic_moment = None
        except Exception:
            rec.magnetic_moment = None

    # Passivasyon: sadece H/F/S kabul et
    if rec.passivation is not None and rec.passivation not in ("H", "F", "S"):
        rec.passivation = None

    # Vacancy: sadece V_Zn veya V_O kalsın
    if rec.vacancy is not None and rec.vacancy not in ("V_Zn", "V_O"):
        rec.vacancy = None

    return rec


def extract_pdfs(
    input_dir: str,
    output_dir: str,
    json_name: str = "znr_dataset.json",
    csv_name: str = "znr_dataset.csv",
    excel_name: str = "znr_dataset.xlsx",
    log_level: str = "INFO",
) -> None:
    """
    Belirtilen klasördeki tüm PDF dosyalarından ZnO odaklı özellikleri çıkarır,
    JSON/CSV/Excel olarak kaydeder ve extraction.log içine işlem günlüğü yazar.
    """
    from .io_utils import write_json, write_csv, write_excel

    os.makedirs(output_dir, exist_ok=True)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = _setup_logger(output_dir, level)

    pdfs = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    records: List[PaperRecord] = []

    logger.info("Starting extraction on %d PDF(s).", len(pdfs))

    for path in pdfs:
        try:
            logger.info("Reading PDF: %s", os.path.basename(path))
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
                extras=None,
            )

            rec = _sanitize_record(rec)
            records.append(rec)
            logger.info(
                "Processed %s (confidence=%.3f)",
                os.path.basename(path),
                rec.confidence if rec.confidence is not None else 0.0,
            )

        except Exception as e:
            logger.exception("Failed on %s: %s", os.path.basename(path), e)

    # Çıktılar
    json_path = os.path.join(output_dir, json_name)
    csv_path = os.path.join(output_dir, csv_name)
    xlsx_path = os.path.join(output_dir, excel_name)

    write_json(json_path, records)
    write_csv(csv_path, records)
    write_excel(xlsx_path, records)

    logger.info("Wrote outputs: %s, %s, %s", json_name, csv_name, excel_name)