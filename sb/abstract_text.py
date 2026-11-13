"""Print the plain-text abstract for OpenReview from paper/main.tex (the two must match; hosts' template rule).

    python -m sb.abstract_text
"""

from __future__ import annotations

import re
from pathlib import Path


def abstract() -> str:
    s = Path("paper/main.tex").read_text(encoding="utf-8")
    body = s.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
    body = "\n".join(line for line in body.split("\n") if not line.lstrip().startswith("%"))
    body = body.replace(r"\,\%", " %").replace("--", "-")
    return re.sub(r"\s+", " ", body).strip()


if __name__ == "__main__":
    a = abstract()
    print(a)
    print("characters:", len(a), "backslashes left:", a.count("\\"))
