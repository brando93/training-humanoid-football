"""Genera docs/checklist_habilidades.md a partir de configs/skills_checklist.yaml y una medición de
retarget/eval_repeat.py. Los checks se calculan, nunca se ponen a mano.

Check = "Lo hace" (100% de éxito en todas las corridas, >= MIN_RUNS por clip, error medio < 10 cm)
        Y "Natural" (evaluador de naturalidad; mientras no exista, ninguna habilidad tiene check).
El historial (fecha del primer check, y si se perdió) vive en docs/checklist_history.json.

Uso: phase0_basics/.venv/bin/python retarget/update_checklist.py data/cmu_motions/repeat_baseline_v0.json "Tracker NVIDIA (sin ajuste)"
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CFG = REPO / "configs" / "skills_checklist.yaml"
OUT = REPO / "docs" / "checklist_habilidades.md"
HIST = REPO / "docs" / "checklist_history.json"
MIN_RUNS = 5
MAX_ERR_CM = 10.0
STAGES = {
    "etapa_1_movimiento_humano": "Etapa 1 — Moverse como un humano, de forma natural",
    "etapa_2_atletico_futbol": "Etapa 2 — Movimiento atlético para el fútbol (sin balón)",
    "etapa_3_balon": "Etapa 3 — El balón",
}
GROUPS = {
    "postura_y_equilibrio": "Postura y equilibrio", "caminar": "Caminar", "correr": "Correr", "saltar": "Saltar",
    "suelo": "Suelo", "velocidad": "Velocidad", "agilidad": "Agilidad", "saltos": "Saltos", "gesto": "Gesto técnico",
    "fisica": "Física del balón", "basicas_B0_B5": "Básicas con balón (B0–B5)", "juego_B6_B9": "Juego (B6–B9)",
}
NATURAL_MIN = 4  # nota de Brandon (1-5) desde la cual cuenta como natural
REVIEWS = REPO / "docs" / "naturalness_reviews.json"  # la escribe retarget/apply_review.py


def load_natural() -> dict[str, dict]:
    """Por ahora "natural" = la última nota visual de Brandon en un PR de corrida. Las métricas físicas
    (pies que patinan, fuerzas, suavidad) se sumarán cuando exista el evaluador."""
    return json.loads(REVIEWS.read_text()) if REVIEWS.exists() else {}


def skill_stats(result: dict) -> dict[str, dict]:
    if "skills" in result and "clips" not in result:  # metrics.json de reports/runs/<id>/ (para Actions)
        return {k: {"rate": v["rate"], "err_cm": v["err_cm"], "n1": v["lo_hace"], "fail": v["fail"],
                    "min_runs": MIN_RUNS, "clips": None} for k, v in result["skills"].items()}
    agg: dict[str, dict] = defaultdict(lambda: {"runs": 0, "ok": 0, "err": [], "clips": 0, "min_runs": 10**9, "fail": []})
    for key, c in result["clips"].items():
        s = agg[c["skill"]]
        runs = c["runs"]
        s["clips"] += 1
        s["runs"] += len(runs)
        s["min_runs"] = min(s["min_runs"], len(runs))
        ok = sum(r["ok"] for r in runs)
        s["ok"] += ok
        s["err"] += [r["gt_mean_cm"] for r in runs if r["ok"] and r["gt_mean_cm"] is not None]
        if ok < len(runs):
            s["fail"].append(f"{key.split('/')[-1]} ({ok}/{len(runs)})")
    for s in agg.values():
        s["rate"] = s["ok"] / s["runs"] if s["runs"] else 0.0
        s["err_cm"] = sum(s["err"]) / len(s["err"]) if s["err"] else None
        s["n1"] = s["rate"] == 1.0 and s["min_runs"] >= MIN_RUNS and s["err_cm"] is not None and s["err_cm"] < MAX_ERR_CM
    return agg


def main() -> None:
    src = Path(sys.argv[1]).resolve()
    label = sys.argv[2] if len(sys.argv) > 2 else src.stem
    stats = skill_stats(json.loads(src.read_text()))
    cfg = yaml.safe_load(CFG.read_text())
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    natural = load_natural()
    today = date.today().isoformat()

    rows, total, done, does = [], 0, 0, 0
    for stage, groups in cfg.items():
        rows.append(f"\n## {STAGES.get(stage, stage)}\n")
        rows.append("| | Habilidad | Lo hace | Natural | Cuando se pide | Robusto | Detalle |")
        rows.append("|---|---|---|---|---|---|---|")
        for group, items in groups.items():
            rows.append(f"| | **{GROUPS.get(group, group)}** | | | | | |")
            for it in items:
                total += 1
                h = hist.setdefault(it["id"], {})
                s = stats.get(it["eval"]) if it["eval"] else None
                r = natural.get(it["id"])
                nat = None if r is None else r["nota"] >= NATURAL_MIN
                nat_txt = "⬜" if s is None else ("⏳ sin nota" if r is None else f"{'✅' if nat else '❌'} {r['nota']}/5")
                if s is None:
                    lo_hace, check = "⬜ sin prueba", "⬜"
                    detail = "Faltan clips" if stage != "etapa_3_balon" else "Pendiente de su etapa"
                else:
                    pct = f"{s['rate'] * 100:.0f}%"
                    err = f"{s['err_cm']:.1f} cm" if s["err_cm"] is not None else "—"
                    mark = "✅" if s["n1"] else ("🟡" if s["rate"] > 0 else "❌")
                    lo_hace = f"{mark} {pct} · {err}"
                    does += s["n1"]
                    full = s["n1"] and nat is True
                    if full:
                        h.setdefault("check_first", today)
                        h.pop("check_lost", None)
                        done += 1
                        check = "✅"
                    else:
                        if "check_first" in h:
                            h["check_lost"] = today
                        check = "🟡" if s["rate"] > 0 else "❌"
                    why = []
                    if s["rate"] < 1:
                        why.append("falla: " + ", ".join(s["fail"]))
                    if s["err_cm"] is not None and s["err_cm"] >= MAX_ERR_CM:
                        why.append(f"error ≥ {MAX_ERR_CM:.0f} cm")
                    if s["min_runs"] < MIN_RUNS:
                        why.append(f"solo {s['min_runs']} corridas por clip")
                    if s["n1"] and nat is None:
                        why.append("lo hace; falta tu nota de naturalidad")
                    if r is not None:
                        why.append(f"nota del {r['date']} (corrida {r['run_id']})")
                        if r.get("defectos"):
                            why.append("defectos: " + ", ".join(r["defectos"]))
                    first = f"check desde {h['check_first']}" if full else ""
                    lost = f"⚠️ perdió el check el {h['check_lost']}" if h.get("check_lost") else ""
                    detail = "; ".join(x for x in [first, lost, *why] if x)
                rows.append(f"| {check} | {it['nombre']} | {lo_hace} | {nat_txt} | ⬜ | ⬜ | {detail} |")
    HIST.write_text(json.dumps(hist, indent=2, ensure_ascii=False) + "\n")

    head = [
        "# Checklist de habilidades del futbolista",
        "",
        f"Última medición: **{label}** ({today}), archivo `{src.relative_to(REPO) if src.is_absolute() else src}`.",
        f"**Con check: {done} de {total}.** Lo hacen (sin medir aún si es natural): {does}.",
        "",
        "Orden: primero moverse como un humano de forma natural (etapa 1), luego lo atlético para el fútbol (etapa 2),",
        "luego el balón (etapa 3). Los checks los calcula `retarget/update_checklist.py`; no se editan a mano.",
        "",
        "Una habilidad tiene ✅ solo si cumple **las dos** columnas:",
        f"- **Lo hace:** imita sus clips en MuJoCo con 100% de éxito en todas las corridas (al menos {MIN_RUNS} por clip) "
        f"y error de posición medio < {MAX_ERR_CM:.0f} cm. Formato: éxito · error medio.",
        "- **Natural:** se mueve como un humano real, medido con física: pies que no patinan, suavidad como la del "
        "humano real, fuerzas articulares y de contacto en rangos humanos, y la nota visual de Brandon. "
        f"Hoy cuenta tu nota en el review del PR de cada corrida: ≥ {NATURAL_MIN}/5 = natural. Las métricas físicas se sumarán después.",
        "- Después: **cuando se pide** (responde a órdenes) y **robusto** (aguanta empujones y variantes).",
        "- ✅ logrado · 🟡 a veces · ❌ no · ⬜ sin prueba todavía.",
    ]
    OUT.write_text("\n".join(head + rows) + "\n")
    print(f"{OUT}: check {done}/{total}, lo hacen {does}")


if __name__ == "__main__":
    main()
