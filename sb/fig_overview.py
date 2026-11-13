"""Figure 1: the controller at every step (top) and the eight pre-registered blind rounds (bottom).

Numbers: hypotheses passed per round from docs/RESULTS_HELDOUT.md and docs/RESULTS_ROUND2.md to RESULTS_ROUND7.md
(round 6: H3 counted as failed, docs/DEVIATIONS.md deviation 6).

    python -m sb.fig_overview docs/fig/fig_overview.png
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, FILL, PLANT = "#2a78d6", "#eef4fc", "#f4f3f0"
TITLE, BODY = 8.0, 7.3
# (round, version frozen for it, hypotheses passed, hypotheses in all)
# Round 8 tested a candidate that was not adopted (v16 + delay-aware heating net; docs/RESULTS_ROUND8.md).
ROUNDS = [(1, "v7", 0, 3), (2, "v8", 4, 4), (3, "v9", 3, 4), (4, "v10", 4, 5), (5, "v11", 5, 5), (6, "v15", 3, 4),
          (7, "v16", 4, 4), (8, "v16 + net", 3, 4)]


def box(ax, x, y, w, h, title, body, fill=FILL, edge=BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fill, ec=edge, lw=0.8))
    ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=TITLE, weight="bold", color=TEXT)
    ax.text(x + w / 2, y + h - 5.4, body, ha="center", va="top", fontsize=BODY, color=TEXT2, linespacing=1.3)


def arrow(ax, a, b, color=TEXT2):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=7, lw=0.8, color=color, shrinkA=0,
                                 shrinkB=0))


def main(out: str) -> None:
    fig = plt.figure(figsize=(6.5, 4.0), facecolor=SURFACE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")

    ax.text(1, 61, "a   The controller, every 5-minute step (same code and settings everywhere, no training phase)",
            fontsize=TITLE + 0.2, weight="bold", color=TEXT, va="top")
    # Row 1: the loop through the zones.
    box(ax, 1, 40, 16.5, 16, "Measure", "zone temperatures\n(one step late),\noutside air,\ncomfort-mode flag",
        fill=PLANT, edge=TEXT2)
    box(ax, 20.5, 40, 19.5, 16, "Zone model", "5 numbers per zone\n+ slab node (4 h lag),\nidentified online by\n"
        "recursive least squares")
    box(ax, 43, 40, 22, 16, "Plan past the delay", "predict $T_{k+1}$ from the\nheat in the pipe, choose\n"
        "the heat for $T_{k+2}$, add\na disturbance estimate")
    box(ax, 68.5, 40, 19, 16, "Heat to boxes", "cooling: airflow;\nheating: 35 °C\ndischarge, airflow\ncapped at a quarter")
    ax.add_patch(FancyBboxPatch((91, 23), 8, 33, boxstyle="round,pad=0,rounding_size=1.2", fc=PLANT, ec=TEXT2,
                                lw=0.8))
    ax.text(95, 39.5, "Building (simulator)", ha="center", va="center", fontsize=TITLE, weight="bold", color=TEXT,
            rotation=90)
    # Row 2: what sets the targets and the plant.
    box(ax, 43, 23, 22, 14, "Setbacks", "outside comfort hours\neach zone floats, then\nrecovers just in time")
    box(ax, 68.5, 23, 19, 14, "Plant by cost", "supply air by reward\ncost; duct and pump\npressure reset;\n"
        "hot water at 350 K")

    for a, b in (((17.5, 48), (20.5, 48)), ((40, 48), (43, 48)), ((65, 48), (68.5, 48)), ((87.5, 48), (91, 48)),
                 ((87.5, 30), (91, 30)), ((54, 37), (54, 40)), ((78, 40), (78, 37))):
        arrow(ax, a, b)
    # The model learns from its own prediction error.
    arrow(ax, (43, 43), (40, 43), color=BLUE)
    ax.text(30.25, 38.6, "the prediction error\nupdates the model", fontsize=BODY, color=BLUE, ha="center", va="top",
            linespacing=1.3)
    # Feedback: the building's next reading goes back to the measurement.
    ax.plot([95, 95, 9.25], [23, 20.8, 20.8], color=TEXT2, lw=0.8, solid_joinstyle="miter")
    arrow(ax, (9.25, 20.8), (9.25, 40))
    ax.text(30, 21.4, "next reading, 5 minutes later", fontsize=BODY, color=TEXT2, ha="center", va="bottom")

    # Panel b: the protocol and the rounds.
    ax.plot([1, 99], [18.6, 18.6], color=GRID, lw=0.8)
    ax.text(1, 17.4, "b   Testing transfer: eight pre-registered blind rounds, each on six newly generated buildings",
            fontsize=TITLE + 0.2, weight="bold", color=TEXT, va="top")
    box(ax, 1, 1, 19, 13, "Before each round", "freeze code hash,\nscenarios, hypotheses,\npass marks;\n"
        "timestamp on Bitcoin", fill=PLANT, edge=TEXT2)
    arrow(ax, (20, 7.5), (22.5, 7.5))
    w = (99 - 22.5 - 0.5 * (len(ROUNDS) - 1)) / len(ROUNDS)
    for i, (r, v, ok, n) in enumerate(ROUNDS):
        x = 22.5 + i * (w + 0.5)
        ax.add_patch(FancyBboxPatch((x, 1), w, 13, boxstyle="round,pad=0,rounding_size=1.2", fc=SURFACE,
                                    ec=TEXT2, lw=0.6))
        ax.text(x + w / 2, 12.4, f"Round {r}\n{v}", ha="center", va="top", fontsize=TITLE - 1.7, weight="bold",
                color=TEXT, linespacing=1.15)
        for j in range(n):
            cx = x + w / 2 + (j - (n - 1) / 2) * 1.75
            ax.add_patch(Circle((cx, 6.9), 0.7, fc=BLUE if j < ok else SURFACE, ec=BLUE, lw=0.8))
        ax.text(x + w / 2, 4.9, f"{ok} of {n}\npassed", ha="center", va="top", fontsize=BODY, color=TEXT2,
                linespacing=1.15)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_overview.png")
