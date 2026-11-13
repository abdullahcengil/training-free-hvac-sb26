# Deviations from the pre-registration

1. **16 Oct 2026, 17:44 UTC. Held-out run crashed before any step was simulated.** The starter kit's scenario generator, run on Windows with an absolute output folder, writes paths such as `D:\...\scenarios\building_7001/...` into `config.gin`; gin reads `\b` as a backspace, so the floor-plan file could not be opened. No result of any policy was produced. **Fix:** backslashes replaced by forward slashes on the four path lines of each config (`sb/fix_heldout_paths.py`); nothing else changed. The old hashes match `heldout/MANIFEST.txt`; old and new hashes are in `heldout/MANIFEST_PATHFIX.txt`. The run was restarted with the same frozen policy commit.

2. **16 Oct 2026, about 19:00-19:50 UTC. Some held-out jobs crashed out of memory.** While the held-out run was going, extra diagnostic simulations were started on the same 16 GB machine. Some held-out worker processes then failed inside the simulator's sparse solver (`RuntimeError: SUPERLU_MALLOC failed`) and `sb.run` stopped that policy's run: the frozen controller had 10 of 12 scenarios and pid_water 4 of 12. A crashed job writes no result, so no number was lost or chosen. **Fix:** the missing jobs are re-run with `sb/heldout_fill.sh`, which skips every scenario that already has a result; the controller is run from the file exported from the commit in `RUN_INFO.json` (`ad59466`, SHA-256 `ed09634e...`), not from the working copy. The working copy of `policies/zonal.py` had gained two options (v8, default off) during the run; with their defaults they add exactly zero to every prediction, so results are bit-for-bit those of the frozen file. From now on at most six simulation processes run at a time (each needs about 1 GB). The bit-for-bit claim is checked in `docs/TUNING_LOG.md` (working copy with defaults vs the frozen dev result).

3. **17 Oct 2026, early morning. The machine shut down during both runs.** At that point round 2 had all 12 results for v8 and v7 and 8 of 12 for pid_water; round 1 had 5 of 12 for bang_bang; the post-hoc v8 run on round 1 had 7 of 12. Jobs in progress write no result, so nothing partial was kept. **Fix:** the same scripts were restarted at about 10:15 (UTC+2): round-2 baselines with `sb/heldout2_resume.sh` (does not rewrite `RUN_INFO.json`), round 1 with `sb/heldout_fill.sh bang_bang`, the post-hoc run with `sb/posthoc_r1.sh`. All skip finished scenarios. The policies and parameters are unchanged.

## Deviation 4 (round 4, 22 Oct 2026): the computer slept during the run

During the last pid_water runs of round 4 the computer went to sleep at 05:10 and woke at 11:54 (Windows System log: Kernel-Power event 42, then Power-Troubleshooter). The processes were suspended, not stopped, and resumed; the simulation is deterministic and has no wall-clock input, so the results are unaffected. All 36 runs finished; the v10 and v9 runs had finished before the sleep. From now on the session keeps the machine awake during runs.

## Deviation 5 (round 5, 22 Oct 2026): run stopped for a Windows security update

The user had to install a Windows security update that required stopping running processes. At 22:22 (UTC+2) the
round-5 run (`sb/heldout5.sh`, started 21:12:32) was stopped by ending its processes: all 12 v11 runs had finished
and been written; the v10 runs had started about two minutes earlier and had written nothing; pid_water had not
started. A stopped job writes no result, so nothing partial was kept. **Fix:** after the update, the run continues
with `sb/heldout5_resume.sh`: the same frozen files (`zonal_405fc62….py` for v11, `zonal_24f07c3….py` for v10) and
parameter files; `sb.run` skips every scenario that already has a result; RUN_INFO.json is left as written at the
start and the restart time goes to RUN_RESUME.json. The simulation is deterministic and has no wall-clock input, so
the results are those of an uninterrupted run. No result was looked at to decide anything; the v11 log line with its
12-scenario score was printed by the runner before the stop.
Resumed at 22:27:42 (UTC+2; `RUN_RESUME.json`) after the Claude desktop app had been quit and reopened; Windows had
not restarted (last boot 17 Oct). The 12 v11 results were reused unchanged (`sb.run` skipped them); v10 and
pid_water run from the start of each scenario.

## Deviation 6 (round 6, 30 Oct 2026): a pass mark differs between the plan and its runner

The plan (docs/PREREGISTRATION_6.md, stamped 02:18) sets H3 at "at most 1.5 times v14's comfort regret"; the runner it
names by hash (`sb/run_round6h.py`) checks `cb <= 1.10 * ca`, a constant left from the plan's draft. Found when the
runner printed FAIL for a ratio of 1.22 (read 03:14). Neither file was changed after the runs. We report both readings
and count H3 as failed (the stricter one); the plan's decision does not depend on H3.
