"""Lector de CMU Motion Capture (ASF/AMC) con cinemática directa.

ASF describe el esqueleto (huesos, dirección, largo, ejes, grados de libertad).
AMC trae, por cuadro, la traslación de la raíz y los ángulos (en grados) de cada hueso.

Convenciones de CMU (verificadas en los .asf): X = izquierda del sujeto, Y = arriba, Z = adelante;
unidades de largo = pulgadas / 0.45 (`:units length 0.45`); 120 cuadros por segundo.

Salida: posición mundial del EXTREMO de cada hueso (y de la raíz) en metros, en el marco de
Anatomical SOMA: X = adelante, Y = izquierda, Z = arriba.

Fórmula estándar ASF/AMC (la misma del parser de referencia de CMU):
    C = euler_xyz(axis); L_hueso = C · euler_dofs(cuadro) · C⁻¹
    R_mundo(hueso) = R_mundo(padre) · L_hueso
    extremo(hueso) = extremo(padre) + largo · R_mundo(hueso) · dirección
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

INCH = 0.0254
CMU_FPS = 120

# CMU (X izq, Y arriba, Z adelante) -> SOMA (X adelante, Y izq, Z arriba). Rotación propia (det = +1).
CMU_TO_SOMA = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


@dataclass
class Bone:
    name: str
    direction: np.ndarray
    length: float
    axis_deg: np.ndarray
    axis_order: str
    dofs: list[str] = field(default_factory=list)
    parent: str | None = None
    children: list[str] = field(default_factory=list)

    @property
    def C(self) -> np.ndarray:
        return Rotation.from_euler(self.axis_order.lower(), self.axis_deg, degrees=True).as_matrix()


@dataclass
class Skeleton:
    bones: dict[str, Bone]
    length_scale: float  # unidades ASF -> metros
    root_order: list[str]
    root_axis: str


def parse_asf(path: Path) -> Skeleton:
    lines = [ln.strip() for ln in Path(path).read_text(errors="replace").splitlines()]
    length_unit = 1.0
    root_order, root_axis = ["TX", "TY", "TZ", "RX", "RY", "RZ"], "XYZ"
    bones: dict[str, Bone] = {
        "root": Bone("root", np.zeros(3), 0.0, np.zeros(3), "XYZ", ["tx", "ty", "tz", "rx", "ry", "rz"])
    }
    i = 0
    section = None
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(":"):
            section = ln.split()[0]
            i += 1
            continue
        tok = ln.split()
        if section == ":units" and tok and tok[0] == "length":
            length_unit = float(tok[1])
        elif section == ":root" and tok:
            if tok[0] == "order":
                root_order = [t.upper() for t in tok[1:]]
            elif tok[0] == "axis":
                root_axis = tok[1].upper()
        elif section == ":bonedata" and tok and tok[0] == "begin":
            b = {"dofs": []}
            i += 1
            while lines[i].split()[0] != "end":
                t = lines[i].split()
                if t[0] == "name":
                    b["name"] = t[1]
                elif t[0] == "direction":
                    b["direction"] = np.array([float(x) for x in t[1:4]])
                elif t[0] == "length":
                    b["length"] = float(t[1])
                elif t[0] == "axis":
                    b["axis_deg"] = np.array([float(x) for x in t[1:4]])
                    b["axis_order"] = t[4].upper()
                elif t[0] == "dof":
                    b["dofs"] = [d.lower() for d in t[1:]]
                i += 1
            bones[b["name"]] = Bone(b["name"], b["direction"], b["length"], b["axis_deg"], b["axis_order"], b["dofs"])
        elif section == ":hierarchy" and tok and tok[0] not in ("begin", "end"):
            parent = tok[0]
            for child in tok[1:]:
                bones[child].parent = parent
                bones[parent].children.append(child)
        i += 1
    # largo en ASF: unidades = pulgadas * length_unit  ->  metros = valor / length_unit * 0.0254
    return Skeleton(bones, INCH / length_unit, root_order, root_axis)


def parse_amc(path: Path) -> list[dict[str, list[float]]]:
    frames: list[dict[str, list[float]]] = []
    cur: dict[str, list[float]] | None = None
    for ln in Path(path).read_text(errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(":"):
            continue
        tok = ln.split()
        if len(tok) == 1 and tok[0].isdigit():
            cur = {}
            frames.append(cur)
        elif cur is not None:
            cur[tok[0]] = [float(x) for x in tok[1:]]
    return frames


def _euler_from_dofs(dofs: list[str], values: list[float]) -> np.ndarray:
    """Rotación de un hueso a partir de sus dofs en el orden del archivo (ejes fijos, grados)."""
    order, angles = "", []
    for d, v in zip(dofs, values):
        if d.startswith("r"):
            order += d[1]
            angles.append(v)
    if not order:
        return np.eye(3)
    return Rotation.from_euler(order, angles, degrees=True).as_matrix()


def forward_kinematics(skel: Skeleton, frames: list[dict[str, list[float]]]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Devuelve posiciones (T,3) del extremo de cada hueso y rotaciones (T,3,3), en metros y marco SOMA."""
    T = len(frames)
    pos = {name: np.zeros((T, 3)) for name in skel.bones}
    rot = {name: np.zeros((T, 3, 3)) for name in skel.bones}
    root_C = Rotation.from_euler(skel.root_axis.lower(), [0, 0, 0], degrees=True).as_matrix()
    order = []
    stack = ["root"]
    while stack:
        n = stack.pop()
        order.append(n)
        stack.extend(reversed(skel.bones[n].children))
    for f, fr in enumerate(frames):
        rv = dict(zip(skel.root_order, fr["root"]))
        root_t = np.array([rv["TX"], rv["TY"], rv["TZ"]]) * skel.length_scale
        root_R = root_C @ Rotation.from_euler(
            skel.root_axis.lower(), [rv["R" + a] for a in skel.root_axis], degrees=True
        ).as_matrix() @ root_C.T
        pos["root"][f] = CMU_TO_SOMA @ root_t
        rot["root"][f] = CMU_TO_SOMA @ root_R
        world_R = {"root": root_R}
        world_p = {"root": root_t}
        for n in order[1:]:
            b = skel.bones[n]
            C = b.C
            L = C @ _euler_from_dofs(b.dofs, fr.get(n, [0.0] * len(b.dofs))) @ C.T
            R = world_R[b.parent] @ L
            p = world_p[b.parent] + (b.length * skel.length_scale) * (R @ b.direction)
            world_R[n], world_p[n] = R, p
            pos[n][f] = CMU_TO_SOMA @ p
            rot[n][f] = CMU_TO_SOMA @ R
    return pos, rot


def load_trial(asf: Path, amc: Path) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], Skeleton]:
    skel = parse_asf(asf)
    pos, rot = forward_kinematics(skel, parse_amc(amc))
    return pos, rot, skel
