"""Empaqueta los clips de entrenamiento en un solo .pt de ProtoMotions para la GPU:
los medidos (configs/skills_cmu.yaml, menos configs/training_set.yaml:excluir) más los de solo entrenar
(configs/training_extra_cmu.yaml, convertidos a data/cmu_motions_extra/).

  phase0_basics/.venv/bin/python retarget/pack_training_set.py            # -> data/cmu_soma_train.pt
  aws s3 cp data/cmu_soma_train.pt s3://humanoid-artifacts-611606529792/data/cmu_soma_train.pt --profile humanoid
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PM = Path(os.environ.get("PM_ROOT", REPO / "third_party" / "ProtoMotions"))
PY = os.environ.get("PY_BIN", str(REPO / "phase0_basics" / ".venv" / "bin" / "python"))
MOTIONS = REPO / "data" / "cmu_motions"
EXTRA = REPO / "data" / "cmu_motions_extra"


def main() -> None:
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "data" / "cmu_soma_train.pt"
    skills = yaml.load((REPO / "configs" / "skills_cmu.yaml").read_text(), Loader=yaml.BaseLoader)  # 49_18 no es número
    excl = set((yaml.load((REPO / "configs" / "training_set.yaml").read_text(), Loader=yaml.BaseLoader) or {}).get("excluir") or {})
    extra = yaml.load((REPO / "configs" / "training_extra_cmu.yaml").read_text(), Loader=yaml.BaseLoader)
    keep, dropped = [], []
    plan = [(root, skill, t) for root, cfg in ((MOTIONS, skills), (EXTRA, extra))
            for group in cfg.values() for skill, trials in group.items() for t in trials]
    for root, skill, t in plan:
        f = root / skill / f"cmu_{t}.motion"
        if not f.exists():
            sys.exit(f"Falta {f}")
        (dropped if str(t) in excl else keep).append(f)
    with tempfile.TemporaryDirectory() as tmp:
        for f in keep:  # nombre único por habilidad: un trial puede estar en dos habilidades (127_04)
            shutil.copy(f, Path(tmp) / f"{f.parent.name}__{f.name}")
        subprocess.run([PY, "protomotions/components/motion_lib.py", "--motion-path", tmp, "--output-file", str(out)],
                       cwd=PM, check=True, capture_output=True)
    print(f"{out}: {len(keep)} clips de entrenamiento; excluidos {len(dropped)}: {sorted(f.stem for f in dropped)}")


if __name__ == "__main__":
    main()
