# Paperloom
**Research-grade PDF extraction**  
Licensed under **CC BY-NC 4.0**

Paperloom is a modular scientific extraction pipeline designed to process
materials-science research PDFs.

✅ Advanced extraction rules  
✅ Scientific metadata normalization  
✅ Multi-sheet Excel export  
✅ DOI-aware data model  
✅ Plugin system (`paperloom-excelx`)  
✅ CLI architecture with Typer  
✅ Clean package structure with `src/` layout  

---

## 🌐 Key Features
- **PDF → structured dataset** (`JSON`, `CSV`, `XLSX`)
- Scientific entities:
  - Band gap (direct/indirect)
  - Doping / passivation types  
  - Vacancy models (V_Zn, V_O)
  - U-values (Hubbard U for Zn-d, O-p)
  - k-points, functionals, confidence levels
- Extracts metadata:
  - Title, year, authors, DOI
  - Keywords
  - Extracted abstract
- **Excel export plugin** with multi-sheet format:
  - `Metadata`
  - `Scientific_Data`
- Plugin framework for custom extensions

---

# 📦 Installation

### 1. Install Paperloom (core)
```bash
pip install -e .
