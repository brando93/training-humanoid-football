"""Retargeting de CMU Motion Capture a Anatomical SOMA (ProtoMotions), en CPU.

Pasos por trial:
  1. ASF/AMC -> posiciones 3D de las articulaciones de CMU (cmu_asf_amc.py), en metros y marco SOMA.
  2. Escalado uniforme por sujeto: largo de pierna de SOMA / largo de pierna del sujeto.
  3. Cinemática inversa en MuJoCo (Gauss-Newton amortiguado, por cuadro, a 30 fps): ajusta la
     posición/orientación de la cadera y los 52 ángulos de SOMA para que sus articulaciones coincidan
     con las de CMU, respetando los límites articulares. Cada cuadro arranca del anterior (continuidad).
  4. Exportación con las funciones de ProtoMotions (las mismas del conversor de G1): cinemática directa,
     velocidades, altura sobre el suelo, contactos de pies -> archivo .motion.

Uso (desde la raíz del repo, con el entorno local):
  phase0_basics/.venv/bin/python retarget/cmu_to_anatomic_soma.py --config configs/skills_cmu.yaml
  phase0_basics/.venv/bin/python retarget/cmu_to_anatomic_soma.py --trials 16_08 10_01
  phase0_basics/.venv/bin/python retarget/cmu_to_anatomic_soma.py --smooth-hz 6 --out data/cmu_motions_s6
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
import torch
import yaml
from scipy.spatial.transform import Rotation

REPO = Path(__file__).resolve().parents[1]
PM = REPO / "third_party" / "ProtoMotions"
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(PM))
sys.path.insert(0, str(PM / "data" / "scripts"))

from cmu_asf_amc import CMU_FPS, CMU_TO_SOMA, load_trial  # noqa: E402

MJCF = PM / "protomotions" / "data" / "assets" / "mjcf" / "anatomic_soma.xml"
OUT_FPS = 30

# Cuerpo de SOMA <- extremo del hueso de CMU, con su peso en la cinemática inversa.
# Piernas y pies pesan más: son los que sostienen al humanoide y los que más importan en fútbol.
KEYPOINTS = [
    ("Hips", "root", 4.0),
    ("LeftLeg_x_link", "lhipjoint", 2.0),
    ("RightLeg_x_link", "rhipjoint", 2.0),
    ("LeftShin", "lfemur", 3.0),
    ("RightShin", "rfemur", 3.0),
    ("LeftFoot_x_link", "ltibia", 4.0),
    ("RightFoot_x_link", "rtibia", 4.0),
    ("LeftToeBase", "lfoot", 3.0),
    ("RightToeBase", "rfoot", 3.0),
    ("Neck1_x_link", "lowerneck", 1.0),
    ("Head_x_link", "upperneck", 0.5),
    ("LeftArm_x_link", "lclavicle", 1.0),
    ("RightArm_x_link", "rclavicle", 1.0),
    ("LeftForeArm", "lhumerus", 0.7),
    ("RightForeArm", "rhumerus", 0.7),
    ("LeftHand_x_link", "lradius", 0.5),
    ("RightHand_x_link", "rradius", 0.5),
]


class SomaIK:
    def __init__(self, mjcf: Path = MJCF):
        self.m = mujoco.MjModel.from_xml_path(str(mjcf))
        self.d = mujoco.MjData(self.m)
        self.body_ids = [self.m.body(b).id for b, _, _ in KEYPOINTS]
        self.weights = np.repeat(np.array([w for _, _, w in KEYPOINTS]), 3)
        mujoco.mj_forward(self.m, self.d)
        p = lambda n: self.d.xpos[self.m.body(n).id].copy()  # noqa: E731
        self.leg_length = np.linalg.norm(p("LeftShin") - p("LeftLeg_x_link")) + np.linalg.norm(
            p("LeftFoot_x_link") - p("LeftShin")
        )
        # Límites de los hinges (qpos 7: en adelante, un valor por articulación).
        self.lo = self.m.jnt_range[1:, 0].copy()
        self.hi = self.m.jnt_range[1:, 1].copy()
        self.jacp = np.zeros((3, self.m.nv))

    def solve_frame(self, targets: np.ndarray, qpos0: np.ndarray, iters: int, damping: float = 1e-2) -> tuple[np.ndarray, float]:
        m, d = self.m, self.d
        d.qpos[:] = qpos0
        dq = np.zeros(m.nv)
        err = np.inf
        for _ in range(iters):
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            cur = d.xpos[self.body_ids]
            r = (targets - cur).reshape(-1) * self.weights
            err = float(np.sqrt(np.mean(np.sum((targets - cur) ** 2, axis=1))))
            J = np.empty((3 * len(self.body_ids), m.nv))
            for k, bid in enumerate(self.body_ids):
                mujoco.mj_jacBody(m, d, self.jacp, None, bid)
                J[3 * k : 3 * k + 3] = self.jacp
            J *= self.weights[:, None]
            H = J.T @ J + damping * np.eye(m.nv)
            dq = np.linalg.solve(H, J.T @ r)
            mujoco.mj_integratePos(m, d.qpos, dq, 1.0)
            d.qpos[7:] = np.clip(d.qpos[7:], self.lo, self.hi)
            if np.abs(dq).max() < 1e-4:
                break
        mujoco.mj_kinematics(m, d)
        cur = d.xpos[self.body_ids]
        err = float(np.sqrt(np.mean(np.sum((targets - cur) ** 2, axis=1))))
        return d.qpos.copy(), err


def lowpass(pos: dict[str, np.ndarray], cutoff_hz: float, fps: float = CMU_FPS) -> dict[str, np.ndarray]:
    """Filtro Butterworth de 4º orden, fase cero (filtfilt): quita el temblor del mocap sin retrasar el movimiento."""
    from scipy.signal import butter, filtfilt

    b, a = butter(4, cutoff_hz / (fps / 2))
    pad = min(3 * max(len(a), len(b)), len(next(iter(pos.values()))) - 1)
    return {k: filtfilt(b, a, v, axis=0, padlen=pad) for k, v in pos.items()}


def clean_trial(pos: dict[str, np.ndarray], rot: dict[str, np.ndarray], max_speed: float = 12.0):
    """Recorta cuadros sin datos de mocap: raíz en (0,0,0) exacto o saltos imposibles (> max_speed m/s).

    Ej.: 104_01 trae ~1 s con la cadera en el origen y luego salta 2,4 m. Se queda el tramo continuo más largo.
    """
    root = pos["root"]
    T = len(root)
    bad = np.all(np.abs(root) < 1e-6, axis=1)
    jump = np.zeros(T, dtype=bool)
    jump[1:] = np.linalg.norm(np.diff(root, axis=0), axis=1) * CMU_FPS > max_speed
    best, start = (0, 0), None
    for i in range(T + 1):
        ok = i < T and not bad[i] and not (jump[i] and start is not None)
        if i < T and jump[i] and start is not None:  # el salto corta el tramo y empieza otro aquí
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None if bad[i] else i
            continue
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    a, b = best
    trimmed = (a, T - b)
    return {k: v[a:b] for k, v in pos.items()}, {k: v[a:b] for k, v in rot.items()}, trimmed


def retarget_trial(ik: SomaIK, asf: Path, amc: Path, smooth_hz: float = 0.0, smooth_out: bool = False) -> tuple[np.ndarray, dict]:
    pos, rot, skel = load_trial(asf, amc)
    pos, rot, trimmed = clean_trial(pos, rot)
    if smooth_hz > 0:
        pos = lowpass(pos, smooth_hz)
    step = max(1, round(CMU_FPS / OUT_FPS))
    leg_cmu = np.linalg.norm(pos["lfemur"][0] - pos["lhipjoint"][0]) + np.linalg.norm(pos["ltibia"][0] - pos["lfemur"][0])
    scale = ik.leg_length / leg_cmu
    T = len(range(0, len(pos["root"]), step))
    qpos = np.zeros((T, ik.m.nq))
    errs = np.zeros(T)
    q = ik.d.qpos.copy()
    for k, f in enumerate(range(0, len(pos["root"]), step)):
        targets = np.stack([pos[c][f] for _, c, _ in KEYPOINTS]) * scale
        # Estimación inicial de la cadera: posición y orientación de la raíz de CMU, en ejes SOMA.
        R_soma = CMU_TO_SOMA @ (CMU_TO_SOMA.T @ rot["root"][f]) @ CMU_TO_SOMA.T
        q[0:3] = targets[0]
        xyzw = Rotation.from_matrix(R_soma).as_quat()
        q[3:7] = [xyzw[3], xyzw[0], xyzw[1], xyzw[2]]
        q, errs[k] = ik.solve_frame(targets, q, iters=150 if k == 0 else 25)
        qpos[k] = q
    if smooth_out and smooth_hz > 0 and T > 15:
        # Opcional: filtrar también la salida de la IK (cadera y 52 ángulos). Medido el 2026-11-22: a 6 Hz
        # sube el deslizamiento de pies de 6,4 a 10,1 cm/s, porque mueve el pie apoyado. Apagado por defecto.
        from scipy.signal import butter, filtfilt

        b, a = butter(4, min(smooth_hz, 0.4 * OUT_FPS) / (OUT_FPS / 2))
        qpos[:, 0:3] = filtfilt(b, a, qpos[:, 0:3], axis=0)
        qpos[:, 7:] = np.clip(filtfilt(b, a, qpos[:, 7:], axis=0), ik.lo, ik.hi)
    info = {
        "frames": T,
        "duration_s": round(T / OUT_FPS, 2),
        "scale": round(float(scale), 3),
        "trimmed_frames_start_end_120fps": list(trimmed),
        "smooth_hz": smooth_hz,
        "smooth_out": smooth_out,
        "ik_rmse_cm_mean": round(float(errs.mean() * 100), 2),
        "ik_rmse_cm_max": round(float(errs.max() * 100), 2),
    }
    return qpos, info


def export_motion(qpos_np: np.ndarray, out: Path) -> dict:
    """Mismo procedimiento que data/scripts/convert_g1_csv_to_proto.py de ProtoMotions."""
    from contact_detection import compute_contact_labels_from_pos_and_vel
    from protomotions.components.pose_lib import (
        compute_cartesian_velocity,
        extract_kinematic_info,
        extract_qpos_from_transforms,
        extract_transforms_from_qpos,
        fk_from_transforms_with_velocities,
    )

    ki = extract_kinematic_info(str(MJCF))
    qpos = torch.tensor(qpos_np, dtype=torch.float32)
    root_pos, rot_mats = extract_transforms_from_qpos(ki, qpos)
    motion = fk_from_transforms_with_velocities(
        kinematic_info=ki, root_pos=root_pos, joint_rot_mats=rot_mats, fps=OUT_FPS,
        compute_velocities=True, velocity_max_horizon=3,
    )
    q2 = extract_qpos_from_transforms(ki, root_pos, rot_mats)
    motion.dof_pos = q2[:, 7:]
    motion.dof_vel = compute_cartesian_velocity(batched_robot_pos=q2[:, 7:].unsqueeze(1), fps=OUT_FPS).squeeze(1)
    shift = motion.fix_height_per_frame(height_offset=0.02)
    if motion.rigid_body_vel is not None:
        vd = torch.zeros(shift.shape[0], 1, 3)
        vd[:-1] = ((shift[1:] - shift[:-1]).unsqueeze(1)) / motion.motion_dt
        motion.rigid_body_vel = motion.rigid_body_vel + vd
    motion.fix_height(height_offset=0.04)
    motion.rigid_body_contacts = compute_contact_labels_from_pos_and_vel(
        positions=motion.rigid_body_pos, velocity=motion.rigid_body_vel, vel_thres=0.15, height_thresh=0.1
    ).to(torch.bool)
    motion.local_rigid_body_rot = None
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(motion.to_dict(), str(out))
    # Calidad: deslizamiento de pies cuando están en contacto, y penetración del suelo.
    m = mujoco.MjModel.from_xml_path(str(MJCF))
    # Se mide en el antepié (ToeBase): al correr, el contacto suele ser con la punta, no el tobillo.
    feet = [m.body("LeftToeBase").id - 1, m.body("RightToeBase").id - 1]  # sin el cuerpo "world"
    p = motion.rigid_body_pos.numpy()
    c = motion.rigid_body_contacts.numpy()
    slide = []
    for fi in feet:
        v = np.linalg.norm(np.diff(p[:, fi, :2], axis=0), axis=1) * OUT_FPS
        on = c[1:, fi] & c[:-1, fi]
        if on.any():
            slide.append(v[on].mean())
    return {
        "foot_slide_cm_s": round(float(np.mean(slide) * 100), 1) if slide else None,
        "min_body_height_cm": round(float(p[:, :, 2].min() * 100), 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=REPO / "configs" / "skills_cmu.yaml")
    ap.add_argument("--trials", nargs="*", help="Solo estos trials (ej. 16_08 10_01)")
    ap.add_argument("--raw", type=Path, default=REPO / "data" / "cmu_raw")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "cmu_motions")
    ap.add_argument("--smooth-hz", type=float, default=0.0,
                    help="Frecuencia de corte del filtro pasa-bajos sobre el mocap (0 = sin filtro)")
    ap.add_argument("--smooth-out", action="store_true", help="Filtrar también la salida de la IK (empeora el deslizamiento de pies)")
    args = ap.parse_args()

    cfg = yaml.load(args.config.read_text(), Loader=yaml.BaseLoader)  # todo como texto: 16_08 no es 1608
    plan: list[tuple[str, str]] = []
    for group in cfg.values():
        for skill, trials in group.items():
            for t in trials:
                t = str(t)
                if not args.trials or t in args.trials:
                    plan.append((skill, t))
    seen, unique = set(), []
    for skill, t in plan:
        if (skill, t) not in seen:
            seen.add((skill, t)); unique.append((skill, t))

    ik = SomaIK()
    rep_path = args.out / "retarget_report.json"
    # Con --trials se actualizan solo esas entradas; no se pierde el resto del reporte.
    report = json.loads(rep_path.read_text()) if args.trials and rep_path.exists() else {}
    for skill, t in unique:
        subj = t.split("_")[0]
        t0 = time.time()
        qpos, info = retarget_trial(ik, args.raw / f"{subj}.asf", args.raw / f"{t}.amc", args.smooth_hz, args.smooth_out)
        info.update(export_motion(qpos, args.out / skill / f"cmu_{t}.motion"))
        info["seconds"] = round(time.time() - t0, 1)
        report[f"{skill}/{t}"] = info
        print(f"{skill:22} {t:7} {info}", flush=True)
    (args.out / "retarget_report.json").write_text(json.dumps(report, indent=2))
    print(f"Reporte: {args.out / 'retarget_report.json'}")


if __name__ == "__main__":
    main()
