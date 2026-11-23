"""Lee la review de Brandon en un PR de corrida (bloque YAML con `naturalidad:`) y la guarda.

Escribe:
  reports/runs/<run_id>/review.json   la review de esa corrida
  docs/naturalness_reviews.json       la última nota de cada habilidad (la usa update_checklist.py: >= 4 = natural)

Uso (con gh autenticado, o GH_TOKEN en Actions):
  python retarget/apply_review.py --pr 3 [--reviewer brando93]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
AGG = REPO / "docs" / "naturalness_reviews.json"
BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.S)
# Etiquetas de defecto: cada una corresponde a un ajuste concreto (docs/review_guide.md).
DEFECTOS = {"patina", "rigido", "brusco", "se_cae", "final_inestable", "postura_rara", "brazos_raros", "falla", "otro"}
VS = {"mejor", "igual", "peor"}


def gh(path: str) -> list | dict:
    return json.loads(subprocess.run(["gh", "api", "--paginate", path], check=True, capture_output=True, text=True).stdout)


def find_review(pr: int, reviewer: str) -> tuple[dict, str, str] | None:
    """Último bloque `naturalidad:` del revisor, en reviews o comentarios del PR."""
    texts = []
    for r in gh(f"repos/{{owner}}/{{repo}}/pulls/{pr}/reviews"):
        if r["user"]["login"] == reviewer and r.get("body"):
            texts.append((r["submitted_at"], r["body"], r["html_url"]))
    for c in gh(f"repos/{{owner}}/{{repo}}/issues/{pr}/comments"):
        if c["user"]["login"] == reviewer:
            texts.append((c["created_at"], c["body"], c["html_url"]))
    for when, body, url in sorted(texts, reverse=True):
        for m in BLOCK.finditer(body):
            data = yaml.safe_load(m.group(1)) or {}
            if isinstance(data, dict) and "naturalidad" in data:
                return data, when, url
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--reviewer", default="brando93")
    args = ap.parse_args()
    branch = gh(f"repos/{{owner}}/{{repo}}/pulls/{args.pr}")["head"]["ref"]
    if not branch.startswith("run/"):
        raise SystemExit(f"El PR {args.pr} no es de una corrida (rama {branch}).")
    run_id = branch.removeprefix("run/")
    found = find_review(args.pr, args.reviewer)
    if not found:
        raise SystemExit("No hay bloque `naturalidad:` del revisor todavía.")
    data, when, url = found
    notas, detalle = {}, {}
    for k, v in (data.get("naturalidad") or {}).items():
        entry = v if isinstance(v, dict) else {"nota": v}  # formato simple (solo la nota) o completo
        nota, vs = entry.get("nota"), entry.get("vs_anterior")
        defectos = [str(d).strip() for d in (entry.get("defectos") or [])]
        if nota in (None, "") and not vs and not defectos:
            continue
        if nota not in (None, ""):
            nota = int(nota)
            if not 1 <= nota <= 5:
                raise SystemExit(f"Nota fuera de rango para {k}: {nota} (debe ser 1-5)")
            notas[k] = nota
        if vs and vs not in VS:
            raise SystemExit(f"vs_anterior de {k} debe ser mejor, igual o peor (no '{vs}')")
        malos = [d for d in defectos if d not in DEFECTOS]
        if malos:
            raise SystemExit(f"Etiquetas desconocidas en {k}: {malos}. Válidas: {sorted(DEFECTOS)}")
        detalle[k] = {"nota": notas.get(k), "vs_anterior": vs, "defectos": defectos}
    review = {"run_id": run_id, "pr": args.pr, "reviewer": args.reviewer, "date": when[:10], "url": url,
              "naturalidad": notas, "detalle": detalle, "comentarios": (data.get("comentarios") or "").strip()}
    out = REPO / "reports" / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "review.json").write_text(json.dumps(review, indent=1, ensure_ascii=False) + "\n")
    agg = json.loads(AGG.read_text()) if AGG.exists() else {}
    for k, d in detalle.items():
        prev = agg.get(k, {})
        agg[k] = {"nota": d["nota"] if d["nota"] is not None else prev.get("nota"), "vs_anterior": d["vs_anterior"],
                  "defectos": d["defectos"], "run_id": run_id, "date": review["date"], "pr": args.pr}
        if agg[k]["nota"] is None:
            agg.pop(k)
    AGG.write_text(json.dumps(dict(sorted(agg.items())), indent=1, ensure_ascii=False) + "\n")
    print(f"{len(detalle)} habilidades revisadas por {args.reviewer} en {run_id}: {detalle}")


if __name__ == "__main__":
    main()
