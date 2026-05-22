#!/usr/bin/env python3
"""Render the HTML resume to a polished, ATS-friendly PDF."""
from pathlib import Path
from weasyprint import HTML

HERE = Path(__file__).parent
SRC = HERE / "resume.html"
OUT = HERE.parent / "Resume_Swetha_Suhasini_Indur_MedicalWriter.pdf"

HTML(filename=str(SRC)).write_pdf(target=str(OUT))
print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")
