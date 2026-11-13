"""Second public ablation into the paper and its plan, by the rules of docs/PUBLIC_ABLATION2.md.

    python sb/paper_apply_public2.py <nolag> <nohold> <noslab> <lag24> <lag96> "<scores read, UTC: 10 Nov, 07:31>" "<write-up UTC>" "<local date-time from date>" [--dry]
"""
import sys

V16 = 0.01031
TEX = r"D:\Projeler\SmartBuildings\paper\main.tex"
DOC = r"D:\Projeler\SmartBuildings\docs\PUBLIC_ABLATION2.md"
args = [a for a in sys.argv[1:] if a != "--dry"]
dry = "--dry" in sys.argv
sc = dict(zip(["nolag", "nohold", "noslab", "lag24", "lag96"], [float(x) for x in args[:5]]))
read_utc, writeup_utc, local_now = args[5], args[6], args[7]
r = {k: v / V16 for k, v in sc.items()}
for k in sc:
    print(f"{k:7s} {sc[k]:.5f}  {r[k]:.3f}")

# Rules (fixed before any score).
if sc["nolag"] >= 0.01134:
    rule1 = "large"
elif sc["nolag"] < 0.01083:
    rule1 = "little"
else:
    rule1 = "modest"
rule2 = sc["noslab"] >= 0.01083
rule3 = all(0.00979 <= sc[k] <= 0.01083 for k in ("lag24", "lag96"))
print("rule 1:", rule1, "| rule 2 (slab matters):", rule2, "| rule 3 (lag need not be exact):", rule3)


def load(p):
    raw = open(p, "rb").read().decode("utf-8")
    return "\r\n" in raw, raw.replace("\r\n", "\n")


def save(p, s, crlf):
    if crlf:
        s = s.replace("\n", "\r\n")
    if not dry:
        open(p, "wb").write(s.encode("utf-8"))


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:80])
    return s.replace(old, new)


f2 = lambda x: f"{x:.2f}"
crlf, s = load(TEX)

# Table 10: a public column.
s = rep(s, "with a two-hour lag the other seven are better).}\\label{tab:what2}",
        "with a two-hour lag the other seven are better). Public: Kaggle public score relative to v16's 0.01031 (one score\neach).}\\label{tab:what2}")
s = rep(s, "\\begin{tabular}{lccc}\\toprule\nVariant of v16 & Loss / v16 & Worse in & Comfort\\\\\\midrule\nv16 & 1 & -- & 0.00048\\\\\n",
        "\\begin{tabular}{lcccc}\\toprule\nVariant of v16 & Loss / v16 & Worse in & Comfort & Public\\\\\\midrule\nv16 & 1 & -- & 0.00048 & 1\\\\\n")
for row, k in (("cool-hold) & 1.14 (1.03--1.30) & 12 of 12 & 0.00173", "nolag"),
               ("heating & 1.05 (1.00--1.12) & 3 of 12 & 0.00099", "nohold"),
               ("model) & 1.16 (1.09--1.27) & 12 of 12 & 0.00189", "noslab"),
               ("of four & 0.99 (0.98--1.00) & 5 of 12 & 0.00040", "lag24"),
               ("eight hours & 1.02 (1.01--1.03) & 12 of 12 & 0.00062", "lag96")):
    s = rep(s, row, row + " & " + f2(r[k]))

# Appendix I: what the public scores say, by the rules.
txt1 = {"large": "a large part of the transfer on the hidden buildings too",
        "modest": "a modest part of the transfer on the hidden buildings",
        "little": "little on the public windows"}[rule1]
add = (
    "\n% docs/PUBLIC_ABLATION2.md (rules written and timestamped before any build; scores read " + read_utc + " UTC).\n"
    f"On the public leaderboard (Table~\\ref{{tab:what2}}, last column; rules fixed before submission) all the delay handling off\n"
    f"scores {f2(r['nolag'])} times v16, so it carries {txt1}; without the slab node the score is {f2(r['noslab'])} times "
    + ("(the slab matters there as well)" if rule2 else "(below the 1.05 that would show the slab matters there)")
    + f", and with a two- or eight-hour lag {f2(r['lag24'])} and {f2(r['lag96'])} times"
    + (" (the lag need not be exact there either)" if rule3 else " (outside the 5\\,\\% band the rule set)")
    + f". Without the cooling rule it is {f2(r['nohold'])} times.\n"
)
s = rep(s, "0.8\\,\\% below v16's on the mean, with an interval that includes 1; v16 did not change.\n",
        "0.8\\,\\% below v16's on the mean, with an interval that includes 1; v16 did not change." + add)

# Timestamps: row and sentence.
row = ("Public ablation 2 (Table~\\ref{tab:what2}) & \\texttt{c90ad08b2e6ca3d6} & 975,121 & 9 Nov, 02:42 & 9 Nov, 00:08 & "
       f"{read_utc} & {writeup_utc}")
i = s.index("\\label{tab:stamps}")
j = s.index("\\bottomrule", i)
k = s.rfind("\n", 0, j) + 1
s = s[:j] + "\n" + row + "\\\\" + s[j:]
s = rep(s, "the sensor-fault test and the public ablation, but", "the sensor-fault test and both public ablations, but")
save(TEX, s, crlf)
print("--- appendix text ---" + add + "--- row ---\n" + row)

# Plan: the result.
crlf, d = load(DOC)
res = (
    f"## Result\n\nScores read {local_now} by `date` (UTC {read_utc}); v16 = 0.01031.\n\n"
    "| arm | public score | / v16 |\n|---|---|---|\n"
    + "".join(f"| {k} | {sc[k]:.5f} | {r[k]:.3f} |\n" for k in sc)
    + f"\nBy the rules: (1) all delay handling off, {r['nolag']:.3f}: {rule1}; (2) slab node "
    + ("matters there" if rule2 else "not shown to matter there (below 1.05)")
    + f" ({r['noslab']:.3f}); (3) lag24 {r['lag24']:.3f}, lag96 {r['lag96']:.3f}: "
    + ("the lag need not be exact there either" if rule3 else "outside the 5 % band")
    + f"; (4) nohold {r['nohold']:.3f}, reported as it comes. In the paper: Table 10 public column, Appendix I, Table 16.\n"
)
d = rep(d, "## Result\n\n(empty until the scores come)\n", res)
save(DOC, d, crlf)
print("--- plan result ---\n" + res)
print("dry run, nothing written" if dry else "written")
