"""Audit helper: count the typeset lines of each main-text paragraph (pages 1-9) in two builds of the paper, to see
which paragraph gained or lost a line.

    python audit/para_lines.py OLD.pdf NEW.pdf
"""
import re
import sys

from pypdf import PdfReader


def lines(path: str) -> list[str]:
    pdf = PdfReader(path)
    out = []
    for i in range(9):
        t = pdf.pages[i].extract_text()
        if i == 8:
            t = t[: t.find("References")]
        out += [f"p{i + 1}| {ln}" for ln in t.splitlines() if not re.fullmatch(r"\d+", ln.strip())]
    return out


def main() -> None:
    a, b = lines(sys.argv[1]), lines(sys.argv[2])
    for name, x in (("old", a), ("new", b)):
        per = {}
        for ln in x:
            per[ln[:2]] = per.get(ln[:2], 0) + 1
        print(name, "lines per page:", per, "total", len(x))


if __name__ == "__main__":
    main()


def hunks() -> None:
    """Changed stretches of typeset lines, old against new, with their line counts."""
    import difflib

    a, b = [x[4:] for x in lines(sys.argv[1])], [x[4:] for x in lines(sys.argv[2])]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    net = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        d = (j2 - j1) - (i2 - i1)
        net += d
        print(f"{d:+d} lines ({i2 - i1} -> {j2 - j1}): old '{(a[i1] if i2 > i1 else '')[:60]}' | new '{(b[j1] if j2 > j1 else '')[:60]}'")
    print("net", net)


if __name__ == "__main__" and "--hunks" in sys.argv:
    hunks()
