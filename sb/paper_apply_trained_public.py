"""Put the trained policy's public leaderboard score into the paper's appendix (docs/TRAINED_BASELINE.md: one submission
with the same weights if the notebook check passes, reported as it comes; references from the paper: v16 0.01031,
the official pid_water baseline 0.06404, both submitted unchanged).

    python sb/paper_apply_trained_public.py <public score> "<read, e.g. 11 Nov, 19:40 UTC>" [--dry]

Run after sb/paper_apply_trained.py (the appendix must already hold the outcome paragraph).
"""
import sys

APP = r"D:\Projeler\SmartBuildings\paper\app_trained.tex"
V16, PID = 0.01031, 0.06404

score, when = float(sys.argv[1]), sys.argv[2]
dry = "--dry" in sys.argv

raw = open(APP, "rb").read().decode("utf-8")
crlf = "\r\n" in raw
a = raw.replace("\r\n", "\n")
key = "One architecture, one budget and one seed say little about what trained\ncontrol can reach.\n"
assert a.count(key) == 1, "outcome paragraph not found: run sb/paper_apply_trained.py first"
assert "public leaderboard, the same weights" not in a, "already applied"
add = (
    "\n% Kaggle public leaderboard, one submission of the same weights (notebook submission/lb/trained_residual.ipynb,\n"
    f"% checked to give the same actions as the two-file policy); score read {when}.\n"
    f"On the public leaderboard, the same weights scored {score:.5f}: {score / PID:.2f} times the official pid\\_water\n"
    f"baseline (0.06404) and {score / V16:.1f} times v16 (0.01031), both submitted unchanged.\n"
)
a = a.replace(key, key + add)
print(add)
if not dry:
    if crlf:
        a = a.replace("\n", "\r\n")
    open(APP, "wb").write(a.encode("utf-8"))
print("dry run, nothing written" if dry else "written")
