"""Rewrite the final OpenReview fields at the top of docs/PAPER_PLAN.md from paper/main.tex (abstract via
sb.abstract_text), with the date and time given from `date`.

    python -m sb.update_openreview_fields "10 Nov 2026 08:40" "after the second public ablation"
"""

import sys

from sb.abstract_text import abstract

TLDR = ("A training-free HVAC controller learns five numbers per zone online. After a fix to its failed first blind "
        "round, it beat the strongest official baseline in all 122 scenarios outside its development set. Without "
        "learning, its loss nearly triples.")


def main() -> None:
    when, why = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    p = "docs/PAPER_PLAN.md"
    raw = open(p, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    assert lines[2].startswith("## FINAL OpenReview fields")
    assert lines[5].startswith("- Abstract (plain text")
    assert lines[6].startswith("- TLDR (")
    lines[2] = (f"## FINAL OpenReview fields (copy from here; {when} by `date`{', ' + why if why else ''}; "
                "every older abstract or TLDR below is superseded)")
    lines[5] = f'- Abstract (plain text, generated from main.tex by `python -m sb.abstract_text`, {when}): "{abstract()}"'
    assert len(TLDR) <= 250
    lines[6] = f'- TLDR ({len(TLDR)} characters, limit 250): "{TLDR}"'
    s = "\n".join(lines)
    if crlf:
        s = s.replace("\n", "\r\n")
    open(p, "wb").write(s.encode("utf-8"))
    print("ok: abstract", len(abstract()), "characters, TLDR", len(TLDR))


if __name__ == "__main__":
    main()
