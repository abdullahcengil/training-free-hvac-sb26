"""Put the trained-controller result into the paper, from results/rl_test/summary.json (written by
`python -m sb.run_trained --read`), by the reading rules of docs/TRAINED_BASELINE.md. Prints every inserted text.

    python sb/paper_apply_trained.py "<first result UTC, e.g. 10 Nov, 17:02>" "<write-up UTC>" [--dry]

The case "trained policy better than v16" is not handled here: the plan then requires the abstract and the conclusion
to say so, which is done by hand.
"""
import json
import sys

import os

SUM = os.environ.get("TRAINED_SUMMARY", r"D:\SmartBuildings_data\results\rl_test\summary.json")
TEX = r"D:\Projeler\SmartBuildings\paper\main.tex"
APP = r"D:\Projeler\SmartBuildings\paper\app_trained.tex"
first, writeup = sys.argv[1], sys.argv[2]
dry = "--dry" in sys.argv

d = json.load(open(SUM))
b = d["budget"]
tp, tplo, tphi = d["trained_over_pid"]
nbp = d["trained_below_pid"]
tv, tvlo, tvhi = d["trained_over_v16"]
vbt = d["v16_below_trained"]
vp = d["v16_over_pid"][0]
hours, steps = b["hours"], b["train_steps"] / 1e6

rule1 = tp <= 0.95 and nbp >= 9
if tv < 1.0:
    raise SystemExit(f"trained / v16 = {tv:.3f} < 1: the plan requires the abstract and conclusion to say so; edit by hand")
rule2 = "strong" if (vbt >= 10 and tv >= 1.5) else "modest"
print(f"rule 1 (real competitor): {'yes' if rule1 else 'no'} (trained/pid {tp:.3f}, below pid in {nbp} of 12)")
print(f"rule 2: {rule2} (trained/v16 {tv:.3f}, v16 lower in {vbt} of 12)")


def load(p):
    raw = open(p, "rb").read().decode("utf-8")
    return raw, "\r\n" in raw, raw.replace("\r\n", "\n")


def save(p, s, crlf):
    if crlf:
        s = s.replace("\n", "\r\n")
    if not dry:
        open(p, "wb").write(s.encode("utf-8"))


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:80])
    return s.replace(old, new)


# 1. Main text, end of Section 4.1.
para = (
    "\n\n% docs/TRAINED_BASELINE.md (plan and reading rules timestamped before training); sb/run_trained.py --read\n"
    "% (results/rl_test/summary.json).\n"
    "We also trained a policy, since the starter kit ships none: a residual on pid\\_water with two small networks\n"
    "shared by all zones and air handlers, trained by PPO on five training buildings for "
    f"{hours:.0f} hours ({steps:.1f} million\n"
    "simulator steps; Appendix~\\ref{app:trained}). On the twelve buildings of Table~\\ref{tab:what} its loss is "
    f"{tp:.2f} times\n"
    f"pid\\_water's (below it in {nbp} of 12{'' if rule1 else '; no reliable gain within this budget'}) and "
    f"{tv:.1f} times v16's (v16 lower in {vbt} of 12).\n"
)
raw, crlf, s = load(TEX)
s = rep(s, "building size may be\n(Section~\\ref{sec:big}).\n\n\\subsection{What carries the transfer?}",
        "building size may be\n(Section~\\ref{sec:big})." + para + "\n\\subsection{What carries the transfer?}")
print("\n--- Section 4.1 paragraph ---" + para)

# 2. Limitations.
old_lim = ("Our public score is far from the top of the leaderboard, and we\ncompare with no trained policy (the starter kit "
           "ships none), so the evidence is against the official baselines only.")
new_lim = ("Our public score is far from the top of the leaderboard, and the trained\ncomparison (one architecture, "
           "budget and seed) says little about what trained control can reach.")
s = rep(s, old_lim, new_lim)
print("--- Limitations ---\n" + new_lim)

# 3. The appendix goes in before the timestamps.
s = rep(s, "\\section{Timestamps of the plans}\\label{app:stamps}", "\\input{app_trained}\n\n\\section{Timestamps of the plans}\\label{app:stamps}")

# 4. Timestamp table row and the sentence about it.
row = (f"Trained policy (App.~\\ref{{app:trained}}) & \\texttt{{289e165b14900a7d}} & 975,121 & 9 Nov, 02:42 & 9 Nov, 02:27 & "
       f"{first} & {writeup}\\\\")
i = s.index("\\label{tab:stamps}")
j = s.index("\\bottomrule", i)
k = s.rfind("\n", 0, j) + 1
line = s[k:j]
s = s[:j] + "\n" + row + s[j:]
print("--- Table row ---\n" + row)

# 4b. The sources table (Appendix "Where the numbers come from") gets the trained table and figure.
src_key = "Table~\\ref{tab:stamps} & \\texttt{opengrid.ots verify}"
src_row = ("Table~\\ref{tab:trained}; Fig.~\\ref{fig:trained} & \\texttt{run\\_trained.py} (\\texttt{-{}-read}), "
           "\\texttt{fig\\_trained.py} & training logs \\texttt{results/rl/main}, test runs \\texttt{results/rl\\_test}; "
           "\\texttt{TRAINED\\_BASELINE.md}\\\\\n")
s = rep(s, src_key, src_row + src_key)
print("--- Sources row ---\n" + src_row)
save(TEX, s, crlf)

# 5. Appendix: budget and the outcome by the plan's rules.
raw, crlf, a = load(APP)
a = a.replace("BUDGET_STEPS", f"{steps:.1f} million").replace("BUDGET_HOURS", f"{hours:.0f}")
a = a.replace("BUDGET_BEST", f"{b['best_it']}").replace("BUDGET_VAL", f"{b['best_val']:.5f}")
assert "BUDGET_" not in a
outcome = (
    "\n% Reading rules of docs/TRAINED_BASELINE.md, fixed before training.\n"
    "By the rules fixed before training, a real improvement on pid\\_water needs at most 0.95 times its loss and a lower\n"
    f"loss in at least 9 of 12 scenarios: the trained policy reached {tp:.2f} times (95\\,\\% interval {tplo:.2f}--{tphi:.2f}), "
    f"lower in {nbp} of 12, so it\n"
    + ("is one. " if rule1 else "is not one within this budget. ")
    + ("v16 beats it with this budget: v16 is lower in " if rule2 == "strong" else "v16 is modestly better: lower in ")
    + f"{vbt} of 12, and the trained policy loses {tv:.1f} times as much\n"
    f"(interval {tvlo:.1f}--{tvhi:.1f}). Before the test we expected 0.6--1.0 times pid\\_water's loss and a factor of 3--5 to v16 (our\n"
    "opinion, written in the plan). Both drew on the same six shipped buildings: v16's design during development, the\n"
    "trained policy for training and validation. One architecture, one budget and one seed say little about what trained\n"
    "control can reach.\n"
)
a = a.rstrip("\n") + "\n" + outcome
save(APP, a, crlf)
print("--- Appendix outcome ---" + outcome)
print("dry run, nothing written" if dry else "written")
