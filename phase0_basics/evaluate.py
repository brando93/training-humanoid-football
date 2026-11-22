"""Evalúa una política entrenada: métricas y video.

  uv run python evaluate.py --task stand
  uv run python evaluate.py --task walk --episodes 5

Métricas:
  - duración: cuántos pasos aguanta de pie (máximo 1000 = 15 s de simulación)
  - caídas: episodios que terminan antes por caerse
  - distancia: cuánto avanzó en x (para "walk" debe crecer; para "stand" debe ser ~0)
El video queda en runs/<tarea>_s<seed>/video.mp4.
"""

from __future__ import annotations

import argparse

import imageio.v2 as imageio
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from train import RUNS, make_env


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["stand", "walk", "hack"], default="stand")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--episodes", type=int, default=3)
    args = p.parse_args()

    run_dir = RUNS / f"{args.task}_s{args.seed}"
    model = PPO.load(run_dir / "final", device="cpu")
    venv = DummyVecEnv([lambda: make_env(args.task, render_mode="rgb_array")])
    venv = VecNormalize.load(str(run_dir / "vecnormalize.pkl"), venv)
    venv.training = False
    venv.norm_reward = False

    lengths, falls, distances, frames = [], 0, [], []
    for ep in range(args.episodes):
        obs = venv.reset()
        start_x = float(venv.envs[0].unwrapped.data.qpos[0])
        last_x = start_x
        steps, done = 0, False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, dones, infos = venv.step(action)
            steps += 1
            done = bool(dones[0])
            # Humanoid-v5 reporta x_position en info; al terminar, el entorno ya se reinició,
            # así que usamos el último valor reportado y no qpos.
            last_x = float(infos[0].get("x_position", last_x))
            if ep == 0 and steps % 2 == 0:
                frames.append(venv.envs[0].render())
        truncated = infos[0].get("TimeLimit.truncated", False)
        falls += 0 if truncated else 1
        lengths.append(steps)
        distances.append(last_x - start_x)

    print(f"Episodios: {args.episodes}")
    print(f"Duración media: {np.mean(lengths):.0f} pasos (máx. 1000)")
    print(f"Caídas: {falls}/{args.episodes}")
    print(f"Distancia media en x: {np.mean(distances):.2f} m")
    video = run_dir / "video.mp4"
    imageio.mimsave(video, frames, fps=33)
    print(f"Video: {video}")


if __name__ == "__main__":
    main()
