"""Evalúa clips retargeteados uno por uno (para saber exactamente cuál falla).
Uso: phase0_basics/.venv/bin/python retarget/eval_clips.py 143_02 78_06 ...  (N en paralelo con WORKERS=)"""
import os, re, shutil, sys, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_battery_3a as rb

def one(trial: str) -> tuple[str, dict]:
    src = next(rb.MOTIONS.glob(f"*/cmu_{trial}.motion"))
    d = rb.MOTIONS / "_single" / trial
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, d / src.name)
    rel = Path("_single") / trial
    vals = rb.evaluate(str(rel))
    return trial, {"skill": src.parent.name, "ok": vals["success_rate"] == 1.0, "gt_mean_cm": round((vals["gt_error/mean"] or 0) * 100, 1)}

if __name__ == "__main__":
    out = {}
    with ThreadPoolExecutor(max_workers=int(os.environ.get("WORKERS", 6))) as pool:
        for f in as_completed([pool.submit(one, t) for t in sys.argv[1:]]):
            t, v = f.result(); out[t] = v; print(t, v, flush=True)
    (rb.MOTIONS / "single_clip_eval.json").write_text(json.dumps(out, indent=2))
