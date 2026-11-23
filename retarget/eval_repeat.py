"""Evalúa cada clip retargeteado N veces en MuJoCo para medir su fiabilidad real.

La inferencia de ProtoMotions no fija semilla: cada corrida es distinta, así que repetir da estadística.
Escribe data/cmu_motions/<salida>.json y, por habilidad, la tasa de éxito sobre todas las corridas.

Uso (desde la raíz del repo):
  REPEATS=5 WORKERS=10 phase0_basics/.venv/bin/python retarget/eval_repeat.py [salida] [trial ...]
"""
import json
import os
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import run_battery_3a as rb  # noqa: E402


def one(src: Path, k: int, tag: str) -> tuple[str, int, dict]:
    trial = src.stem.removeprefix("cmu_")
    rel = Path("_repeat") / tag / f"{src.parent.name}__{trial}_r{k}"
    d = rb.MOTIONS / rel
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, d / src.name)
    v = rb.evaluate(str(rel))
    shutil.rmtree(d, ignore_errors=True)
    return f"{src.parent.name}/{trial}", k, {"skill": src.parent.name, "ok": v["success_rate"] == 1.0,
                      "gt_mean_cm": None if v["gt_error/mean"] is None else round(v["gt_error/mean"] * 100, 1),
                      "jerk_pct": v["high_jerk_frame_percentage_mean"]}


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else "repeat_eval"
    only = set(sys.argv[2:])
    n = int(os.environ.get("REPEATS", 5))
    clips = sorted(p for p in rb.MOTIONS.glob("*/cmu_*.motion") if not p.parent.name.startswith("_")
                   and (not only or p.stem.removeprefix("cmu_") in only))
    res: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=int(os.environ.get("WORKERS", 10))) as pool:
        futs = [pool.submit(one, c, k, tag) for c in clips for k in range(n)]
        for i, f in enumerate(as_completed(futs), 1):
            t, k, v = f.result()
            r = res.setdefault(t, {"skill": v["skill"], "runs": []})
            r["runs"].append(v)
            print(f"[{i}/{len(futs)}] {t:30} r{k} ok={v['ok']} err={v['gt_mean_cm']} cm", flush=True)
    for r in res.values():
        r["success"] = sum(x["ok"] for x in r["runs"]) / len(r["runs"])
        j = [x["jerk_pct"] for x in r["runs"] if x["jerk_pct"] is not None]
        r["jerk_pct"] = round(sum(j) / len(j), 2) if j else None
    by = defaultdict(list)
    for t, r in res.items():
        by[r["skill"]] += [x["ok"] for x in r["runs"]]
    jerks = [r["jerk_pct"] for r in res.values() if r["jerk_pct"] is not None]
    out = {"repeats": n, "motions_dir": str(rb.MOTIONS), "jerk_pct_mean": round(sum(jerks) / len(jerks), 2) if jerks else None, "clips": dict(sorted(res.items())),
           "skills": {s: round(sum(v) / len(v), 3) for s, v in sorted(by.items())}}
    (rb.MOTIONS / f"{tag}.json").write_text(json.dumps(out, indent=2))
    print("\nÉxito por habilidad (todas las corridas):")
    for s, p in out["skills"].items():
        print(f"  {s:22} {p*100:5.1f}%")
    print(f"Jerk alto medio: {out['jerk_pct_mean']}%  |  clips 100%: {sum(r['success'] == 1 for r in res.values())}/{len(res)}")


if __name__ == "__main__":
    main()
