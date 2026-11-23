"""Genera docs/checklist_habilidades.md a partir de configs/skills_checklist.yaml y una medición de
retarget/eval_repeat.py. Los checks se calculan, nunca se ponen a mano.

Nivel 1 ("puede hacerlo") = 100% de éxito en todas las corridas, >= MIN_RUNS por clip, error medio < 10 cm.
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
GROUPS = {
    "postura_y_equilibrio": "Postura y equilibrio", "locomocion": "Locomoción", "cambios_de_ritmo": "Cambios de ritmo",
    "cambios_de_direccion": "Cambios de dirección", "desplazamientos": "Desplazamientos", "salto": "Salto",
    "patada_sin_balon": "Patada (sin balón)", "suelo": "Suelo", "fisica": "Física del balón",
    "basicas_B0_B5": "Básicas con balón (B0–B5)", "juego_B6_B9": "Juego (B6–B9)",
}


def skill_stats(result: dict) -> dict[str, dict]:
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
    src = Path(sys.argv[1])
    label = sys.argv[2] if len(sys.argv) > 2 else src.stem
    stats = skill_stats(json.loads(src.read_text()))
    cfg = yaml.safe_load(CFG.read_text())
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    today = date.today().isoformat()

    rows, total, done = [], 0, 0
    for area, groups in cfg.items():
        rows.append(f"\n## {'Cuerpo (Fase 3)' if area == 'cuerpo' else 'Con balón (Fases F, 4 y 5)'}\n")
        rows.append("| | Habilidad | Nivel 1: puede hacerlo | Nivel 2: cuando se pide | Nivel 3: robusto | Detalle |")
        rows.append("|---|---|---|---|---|---|")
        for group, items in groups.items():
            rows.append(f"| | **{GROUPS.get(group, group)}** | | | | |")
            for it in items:
                total += 1
                h = hist.setdefault(it["id"], {})
                s = stats.get(it["eval"]) if it["eval"] else None
                if s is None:
                    n1, detail = "⬜ sin prueba", "Faltan clips o métrica" if area == "cuerpo" else "Pendiente de su fase"
                    check = "⬜"
                else:
                    pct = f"{s['rate'] * 100:.0f}%"
                    err = f"{s['err_cm']:.1f} cm" if s["err_cm"] is not None else "—"
                    if s["n1"]:
                        h.setdefault("n1_first", today)
                        h.pop("n1_lost", None)
                        n1, check = f"✅ {pct} · {err}", "✅"
                        done += 1
                    else:
                        if "n1_first" in h:
                            h["n1_lost"] = today
                        check = "🟡" if s["rate"] > 0 else "❌"
                        n1 = f"{check} {pct} · {err}"
                    why = []
                    if s["rate"] < 1:
                        why.append("falla: " + ", ".join(s["fail"]))
                    if s["err_cm"] is not None and s["err_cm"] >= MAX_ERR_CM:
                        why.append(f"error ≥ {MAX_ERR_CM:.0f} cm")
                    if s["min_runs"] < MIN_RUNS:
                        why.append(f"solo {s['min_runs']} corridas por clip")
                    first = f"check desde {h['n1_first']}" if "n1_first" in h and s["n1"] else ""
                    lost = f"⚠️ lo perdió el {h['n1_lost']} (lo tenía desde {h['n1_first']})" if h.get("n1_lost") else ""
                    detail = "; ".join(x for x in [first, lost, *why] if x) or f"{s['clips']} clips × {s['min_runs']} corridas"
                rows.append(f"| {check} | {it['nombre']} | {n1} | ⬜ | ⬜ | {detail} |")
    HIST.write_text(json.dumps(hist, indent=2, ensure_ascii=False) + "\n")

    head = [
        "# Checklist de habilidades del futbolista",
        "",
        f"Última medición: **{label}** ({today}), archivo `{src.relative_to(REPO) if src.is_absolute() else src}`.",
        f"**Nivel 1 logrado: {done} de {total} habilidades.**",
        "",
        "Los checks los calcula `retarget/update_checklist.py`; no se editan a mano.",
        "",
        f"- **Nivel 1, puede hacerlo:** imita sus clips de mocap en MuJoCo con **100% de éxito en todas las corridas** "
        f"(al menos {MIN_RUNS} por clip) y error de posición medio < {MAX_ERR_CM:.0f} cm.",
        "- **Nivel 2, cuando se pide:** lo hace ante una orden (dirección, velocidad, momento). Fase 3c.",
        "- **Nivel 3, robusto:** lo mantiene con empujones y variantes. Fase 3c.",
        "- ✅ logrado · 🟡 a veces · ❌ nunca · ⬜ sin prueba todavía. Formato: éxito · error medio.",
    ]
    OUT.write_text("\n".join(head + rows) + "\n")
    print(f"{OUT}: nivel 1 {done}/{total}")


if __name__ == "__main__":
    main()
