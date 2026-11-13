"""What the controller learns about each zone (docs/PARAMS.md): run a frozen version on one scenario and save, per
zone, the five numbers of its thermal model (Eq. 1 of the paper; theta2 = [-lambda, g, c, b, c_cm]) averaged over
the last day of the run, next to the zone's floor area and number of exterior cells read from the simulator's floor
plan (the controller never sees these).

    python -m sb.param_dump --scenario D:/SmartBuildings_data/starter-kit/.../building_train_1/fairbanks_1 \
        --steps 2016 --out D:/SmartBuildings_data/results/params/v15/building_train_1__fairbanks_1.json
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
import re
from pathlib import Path

import numpy as np

from sb.run import _absolute_spec, load_policy_class

V15 = Path(__file__).resolve().parents[1] / "submission" / "V15_PARAMS.json"


def find_attr(obj, name: str, depth: int = 4, seen=None):
    """The first object reachable from obj (through attributes) that has attribute `name`."""
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth < 0:
        return None
    seen.add(id(obj))
    if hasattr(obj, name):
        return obj
    for v in list(getattr(obj, "__dict__", {}).values()):
        if isinstance(v, (int, float, str, bytes, np.ndarray, list, dict, tuple)):
            continue
        hit = find_attr(v, name, depth - 1, seen)
        if hit is not None:
            return hit
    return None


def zone_rooms(policy, meta) -> list[str]:
    """Room names in the controller's zone order (the same loop as TransferPolicy.__init__)."""
    num = lambda s: int(re.sub(r"\D", "", s) or 0)
    assign, zai = meta["ahu_zone_assignments"], meta["zone_action_indices"]
    rooms = []
    for ahu in sorted(assign.keys(), key=num)[: policy.n_ahu]:
        for room in assign[ahu]:
            vav = room.replace("room_", "VAV_")
            if policy.idx.get(vav + "_zone_air_temperature_sensor") is not None and vav in zai:
                rooms.append(room)
    return rooms


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy")
    ap.add_argument("--params", default=str(V15))
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=2016)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        return
    from smart_buildings import evaluate

    scen = Path(a.scenario).resolve()
    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec = env.action_spec()
    kw = json.loads(Path(a.params).read_text())
    policy = load_policy_class(_absolute_spec(a.policy))(meta, spec, **kw)
    rooms = zone_rooms(policy, meta)
    assert len(rooms) == policy.nz, (len(rooms), policy.nz)

    b = find_attr(env, "_room_dict")
    cv = (b.cv_size_cm / 100.0) ** 2
    cells = {r: [tuple(x) for x in np.asarray(c).reshape(-1, 2).tolist()] for r, c in b._room_dict.items()}
    area = [len(cells[r]) * cv for r in rooms]
    # Exterior cells: room cells next to an exterior-wall cell of the simulator's grid (value -2).
    wall = np.asarray(b._exterior_walls) == -2
    nr, nc = wall.shape
    ext = []
    for r in rooms:
        n = 0
        for (i, j) in cells[r]:
            if any(0 <= i + di < nr and 0 <= j + dj < nc and wall[i + di, j + dj]
                   for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                n += 1
        ext.append(n)

    obs, _ = env.reset()
    last = []
    for k in range(a.steps):
        action = evaluate.validate_action(policy.get_action(obs), spec)
        obs, reward, terminated, truncated, _ = env.step(action)
        if k >= a.steps - 288:
            last.append(np.array(policy.theta2, dtype=float))
        if terminated or truncated:
            break
    th = np.mean(last, axis=0)
    rec = {"scenario": str(scen), "steps": a.steps, "policy": a.policy, "cv_m2": cv, "rooms": rooms,
           "area_m2": area, "exterior_cells": ext, "theta2_lastday": th.tolist(),
           "prior": list(policy.p["m2_prior"]), "lo": list(policy.p["m2_lo"]), "hi": list(policy.p["m2_hi"])}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1))
    print(f"{scen.parent.name}/{scen.name}: {len(rooms)} zones, area {min(area):.0f}-{max(area):.0f} m2, "
          f"g median {np.median(th[:, 1]):.4g}")


if __name__ == "__main__":
    main()
