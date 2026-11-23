"""Jerk del movimiento humano REAL (clips de referencia), con la misma métrica de ProtoMotions que la simulación.

Sirve como vara de naturalidad: si el humanoide simulado tiene tanto jerk alto como el humano real, se mueve
igual de suave; si tiene mucho más, se ve robótico o tembloroso.
Escribe data/cmu_motions/reference_jerk.json: {habilidad/trial: % de ventanas de 0,4 s con jerk alto}.
"""
import json
import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "third_party" / "ProtoMotions"))
from protomotions.agents.evaluators.smoothness_calculator import SmoothnessCalculator  # noqa: E402

MOTIONS = REPO / "data" / "cmu_motions"
DT = 1 / 30  # el evaluador mide a la frecuencia de control (30 Hz)


def ref_jerk_pct(motion_file: Path) -> float:
    m = torch.load(motion_file, map_location="cpu", weights_only=False)
    pos = torch.as_tensor(m["rigid_body_pos"], dtype=torch.float32)  # [T, cuerpos, 3]
    calc = SmoothnessCalculator(torch.device("cpu"), dt=DT)  # ventana 0,4 s, umbral 6500, como el evaluador
    w = calc._compute_windowed_normalized_jerk(pos, max(4, round(calc.window_sec / DT)))
    return calc._compute_high_jerk_frame_percentage(w)


def main() -> None:
    out = {}
    for f in sorted(MOTIONS.glob("*/cmu_*.motion")):
        if f.parent.name.startswith("_"):
            continue
        out[f"{f.parent.name}/{f.stem.removeprefix('cmu_')}"] = round(ref_jerk_pct(f), 2)
    (MOTIONS / "reference_jerk.json").write_text(json.dumps(out, indent=1))
    vals = list(out.values())
    print(f"{len(vals)} clips | jerk alto del humano real: media {sum(vals)/len(vals):.1f}%  min {min(vals):.1f}%  max {max(vals):.1f}%")


if __name__ == "__main__":
    main()
