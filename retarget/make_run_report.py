"""Reporte de una corrida para revisar en un PR: clips por habilidad, checklist, métricas y plantilla de review.

Produce:
  reports/runs/<run_id>/README.md   reporte (va en el PR; las imágenes apuntan a la rama `media`)
  reports/runs/<run_id>/metrics.json resumen por habilidad
  <media_dir>/runs/<run_id>/*.gif|mp4 clips (se publican en la rama `media`, que solo guarda las últimas corridas)

Uso:
  phase0_basics/.venv/bin/python retarget/make_run_report.py --eval data/cmu_motions/repeat_baseline_v0.json \
      --run-id 2026-11-22-base --label "Tracker NVIDIA sin ajuste" --media-dir /ruta/media
  (CHECKPOINT=... en el entorno para grabar un tracker propio)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PY = REPO / "phase0_basics" / ".venv" / "bin" / "python"
MOTIONS = Path(os.environ.get("MOTIONS_DIR", REPO / "data" / "cmu_motions")).resolve()
GH_REPO = os.environ.get("GH_REPO", "brando93/training-humanoid-football")
MAX_SECONDS = 8.0
sys.path.insert(0, str(Path(__file__).parent))
from update_checklist import GROUPS, MAX_ERR_CM, STAGES, skill_stats  # noqa: E402


def media_url(run_id: str, name: str) -> str:
    return f"https://github.com/{GH_REPO}/blob/media/runs/{run_id}/{name}?raw=true"


def pick_clips(result: dict, skill: str) -> list[tuple[str, str]]:
    """Clip representativo que sale bien (el más largo) y, si hay, uno que falla."""
    clips = [(t.split("/")[-1], c) for t, c in result["clips"].items() if c["skill"] == skill]
    rep = json.loads((MOTIONS / "retarget_report.json").read_text())
    dur = lambda t: rep.get(f"{skill}/{t}", {}).get("duration_s", 0)  # noqa: E731
    good = sorted([t for t, c in clips if c["success"] == 1.0], key=dur, reverse=True)
    bad = sorted([(c["success"], t) for t, c in clips if c["success"] < 1.0])
    out = [(good[0], "bien")] if good else []
    if bad:
        out.append((bad[0][1], f"falla {bad[0][0]*100:.0f}%"))
    return out


def record(skill: str, trial: str, tag: str, title: str, out_dir: Path) -> tuple[str, str]:
    stem = f"{skill}__{trial}"
    mp4 = out_dir / f"{stem}.mp4"
    label = f"{title} | CMU {trial} | {tag}"
    subprocess.run([str(PY), str(REPO / "retarget" / "record_clip.py"), str(MOTIONS / skill / f"cmu_{trial}.motion"),
                    str(mp4), label, str(MAX_SECONDS)], cwd=REPO, capture_output=True)
    gif = out_dir / f"{stem}.gif"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp4), "-vf",
                    "fps=10,scale=320:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=48:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    str(gif)], check=True)
    return stem, tag


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", type=Path, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--media-dir", type=Path, required=True)
    ap.add_argument("--prev-eval", type=Path)
    ap.add_argument("--cost", default="—", help="Costo de la corrida, ej. '$1,10'")
    ap.add_argument("--notes", default="", help="Texto libre: qué cambió en esta corrida")
    args = ap.parse_args()

    result = json.loads(args.eval.read_text())
    stats = skill_stats(result)
    prev = skill_stats(json.loads(args.prev_eval.read_text())) if args.prev_eval else {}
    cfg = yaml.safe_load((REPO / "configs" / "skills_checklist.yaml").read_text())
    media = args.media_dir / "runs" / args.run_id
    media.mkdir(parents=True, exist_ok=True)

    jobs, items = [], []
    for stage, groups in cfg.items():
        if stage == "etapa_3_balon":
            continue
        for group, its in groups.items():
            for it in its:
                items.append((stage, group, it))
                if it["eval"] and it["eval"] in stats:
                    for trial, tag in pick_clips(result, it["eval"]):
                        jobs.append((it["eval"], trial, tag, it["nombre"]))
    print(f"Grabando {len(jobs)} clips...", flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get("WORKERS", 6))) as pool:
        recorded = list(pool.map(lambda j: record(*j, media), jobs))
    by_skill: dict[str, list[tuple[str, str]]] = {}
    for (skill, *_), rec in zip(jobs, recorded):
        by_skill.setdefault(skill, []).append(rec)
    # Compilación para verla de corrido.
    lst = media / "lista.txt"
    lst.write_text("".join(f"file '{s}.mp4'\n" for s, _ in recorded))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "24", str(media / "compilacion.mp4")], check=True)
    lst.unlink()
    for stem, _ in recorded:  # en la rama media solo quedan los GIF y la compilación
        (media / f"{stem}.mp4").unlink(missing_ok=True)

    lo_hace = sum(1 for s in stats.values() if s["n1"])
    L = [
        f"# Corrida {args.run_id}: {args.label}",
        "",
        f"- **Costo de la corrida:** {args.cost}",
        f"- **Lo hace (100% de éxito, error < {MAX_ERR_CM:.0f} cm):** {lo_hace} habilidades medidas en MuJoCo, 5 corridas por clip.",
        f"- **Compilación de todos los clips:** [compilacion.mp4]({media_url(args.run_id, 'compilacion.mp4')}).",
    ]
    if args.notes:
        L += [f"- **Qué cambió:** {args.notes}"]
    if prev:
        gained = [k for k, s in stats.items() if s["n1"] and not prev.get(k, {}).get("n1")]
        lost = [k for k, s in stats.items() if not s["n1"] and prev.get(k, {}).get("n1")]
        L += [f"- **Ganó \"lo hace\":** {', '.join(gained) or 'ninguna'}", f"- **⚠️ Perdió \"lo hace\":** {', '.join(lost) or 'ninguna'}"]
    L += ["", "Los clips son física real en MuJoCo: el humanoide se mueve solo con sus motores, imitando el mocap.", ""]

    review_ids = []
    for stage, groups in cfg.items():
        if stage == "etapa_3_balon":
            continue
        L += [f"## {STAGES[stage]}", "", "| Habilidad | Clip | Lo hace | Éxito · error | Fallas |", "|---|---|---|---|---|"]
        for group, its in groups.items():
            for it in its:
                s = stats.get(it["eval"]) if it["eval"] else None
                if s is None:
                    L.append(f"| {it['nombre']} | — | ⬜ | sin clips todavía | |")
                    continue
                review_ids.append(it["id"])
                gifs = "<br>".join(f"![{tag}]({media_url(args.run_id, stem + '.gif')})<br>{tag}" for stem, tag in by_skill.get(it["eval"], []))
                mark = "✅" if s["n1"] else ("🟡" if s["rate"] > 0 else "❌")
                err = f"{s['err_cm']:.1f} cm" if s["err_cm"] is not None else "—"
                L.append(f"| **{it['nombre']}** | {gifs} | {mark} | {s['rate']*100:.0f}% · {err} | {', '.join(s['fail'])} |")
        L.append("")

    L += [
        "## Tu review",
        "",
        "Copia este bloque en tu review (botón **Review changes**), pon una nota a cada habilidad y comenta lo que se vea mal.",
        "- **5:** indistinguible de una persona · **4:** natural con detalles menores · **3:** se nota artificial",
        "  · **2:** robótico o raro · **1:** antinatural. Deja vacío lo que no quieras calificar.",
        "- Al enviar el review, en ~1 min un commit del bot guarda tus notas en el PR y recalcula el checklist.",
        "- Luego: **merge** = este modelo pasa a ser el oficial. **Cerrar sin merge** = se descarta.",
        "",
        "```yaml",
        "naturalidad:",
        *[f"  {i}: " for i in review_ids],
        "comentarios: |",
        "  ",
        "```",
    ]
    out = REPO / "reports" / "runs" / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text("\n".join(L) + "\n")
    (out / "metrics.json").write_text(json.dumps({
        "run_id": args.run_id, "label": args.label, "cost": args.cost, "eval_file": str(args.eval.name),
        "skills": {k: {"rate": round(v["rate"], 3), "err_cm": None if v["err_cm"] is None else round(v["err_cm"], 2),
                       "lo_hace": v["n1"], "fail": v["fail"]} for k, v in sorted(stats.items())},
    }, indent=1, ensure_ascii=False) + "\n")
    print(out / "README.md")


if __name__ == "__main__":
    main()
