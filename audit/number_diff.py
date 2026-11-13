"""Audit helper: which numbers appear in one version of the paper source and not in the other? Compares the multiset of
numeric tokens (comments removed) of paper/main.tex and paper/app_trained.tex between a git revision and the working tree.

    python audit/number_diff.py <git revision>
"""
import re
import subprocess
import sys
from collections import Counter

BS = chr(92)  # a backslash, spelled this way so that shells cannot mangle it


def numbers(text: str) -> Counter:
    text = "\n".join(line for line in text.split("\n") if not line.lstrip().startswith("%"))
    text = re.sub(BS + BS + r"(ref|label|cite|includegraphics)[{][^}]*[}]", " ", text)
    text = text.replace("{,}", "").replace(BS + ",", " ")
    return Counter(re.findall(r"(?<![\w.])\d+(?:[.,]\d+)*(?![\w])", text))


def main() -> None:
    rev = sys.argv[1]
    for f in ("paper/main.tex", "paper/app_trained.tex"):
        old = subprocess.run(["git", "show", f"{rev}:{f}"], capture_output=True).stdout.decode("utf-8")
        new = open(f, encoding="utf-8").read()
        a, b = numbers(old), numbers(new)
        print(f"{f}: {sum(a.values())} numbers before, {sum(b.values())} now")
        print("  only in the old version:", dict(sorted((a - b).items())))
        print("  only in the new version:", dict(sorted((b - a).items())))


if __name__ == "__main__":
    main()
