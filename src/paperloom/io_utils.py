import json, csv
import pandas as pd
from typing import List
from .models import PaperRecord

def write_json(path: str, records: List[PaperRecord]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records],
                  f, ensure_ascii=False, indent=2)

def write_csv(path: str, records: List[PaperRecord]) -> None:
    rows = [r.to_dict() for r in records]
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return
    headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def write_excel(path: str, records: List[PaperRecord]) -> None:
    if not records:
        pd.DataFrame().to_excel(path, index=False)
        return

    df = pd.DataFrame([r.to_dict() for r in records])

    # Scientific typing/normalization
    if "bandgap_ev" in df.columns:
        df["bandgap_ev"] = pd.to_numeric(df["bandgap_ev"], errors="coerce")

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    if "ndr" in df.columns:
        df["ndr"] = df["ndr"].astype("boolean")

    # Magnetic moment split
    if "magnetic_moment" in df.columns:
        mm_val = df["magnetic_moment"].str.extract(r"([0-9]+\.?[0-9]*)", expand=False)
        df["magnetic_moment_value"] = pd.to_numeric(mm_val, errors="coerce")
        df["magnetic_moment_unit"] = df["magnetic_moment"].where(df["magnetic_moment"].notna(), None).apply(
            lambda x: "μB" if isinstance(x, str) else None
        )

    # U-values split
    if "u_values" in df.columns:
        df["U_Zn_d"] = pd.to_numeric(df["u_values"].str.extract(r"U_Zn-d=([0-9.]+)", expand=False), errors="coerce")
        df["U_O_p"]  = pd.to_numeric(df["u_values"].str.extract(r"U_O-p=([0-9.]+)",  expand=False), errors="coerce")

    # Sheets
    bio_cols = ["source_path", "title", "authors", "year", "doi", "keywords", "abstract"]
    sci_cols = ["source_path", "system", "edge", "passivation", "doping", "vacancy",
                "functional", "U_Zn_d", "U_O_p", "kpoints",
                "bandgap_ev", "bandgap_type",
                "magnetic_moment_value", "magnetic_moment_unit",
                "ndr", "doi", "confidence"]  # DOI and confidence included

    df_bio = df[[c for c in bio_cols if c in df.columns]]
    df_sci = df[[c for c in sci_cols if c in df.columns]]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_bio.to_excel(writer, sheet_name="Metadata", index=False)
        df_sci.to_excel(writer, sheet_name="Scientific_Data", index=False)
