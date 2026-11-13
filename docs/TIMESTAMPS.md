# Bitcoin timestamps of the pre-registered plans (checked 30 Oct 2026, about 15:50 by `date`)

Every plan was frozen to a file whose SHA-256 hash, and nothing else, went to the OpenTimestamps calendars before the
round's first run. On 30 Oct the proofs (`docs/preregistration*/*.ots`) were upgraded with the calendars' Bitcoin
attestations and verified: each file's hash matches its proof, and each proof's Merkle path ends in the Merkle root of
the named block (headers from blockstream.info). Tool: `SocketZ/opengrid/ots.py` (`info`, `upgrade`, `verify`); the
standard OpenTimestamps client or opentimestamps.org give the same check.

| plan | file | SHA-256 (first 16 hex digits) | first block | block time (UTC) | results first recorded (UTC) |
|---|---|---|---|---|---|
| round 1 | `preregistration/PREREGISTRATION_2026-10-16.md` | fe74aa8a8a4407cb | 971,718 | 16 Oct 14:07 | 17 Oct 11:45 (RESULTS_HELDOUT.md, 13:45 UTC+2) |
| round 2 | `preregistration2/PREREGISTRATION_2_2026-10-17.md` | 699bce06d60774b0 | 971,780 | 16 Oct 23:17 | 17 Oct 13:08 (first commit of RESULTS_ROUND2.md) |
| round 3 | `preregistration3/PREREGISTRATION_3_2026-10-18.md` | 1426c66885a163ad | 971,934 | 18 Oct 02:32 | 18 Oct 05:13 (first commit of RESULTS_ROUND3.md) |
| round 4 | `preregistration4/PREREGISTRATION_4_2026-10-22.md` | e26e2d7991824600 | 972,546 | 21 Oct 23:07 | 22 Oct 10:25 (first commit of RESULTS_ROUND4.md) |
| round 5 | `preregistration5/PREREGISTRATION_5_2026-10-22.md` | e4fce3fcec9d8a62 | 972,648 | 22 Oct 19:26 | 22 Oct 21:46 (RESULTS_ROUND5.md, 23:46 UTC+2) |
| full-size screens | `preregistration6/BIGDEV_2026-10-25.md` | e0da4ae880a0b91e | 973,126 | 25 Oct 21:00 | 27 Oct (BIGDEV.md, screen results) |
| round 6 | `preregistration6h/PREREGISTRATION_6_2026-10-30.md` | e4d9af8c9e155e16 | 973,762 | 30 Oct 01:45 | 30 Oct 02:14 (RESULTS_ROUND6.md, 03:14 UTC+1) |
| round 7 | `preregistration7/PREREGISTRATION_7_2026-10-31.md` | 9b423afc0b60c256 | 973,914 (also 973,915) | 31 Oct 02:24 | 31 Oct 03:22 (first commit of RESULTS_ROUND7.md, 04:22 UTC+1); first run ended 02:33 |
| transfer ablation (post hoc, not a blind round) | `TRANSFER_ABLATION.md` | 5da4428804edc067 | 973,939 | 31 Oct 06:31 | first run started 06:34, first result 06:35 (transfer_abl.log, 07:35 UTC+1) |

The manifests of rounds 1-5 (`MANIFEST*.txt`) are in the same blocks as their plans (round 1 also in 971,719, round 4
also in 972,552: two calendars). Round 6's plan fixed the generator seeds (7701-7706, spares 7707-7715) and the
generator script by its hash; the buildings were generated after the stamp, so their manifest
(`preregistration6h/MANIFEST6_2026-10-30.txt`, committed 02:20 UTC+1) has no proof of its own and can be checked by
generating the buildings again from those seeds.

Reading: a block's time is set by its miner and can be off by up to about an hour. In every round the block's time is
before the first record of the results; in round 6 only by 29 minutes, within that uncertainty (its runs started at
01:25 UTC, after the hash went to the calendars at 01:18 UTC). One plan's heading time was ahead of the clock: round 4
says "about 02:00 (UTC+2)", but its block is at 01:07 (UTC+2), so the file existed by then (note added to
PREREGISTRATION_4.md). In the paper: Appendix "Timestamps of the plans".

