r"""APPLIED on 29 Oct 2026 (user: "Makaleyi tabii ki de 7 sayfaya indir"): its output is now paper/main.tex; the long
version is in commit 968f2cf. Do not run it on the new main.tex (the blocks it moves are already in the appendix).

Preview of a shorter main text (docs/PAPER_PLAN.md, proposal of 27 Oct): writes paper/main_6p.tex from
paper/main.tex by moving blocks to the appendix and putting short versions in their place. Nothing is deleted.
Blocks are found by their text, so the script can be re-run after main.tex changes.

    python paper/make_6p.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC, DST = HERE / "main.tex", HERE / "main_6p.tex"


def find(lines, pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise SystemExit(f"marker not found after line {start}")


def trim(seg):
    while seg and not seg[-1].strip():
        seg = seg[:-1]
    return seg


def main() -> None:
    L = SRC.read_text(encoding="utf-8").split("\n")
    cuts = {}   # name -> (first, last) line indices, inclusive

    i = find(L, lambda s: "fig_probe.png" in s and "includegraphics" in s)
    cuts["probe"] = (find(L, lambda s: s.startswith(r"\begin{figure}"), i - 2), find(L, lambda s: s.startswith(r"\end{figure}"), i))
    a = find(L, lambda s: s.startswith("% docs/TANKFIX.md"))
    cuts["tank"] = (a, find(L, lambda s: s.startswith(r"\subsection{Schedule and setbacks}"), a) - 1)
    g = find(L, lambda s: "fig_glide.png" in s and "includegraphics" in s)
    r5 = find(L, lambda s: "fig_round5.png" in s and "includegraphics" in s)
    cuts["glide_r5"] = (g - 1, find(L, lambda s: s.startswith(r"\end{figure}"), r5))
    t = find(L, lambda s: r"\label{tab:stats}" in s)
    cuts["stats"] = (find(L, lambda s: s.startswith(r"\begin{table}"), t - 3), find(L, lambda s: s.startswith(r"\end{table}"), t))
    a = find(L, lambda s: s.startswith("We submitted each frozen version"))
    cuts["lb"] = (a, find(L, lambda s: s.startswith(r"\section{Where the remaining loss is}"), a) - 1)
    a = find(L, lambda s: s.startswith(r"\section{Where the remaining loss is}"))
    cuts["loss"] = (a, find(L, lambda s: s.startswith(r"\section{New climates: a stress test}"), a) - 1)
    a = find(L, lambda s: s.startswith(r"\section{New climates: a stress test}"))
    cuts["stress"] = (a, find(L, lambda s: s.startswith(r"\section{Full-size buildings}"), a) - 1)
    a = find(L, lambda s: s.startswith(r"(Sections~\ref{sec:protocol}"))
    cuts["contrib"] = (a, find(L, lambda s: s.rstrip().endswith(r"(Section~\ref{sec:big})."), a))

    seg = {k: trim(L[a:b + 1]) for k, (a, b) in cuts.items()}
    short = {
        "contrib": [
            r"(Sections~\ref{sec:protocol} and~\ref{sec:results}, Figure~\ref{fig:overview}b). (4) Two outside checks of the gap",
            r"between our training and public scores: ten new climates (Section~\ref{sec:stress}), and buildings at the size the",
            r"generator draws, which reproduce the gap and show a recovery that the slab slows in large rooms (Section~\ref{sec:big}).",
            r"Where the remaining loss is, and an idea that did not pay (occupancy inference), are in Appendix~\ref{app:loss}.",
        ],
        "tank": [
            r"The controller holds the hot-water setpoint, so its scores do not depend on an accounting issue reported in the",
            r"simulator's tank model (Appendix~\ref{app:tank}).", "",
        ],
        "lb": [
            r"We submitted each frozen version once to the public leaderboard (about a third of the hidden test set) and never",
            r"chose a parameter by it: v8 0.01687, v11 0.01071, v14 0.01048 (rank 71 of 387 on 27 October). The public score has",
            r"been 1.35--1.44 times the training score, against 1.11 on our round-5 buildings, while the official pid\_water",
            r"baseline, submitted unchanged, scored 1.18 times its training score. Appendix~\ref{app:lb} gives the calibration and",
            r"two tests of this gap; a third, buildings at full size, is Section~\ref{sec:big}. A probe that changed only v14's",
            r"hot-water setpoint so that it uses the tank accounting issue (not our method) scored about 0.007, a third lower",
            r"(Appendix~\ref{app:lb}): at least a third of v14's public loss is heating that the issue can remove.", "",
        ],
        "stress": [
            r"\section{New climates: a stress test}\label{sec:stress}",
            r"% docs/STRESS_TEST.md; details in Appendix~\ref{app:stress}.",
            r"The hidden set uses five weather stations absent from training. We ran v13 and pid\_water on the six training",
            r"buildings in ten other cities, two 30-day windows each, 40 scenarios (Appendix~\ref{app:stress}). By a rule fixed",
            r"before the runs, the controller keeps its advantage if the ratio of mean losses v13/pid\_water stays within 1.2 times",
            r"its training value: it was 0.143 against 0.136, and v13 was better in all 40 scenarios. One building in Duluth",
            r"exposed a steady droop in zones with large heat losses; its fix, v14, passed its own rule (training $-0.37$\,\%,",
            r"stress $-1.30$\,\%).", "",
        ],
    }
    appendix = (
        [r"\section{Probe of the simulator}\label{app:probe}"] + seg["probe"] + [""]
        + [r"\section{Paired statistics}\label{app:stats}"] + seg["stats"] + [""]
        + [r"\section{Leaderboard calibration}\label{app:lb}", "% docs/RESULTS_EXTERNAL.md."] + seg["lb"] + [""]
        + [seg["loss"][0] + r"\label{app:loss}"] + seg["loss"][1:] + [""]
        + [r"\section{New climates: details of the stress test}\label{app:stress}"] + seg["stress"][1:] + [""]
        + [r"\section{Hot-water tank accounting}\label{app:tank}"] + seg["tank"] + [""]
    )
    starts = {a: k for k, (a, b) in cuts.items()}
    ends = {k: b for k, (a, b) in cuts.items()}
    out, i = [], 0
    while i < len(L):
        if i in starts:
            k = starts[i]
            out += short.get(k, [])
            i = ends[k] + 1
            continue
        s = L[i]
        if s.startswith(r"\section{Ablations of the first controller}"):
            out += appendix
        if s.startswith(r"\section{Rounds 2--4, per scenario}"):
            out += [r"\section{Per-round figures}"] + seg["glide_r5"]
            i += 1
            continue
        out.append(s)
        i += 1
    DST.write_text("\n".join(out), encoding="utf-8")
    print("wrote", DST.name, len(out), "lines from", len(L))


if __name__ == "__main__":
    main()
