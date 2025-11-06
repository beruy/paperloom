from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class PaperRecord:
    source_path: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    keywords: Optional[str] = None
    abstract: Optional[str] = None
    # ZnO-focused scientific features
    system: Optional[str] = None                 # e.g., 'ZnO nanoribbon', 'ZnO cluster'
    edge: Optional[str] = None                   # ZZ / AC
    passivation: Optional[str] = None            # S / F / H
    doping: Optional[str] = None                 # e.g., 'Co', 'Mn'
    vacancy: Optional[str] = None                # V_Zn / V_O
    functional: Optional[str] = None             # PBE/LDA/HSE/etc.
    u_values: Optional[str] = None               # e.g., 'U_Zn-d=6.5 eV; U_O-p=3.5 eV'
    kpoints: Optional[str] = None                # e.g., '5x1x1', '9×9×1'
    bandgap_ev: Optional[float] = None           # numeric (eV)
    bandgap_type: Optional[str] = None           # direct/indirect
    magnetic_moment: Optional[str] = None        # e.g., '1.98 μB'
    ndr: Optional[bool] = None                   # Negative Differential Resistance mentioned?
    confidence: Optional[float] = None           # simple heuristic confidence score (0..1)
    extras: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
