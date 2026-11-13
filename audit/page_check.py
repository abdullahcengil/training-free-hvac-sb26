"""Audit helper: where does the main text end? Prints the page of the 'AI assistance, code and compute' section, the
page on which the references start, the total page count, and the overfull count of main.log.

    python audit/page_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

PAPER = Path(__file__).resolve().parents[1] / "paper"


def main() -> None:
    pdf = PdfReader(str(PAPER / "main.pdf"))
    pages = [p.extract_text() or "" for p in pdf.pages]
    flat = [re.sub(r"\s+", " ", t) for t in pages]
    ai = [i + 1 for i, t in enumerate(flat) if "AI assistance, code and compute" in t]
    refs = [i + 1 for i, t in enumerate(flat) if re.search(r"\bReferences\b", t)]
    end = [i + 1 for i, t in enumerate(flat) if "one laptop with 16 GB of memory" in t]
    log = (PAPER / "main.log").read_text(encoding="utf-8", errors="replace")
    over = len(re.findall(r"Overfull", log))
    undef = len(re.findall(r"undefined", log))
    print(f"pages {len(pages)}; 'AI assistance' heading on page {ai}; its last sentence on page {end}; "
          f"'References' on page {refs[:1]}; Overfull {over}; undefined {undef}")
    if "-v" in sys.argv:
        t = pages[7]
        k = t.find("AI assistance, code and compute")
        print("--- page 8 from the AI section to the end of the page:")
        print(t[k:][:1500])
    # Room left on page 8: the text block ends at y = 72 pt; lines are 10.9 pt apart.
    ys: list[float] = []

    def visit(text, cm, tm, font, size):
        y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
        if text.strip() and not re.fullmatch(r"\d+", text.strip()) and y > 60:
            ys.append(y)

    pdf.pages[7].extract_text(visitor_text=visit)
    room = (min(ys) - 72.0) / 10.9
    print(f"page 8: lowest body line at y={min(ys):.1f} pt (block ends at 72.0): room for {room:.1f} more lines")
    ok = ai == [8] and end and end[0] == 8 and over == 0 and undef == 0
    print("PAGE CHECK", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