Round 7 (proof upgraded and verified 31 Oct 06:55 by `date`, UTC+1; blocks 973,914 at 02:24 UTC and 973,915 at 02:37 UTC, two calendars): the hash went to the calendars at 02:21:35 UTC, the buildings were generated at 02:22-02:23 UTC (manifest `preregistration7/MANIFEST7_2026-10-31.txt`, committed 03:24 UTC+1; seeds 7801 and 7805 rejected by the generator's own check), the first run ended at 02:33 UTC.

Transfer ablation (proof upgraded and verified 31 Oct 08:07 by `date`, UTC+1): the plan (docs/TRANSFER_ABLATION.md,
written 07:04 UTC+1) went to the calendars at 06:04 UTC; block 973,939 (06:31 UTC) commits to it; the scheduler
started the first run at 06:33:59 UTC. Its buildings are those of rounds 6 and 7, no longer blind, so the stamp fixes
the arms and the reading rules, not the buildings.

## Round 8 (added 31 Oct 2026, 16:20 by `date`)

Plan `docs/preregistration8/PREREGISTRATION_8_2026-10-31.md` (sha256 e782910449f3d4cebbc4156158cc0bdb6e0c5b3ae30a523ca3ba7c513ebea4f1)
went to two calendars at 14:33 UTC (15:33 local; commit 9c1f35c), the buildings were generated at 14:33-14:34 UTC
and the first result was recorded at 14:42 UTC. The Bitcoin upgrade is pending
(`cd <opentimestamps-tool> && python -m opengrid.ots upgrade <plan>.ots`, then `verify`). The calendars
commit to Bitcoin every few hours, so round 8's block will likely come after its first result: for this round the
evidence that the plan came first is the calendars' receipt and the commit, not the block. The paper says so
(Appendix J). The round's main hypothesis failed (docs/RESULTS_ROUND8.md).

Upgraded and verified 31 Oct 16:34 by `date` (`python -m opengrid.ots upgrade`, then `verify`, ok): block 973,986
(hash 0000000000000000000006e22ba67124284216e3bc84cbf7d13ac19d8bd09957), block time 15:00:44 UTC. That is 18 minutes
after the first result was recorded (14:42 UTC, Duluth, v16) and before the twelve main results were read (16:15 local,
15:15 UTC). As expected above, the block alone does not show that round 8's plan came before its first result; the
calendars' receipt (14:33 UTC) and commit 9c1f35c do. Paper Appendix J says so.

## Byte-for-byte storage and two additions (written 8 Nov 2026, 00:28 by `date`)

- The plan files are stored byte for byte (`docs/prereg*/** -text` in .gitattributes; before this, git had stored
  the CRLF plans of rounds 1-5 as LF, so a fresh clone would not have matched 9 of the proofs). Hash them as checked
  out, without line-ending conversion. All 16 proofs re-checked against the stored bytes: 16 of 16 match.
- Transfer ablation: the plan was stamped in place and docs/TRANSFER_ABLATION.md later received the results; the
  stamped version is frozen as `docs/prereg_ablation/TRANSFER_ABLATION_2026-10-31.md` (copy of commit 460361b,
  SHA-256 5da4428804edc067...), with its proof beside it.
- Sensor faults: `docs/prereg_faults/SENSOR_FAULTS_2026-11-04.md` (8d275c9827336c50...), block 974,543 at
  4 Nov 15:50 UTC (blockstream.info, read 8 Nov 2026, 00:28); first result 4 Nov 16:33 UTC (results/faults/check); write-up
  6 Nov 00:00 UTC. Added to the paper's table.
- The paper's table now gives the first result (file times) and the write-up; in rounds 2, 4, 5, 6 and 8 the block
  came 3-18 minutes after the first few results, so the paper rests "plan before first run" on the calendars'
  receipts and the commit history, not on the block alone.
