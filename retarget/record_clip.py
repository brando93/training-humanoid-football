"""Graba en video (MP4) al tracker de Anatomical SOMA ejecutando un clip en MuJoCo (física real, CPU).

Envuelve inference_agent.py de ProtoMotions: tras cada paso de control renderiza fuera de pantalla con una
cámara que sigue a la cadera. Graba el primer episodio (o hasta --seconds).

Uso (desde la raíz del repo):
  phase0_basics/.venv/bin/python retarget/record_clip.py data/cmu_motions/patear_balon_futbol/cmu_10_01.motion out.mp4
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import mujoco
import numpy as np

REPO = Path(__file__).resolve().parents[1]
PM = Path(os.environ.get("PM_ROOT", REPO / "third_party" / "ProtoMotions"))  # en la instancia: /opt/humanoid/ProtoMotions
PY = Path(os.environ.get("PY_BIN", REPO / "phase0_basics" / ".venv" / "bin" / "python"))  # en la instancia: /opt/humanoid/venv/bin/python
CKPT = os.environ.get("CHECKPOINT", "data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt")
W, H, FPS = 960, 540, 30


def main() -> None:
    motion, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    label = sys.argv[3] if len(sys.argv) > 3 else motion.stem
    max_s = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0
    # Una sola pasada del clip: al terminar, ProtoMotions reinicia el episodio (el humanoide salta al inicio)
    # y eso se veía como un "final inestable". Se graba como máximo el largo del clip.
    if motion.is_file():
        import torch
        m = torch.load(motion, map_location="cpu", weights_only=False)
        d = m if isinstance(m, dict) else vars(m)
        n = next(v.shape[0] for v in d.values() if hasattr(v, "shape") and getattr(v, "ndim", 0) > 1)
        max_s = min(max_s, max(n - 2, 1) / float(d.get("fps", 30)))
    lib = out.with_suffix(".pt")
    subprocess.run([str(PY), "protomotions/components/motion_lib.py", "--motion-path", str(motion.parent if motion.is_dir() else motion),
                    "--output-file", str(lib)], cwd=PM, check=True, capture_output=True)
    sys.path.insert(0, str(PM))
    os.chdir(PM)
    from protomotions.simulator.mujoco import simulator as simmod

    state = {"r": None, "t": 0.0, "next": 0.0, "frames": [], "cam": None, "steps": 0}
    orig = simmod.MujocoSimulator._physics_step

    def patched(self):
        orig(self)
        st = state
        if st["r"] is None:
            self.model.vis.global_.offwidth = max(self.model.vis.global_.offwidth, W)
            self.model.vis.global_.offheight = max(self.model.vis.global_.offheight, H)
            st["r"] = mujoco.Renderer(self.model, height=H, width=W)
            cam = mujoco.MjvCamera()
            cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam.distance, cam.elevation, cam.azimuth = 4.0, -12.0, 135.0
            st["cam"] = cam
            st["dt"] = self.model.opt.timestep * self.decimation
        st["t"] += st["dt"]
        if st["t"] + 1e-9 >= st["next"]:
            st["next"] += 1.0 / FPS
            pelvis = self.data.qpos[0:3]
            c = st["cam"].lookat
            c[:] = pelvis if st["cam"].lookat.any() is False or not st["frames"] else 0.9 * c + 0.1 * pelvis
            c[2] = 0.9
            st["r"].update_scene(self.data, camera=st["cam"])
            st["frames"].append(st["r"].render().copy())
        if st["t"] >= max_s:
            # ProtoMotions intercepta SystemExit y sale con error: se guarda el video aquí y se sale directo.
            write_video(st["frames"])
            lib.unlink(missing_ok=True)
            print(out, flush=True)
            os._exit(0)

    def write_video(frames):
        print(f"{len(frames)} cuadros", flush=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        from PIL import Image, ImageDraw, ImageFont
        font = ImageFont.load_default()
        for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            if os.path.exists(f):  # Mac / Ubuntu (instancia de entrenamiento)
                font = ImageFont.truetype(f, 30)
                break
        for f in frames:
            im = Image.fromarray(f)
            d = ImageDraw.Draw(im)
            d.rectangle([10, 10, 20 + d.textlength(label, font=font), 52], fill=(0, 0, 0))
            d.text((15, 14), label, fill=(255, 255, 255), font=font)
            ff.stdin.write(np.asarray(im).tobytes())
        ff.stdin.close()
        ff.wait()

    simmod.MujocoSimulator._physics_step = patched
    sys.argv = ["inference_agent.py", "--simulator", "mujoco", "--checkpoint", CKPT, "--motion-file", str(lib),
                "--num-envs", "1", "--headless", "--full-eval"]
    import runpy
    try:
        runpy.run_path("protomotions/inference_agent.py", run_name="__main__")
    except SystemExit:
        pass
    write_video(state["frames"])
    lib.unlink(missing_ok=True)
    print(out)


if __name__ == "__main__":
    main()
