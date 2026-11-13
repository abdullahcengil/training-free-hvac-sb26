# Round 8 results: a delay-aware heating net (read 31 Oct 2026, 16:15 by `date`)

Plan: docs/PREREGISTRATION_8.md, stamped 31 Oct 15:33 (docs/preregistration8/, OpenTimestamps; Bitcoin upgrade
pending) before the buildings were generated (15:34; the generator's own check rejected seeds 7903 and 7905, so the
spares 7907 and 7908 took slots 3 and 5, as the plan says). Runs 15:34-16:15, `python -m sb.run_round8 --read`.

| building | window | v16 | sp1 | change | comfort v16 -> sp1 |
|---|---|---|---|---|---|
| 7901 | Duluth, from 29 Jan | 0.04232 | 0.04232 | +0.00 % | 0.00087 -> 0.00087 |
| 7902 | Helena, from 10 Dec | 0.00864 | 0.00864 | -0.01 % | 0.00008 -> 0.00008 |
| 7907 | Chicago, from 8 Jan (MLK Day) | 0.00487 | 0.00480 | -1.48 % | 0.00012 -> 0.00008 |
| 7904 | New York, from 12 Feb (Presidents' Day) | 0.00430 | 0.00430 | +0.00 % | 0.00001 -> 0.00001 |
| 7908 | Seattle, from 10 Dec | 0.00232 | 0.00232 | -0.06 % | 0.00006 -> 0.00006 |
| 7906 | San Francisco, from 5 Feb | 0.00149 | 0.00149 | -0.13 % | 0.00004 -> 0.00004 |

- H1 (mean at least 0.3 % below v16): 0.010644 against 0.010656, -0.12 %. **FAIL.**
- H2 (at or below v16 in at least 5 of 6): 5 of 6. PASS.
- H3 (no building more than 1 % worse): worst +0.00 %. PASS.
- H4 (comfort regret at most v16's): x0.97. PASS.

Decision (fixed in the plan): H1 failed, so sp1 does not become v17; **v16 stays** the final version.

Reading: the plan expected this outcome when the six buildings hold no more than one building with small, fast rooms
("with none about -0.1 %, and H1 fails"). Only Chicago gained (-1.5 %, comfort term down by a third); the Duluth window,
the coldest yet (-14.8 C mean), carries 66 % of the summed loss and is unchanged, so the mean barely moves. The
heating net is harmless (no building worse by more than 0.005 %) but its gain is too rare to pay on average.

pid_water on the same six buildings (descriptive, queued after both arms; finished 16:32 by the log): v16 is below it in
all six, ratios 0.237 (Duluth), 0.115 (Helena), 0.101, 0.039, 0.094 and 0.027 (in the order of the table's rows by
building number: 7901, 7902, 7904, 7906, 7907, 7908). The transfer figure (sb/fig_transfer.py) now counts 34 of 34
full-size scenarios on 26 buildings, and the paper 122 of 122 unseen scenarios since v8.
