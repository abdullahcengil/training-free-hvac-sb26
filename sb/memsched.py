"""Run simulations one process each, starting a job only when the machine's memory allows it.

A full-size building commits 2.6-6.4 GB (mostly the LU factors of its grid), so a pool with a fixed number of workers
either leaves the machine idle or runs it out of memory, and a failed allocation kills a run without a result.
Measured 27 Oct, one process alone after loading (peak commit): 7002 3.13 GB, 7003 4.04, 7007 4.68, 7105 6.38; all
within 0.05 GB of 0.86 GB + 5.1 kB per interior grid cell, the estimate used here (plus MARGIN) while a job loads;
once loaded a run uses less (7001: 3.1 GB; training buildings 0.6-1.2 GB), and its measured use counts. About 40 % is
touched (working set; 7105: 2.30 GB), so physical memory is checked separately: all simulations together stay within
SIM_RAM, and available RAM (plus TRIM_CREDIT that Windows takes back from idle programs) must cover a new one.

Commit is the soft limit: the pagefile is system-managed and Windows grows it when commit runs out (27 Oct: limit
21.5 -> 23.8 GB when 3 GB were committed with 1.3 GB free). Before starting a job that does not fit, the scheduler
makes Windows grow it by committing the missing amount for a moment (never past a pagefile of MAX_PAGEFILE GB), so the
simulation's own allocations never wait on a growth. Physical memory is the hard limit.

A job starts only if fewer than max_jobs run, the previous start was at least GAP seconds ago, and
    free commit (after growth) - growth still expected from running jobs - its estimate >= reserve,
    the working sets of all running jobs plus its own stay within SIM_RAM, and RAM is available for it.
Main jobs go in their order. Filler jobs use memory and slots the next main job cannot use yet, but only as much as
still lets that main job fit once the running main jobs have ended. A job that ends without a result is retried once,
after a pause, with a larger estimate. Jobs still running from an earlier scheduler (their logs name a live PID) are
adopted, so the scheduler can be restarted without stopping simulations.

    python -m sb.memsched --one D:/.../job.json      (one job; the scheduler starts these)
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import ctypes
import ctypes.wintypes as wt
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
WORK = Path("D:/SmartBuildings_data/memsched")
SC = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios")
V10 = REPO / "docs" / "preregistration4" / "V10_PARAMS.json"
GB = 1024 ** 3
GAP = 45.0            # s between starts, so that a new process's loading shows in the free memory
MARGIN = 0.15         # GB of commit on top of the fitted peak
WS_FRAC = 0.45        # working set as a share of the peak commit (7105: 0.36)
PHYS_RESERVE = 0.5    # GB of RAM left available
TRIM_CREDIT = 2.0     # GB of RAM Windows can take back from idle programs (browser, music) when needed
SIM_RAM = 6.0         # GB of RAM for all simulations together (working sets; 25-27 Oct: about 5 GB ran well)
MAX_PAGEFILE = 24.0   # GB; the scheduler never makes the pagefile grow past this
LOAD_S = 300.0        # s; after this a job has loaded, and its memory is what it uses (often below the estimate)


class _MemStatus(ctypes.Structure):
    _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class _Counters(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t), ("PrivateUsage", ctypes.c_size_t)]


_k32 = ctypes.windll.kernel32
_k32.OpenProcess.restype = wt.HANDLE
_k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
_k32.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD]
_k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
_k32.CloseHandle.argtypes = [wt.HANDLE]
_k32.VirtualAlloc.restype = ctypes.c_void_p
_k32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, wt.DWORD]
_k32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wt.DWORD]


def _status() -> _MemStatus:
    s = _MemStatus()
    s.dwLength = ctypes.sizeof(s)
    _k32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s


def free_commit_gb() -> float:
    return _status().ullAvailPageFile / GB


def avail_phys_gb() -> float:
    return _status().ullAvailPhys / GB


def grow_commit(need: float) -> float:
    """Make Windows grow the pagefile until `need` GB of commit are free (within MAX_PAGEFILE); returns free commit."""
    s = _status()
    free = s.ullAvailPageFile / GB
    room = s.ullTotalPhys / GB + MAX_PAGEFILE - s.ullTotalPageFile / GB    # growth still allowed
    want = min(need, free + room)
    if free >= want:
        return free
    blocks, held = [], 0.0
    while held < want:
        p = _k32.VirtualAlloc(None, GB // 2, 0x3000, 0x04)    # MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE; untouched
        if not p:
            break
        blocks.append(p)
        held += 0.5
    for p in blocks:
        _k32.VirtualFree(p, 0, 0x8000)
    return free_commit_gb()


def _proc_info(pid: int) -> tuple[bool, float, float]:
    """(alive, private GB, working set GB) of a process."""
    h = _k32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False, 0.0, 0.0
    try:
        code = wt.DWORD()
        alive = bool(_k32.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259    # STILL_ACTIVE
        c = _Counters()
        c.cb = ctypes.sizeof(c)
        if _k32.K32GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
            return alive, c.PrivateUsage / GB, c.WorkingSetSize / GB
        return alive, 0.0, 0.0
    finally:
        _k32.CloseHandle(h)


def _is_python(pid: int) -> bool:
    """True if the process runs python.exe (a job's PID can be reused by another program after the job ended)."""
    h = _k32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wt.DWORD(1024)
        if not ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return False
        return Path(buf.value).name.lower() in ("python.exe", "pythonw.exe")
    finally:
        _k32.CloseHandle(h)


def private_gb(pid: int) -> float:
    return _proc_info(pid)[1]


_EST: dict[str, float] = {}


def peak_gb(scen: str) -> float:
    """Fitted peak commit of one simulation of this scenario (without the margin)."""
    if scen not in _EST:
        plan = np.load(Path(scen) / "floor_plan.npy")
        _EST[scen] = 0.86 + 5.1e-6 * float((plan == 0).sum())
    return _EST[scen]


def job(j: dict, steps: int) -> dict:
    """A jobs-file entry (sb/jobs.py format) as a runnable job with its key and result path."""
    b, w = j["scenario"].split("__")
    kw = json.loads(V10.read_text()) if j.get("base", "v10") == "v10" else {}
    kw.update(j.get("kwargs", {}))
    scen = str(Path(j.get("root", SC)) / b / w)
    out = Path(j["out"])
    return {"policy": j["policy"], "scen": scen, "out": str(out), "steps": steps, "kwargs": kw,
            "key": f"{out.parent.name}_{out.name}__{b}__{w}", "result": str(out / f"{b}__{w}.json")}


def module_job(module: str, args: list[str], scen: str, result: str, key: str) -> dict:
    """A job that runs `python -m module args` (a trace dump, say); `scen` sizes its memory, `result` marks it done."""
    return {"module": module, "args": args, "scen": scen, "result": result, "key": key}


def one(path: str) -> None:
    print(f"PID {_os.getpid()}", flush=True)
    j = json.loads(Path(path).read_text())
    if "module" in j:
        import runpy

        sys.argv = [j["module"], *j["args"]]
        runpy.run_module(j["module"], run_name="__main__", alter_sys=True)
        return
    from sb.run import run_job

    r = run_job((j["policy"], j["scen"], j["out"], j["steps"], True, j["kwargs"]))
    print(f"{Path(j['out']).name} {r['building']}/{r['weather']}: {abs(r['mean_reward']):.5f} ({r['seconds']:.0f}s)",
          flush=True)


def _pid(log: Path) -> int | None:
    try:
        first = log.read_text(errors="replace").split("\n", 1)[0]
    except OSError:
        return None
    return int(first.split()[1]) if first.startswith("PID ") else None


def _adopt(say) -> dict[str, dict]:
    """Jobs started by an earlier scheduler that are still running."""
    running = {}
    for jf in (WORK / "jobs").glob("*.json"):
        j = json.loads(jf.read_text())
        log = WORK / "logs" / f"{jf.stem}.log"
        pid = _pid(log)
        if pid is None or Path(j["result"]).exists() or not _proc_info(pid)[0] or not _is_python(pid):
            continue
        running[j["key"]] = {"job": j, "proc": None, "fh": None, "log": log, "t0": log.stat().st_mtime, "pid": pid,
                             "main": j.get("main", True), "est": peak_gb(j["scen"]) + MARGIN}
        say(f"adopted {j['key']} (PID {pid})")
    return running


def run(plan, max_jobs: int = 3, reserve: float = 0.5, say=print) -> None:
    """plan() -> (mains, fillers): lists of job() dicts not yet done, in order; it is called again every loop."""
    (WORK / "jobs").mkdir(parents=True, exist_ok=True)
    (WORK / "logs").mkdir(parents=True, exist_ok=True)
    running = _adopt(say)
    tries: dict[str, int] = {}
    hold: dict[str, float] = {}
    extra: dict[str, float] = {}
    last, warned = 0.0, ""
    while True:
        for k, r in list(running.items()):
            if r["proc"] is not None:
                code = r["proc"].poll()
                if code is None:
                    continue
                r["fh"].close()
            else:
                r["pid"] = r["pid"] or _pid(r["log"])
                if r["pid"] and _proc_info(r["pid"])[0]:
                    continue
                code = "?"
            del running[k]
            tail = r["log"].read_text(errors="replace").strip().splitlines()[-1:] or [""]
            if Path(r["job"]["result"]).exists():
                say(f"done  {k} [{time.time() - r['t0']:.0f}s] {tail[0][:120]}")
            else:
                tries[k] = tries.get(k, 0) + 1
                hold[k] = time.time() + 300.0
                extra[k] = extra.get(k, 0.0) + 1.0
                say(f"FAILED {k} (exit {code}, try {tries[k]}): {tail[0][:200]}")
        now = time.time()
        mains, fillers = plan()

        def ok(j: dict) -> bool:
            k = j["key"]
            return k not in running and tries.get(k, 0) < 2 and hold.get(k, 0.0) <= now

        held = [j for j in mains + fillers if j["key"] not in running and tries.get(j["key"], 0) < 2
                and hold.get(j["key"], 0.0) > now]
        mains = [j for j in mains if ok(j)]
        keys = {j["key"] for j in mains}
        fillers = [j for j in fillers if ok(j) and j["key"] not in keys]
        if not running and not mains and not fillers and not held:
            say("queue empty")
            return
        if len(running) < max_jobs and now - last >= GAP and (mains or fillers):
            grow_c, grow_p, main_c, ws_all, ws_main = 0.0, 0.0, 0.0, 0.0, 0.0
            for r in running.values():
                r["pid"] = r.get("pid") or _pid(r["log"])
                _, cur_c, cur_p = _proc_info(r["pid"]) if r["pid"] else (True, 0.0, 0.0)
                loading = now - r["t0"] < LOAD_S
                if loading:
                    grow_c += max(0.0, r["est"] - cur_c)
                    grow_p += max(0.0, WS_FRAC * r["est"] - cur_p)
                ws = max(cur_p, WS_FRAC * r["est"]) if loading else cur_p
                ws_all += ws
                if r["main"]:
                    main_c += max(cur_c, r["est"]) if loading else cur_c
                    ws_main += ws
            free_p = avail_phys_gb() + TRIM_CREDIT - grow_p - PHYS_RESERVE

            def est(j: dict) -> float:
                return peak_gb(j["scen"]) + MARGIN + extra.get(j["key"], 0.0)

            def ram_ok(j: dict) -> bool:
                w = WS_FRAC * est(j)
                return w <= free_p and ws_all + w <= SIM_RAM

            def commit_ok(j: dict, protect: dict | None) -> bool:
                e = est(j)
                free_c = grow_commit(grow_c + e + reserve) - grow_c - reserve
                return e <= free_c and (protect is None or free_c + main_c - e >= est(protect))

            start, is_main = None, False
            head = mains[0] if mains else None
            if head is not None and ram_ok(head) and commit_ok(head, None):
                start, is_main = head, True
            else:
                # Fillers never keep the next main job out: with a filler running it must still fit once the running
                # main jobs end, and the last free slot stays for it if only the fillers' memory keeps it out now.
                ws_h = WS_FRAC * est(head) if head is not None else 0.0
                last_slot = len(running) + 1 >= max_jobs
                for f in fillers:
                    w = WS_FRAC * est(f)
                    if not ram_ok(f):
                        continue
                    if head is not None and (ws_all - ws_main + w + ws_h > SIM_RAM or
                                             (last_slot and ws_main + ws_h <= SIM_RAM)):
                        continue
                    if commit_ok(f, head):
                        start = f
                        break
            if start is None and not running and head is not None:
                msg = (f"waiting: {head['key']} needs {est(head):.2f} GB commit and {WS_FRAC * est(head):.2f} GB RAM; "
                       f"free {free_commit_gb():.2f} / {free_p + PHYS_RESERVE:.2f} GB")
                if msg[:60] != warned[:60]:
                    say(msg)
                    warned = msg
            if start is not None:
                k = start["key"]
                (WORK / "jobs" / f"{k}.json").write_text(json.dumps(dict(start, main=is_main)))
                log = WORK / "logs" / f"{k}.log"
                fh = open(log, "w")
                proc = subprocess.Popen([sys.executable, "-m", "sb.memsched", "--one", str(WORK / "jobs" / f"{k}.json")],
                                        cwd=REPO, stdout=fh, stderr=subprocess.STDOUT,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                running[k] = {"job": start, "proc": proc, "fh": fh, "log": log, "est": est(start), "t0": now,
                              "main": is_main, "pid": None}
                last = now
                say(f"start {k} ({'main' if is_main else 'filler'}, est {est(start):.2f} GB, free commit "
                    f"{free_commit_gb():.2f} GB, RAM {free_p + PHYS_RESERVE:.2f} GB, running {len(running)})")
        time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--one":
        one(sys.argv[2])
    else:
        sys.exit(__doc__)
