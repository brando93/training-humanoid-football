"""Fase 0 — fundamentos de RL con el humanoide de Gymnasium (MuJoCo) y PPO.

Tres ejercicios, todos en el Mac y sin GPU:

  stand   Mantenerse de pie quieto: sin premio por avanzar, solo por seguir "vivo" (de pie).
  walk    Caminar hacia adelante: la recompensa estándar de Humanoid-v5.
  hack    Una recompensa mal diseñada a propósito, para ver cómo el agente hace trampa.

Conceptos que aparecen (ver phase0_basics/README.md):
  - Observación: lo que el agente "siente" (posiciones y velocidades de articulaciones, etc.).
  - Acción: lo que el agente decide (17 torques, uno por motor).
  - Recompensa: el número que le dice si lo hizo bien. El agente optimiza ESO, no lo que quisimos decir.
  - PPO: el algoritmo que ajusta la red para conseguir más recompensa, sin cambiarla de golpe.

Uso:
  uv run python train.py --task stand --steps 300000
  uv run tensorboard --logdir runs        (abrir http://localhost:6006)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

RUNS = Path(__file__).parent / "runs"


class StandStillReward(gym.Wrapper):
    """Premia estar de pie con el torso alto y quieto. Castiga moverse de su sitio."""

    def __init__(self, env: gym.Env):
        super().__init__(env)
        self._start_xy = None

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._start_xy = self.unwrapped.data.qpos[0:2].copy()
        return obs, info

    def step(self, action):
        obs, _, terminated, truncated, info = self.env.step(action)
        data = self.unwrapped.data
        torso_z = data.qpos[2]
        drift = float(np.linalg.norm(data.qpos[0:2] - self._start_xy))
        speed = float(np.linalg.norm(data.qvel[0:2]))
        effort = float(np.square(action).sum())
        reward = (
            5.0                      # bono por seguir de pie (el episodio termina si cae)
            + 2.0 * (torso_z - 1.0)  # torso alto
            - 1.0 * drift            # no alejarse de donde empezó
            - 0.5 * speed            # no moverse
            - 0.1 * effort           # no gastar energía de más
        )
        info.update(torso_z=torso_z, drift=drift)
        return obs, reward, terminated, truncated, info


class HackableReward(gym.Wrapper):
    """Recompensa MAL diseñada: solo premia la velocidad hacia adelante del torso, sin pedir
    estar de pie. Suele aprender a lanzarse hacia adelante o arrastrarse: reward hacking."""

    def step(self, action):
        obs, _, terminated, truncated, info = self.env.step(action)
        reward = float(self.unwrapped.data.qvel[0])  # velocidad x del torso
        return obs, reward, terminated, truncated, info


def make_env(task: str, render_mode: str | None = None) -> gym.Env:
    if task == "walk":
        return gym.make("Humanoid-v5", render_mode=render_mode)
    if task == "stand":
        return StandStillReward(gym.make("Humanoid-v5", render_mode=render_mode, forward_reward_weight=0.0))
    if task == "hack":
        # Sin terminar el episodio al caer: así el agente puede "explotar" la recompensa en el suelo.
        return HackableReward(gym.make("Humanoid-v5", render_mode=render_mode, terminate_when_unhealthy=False))
    raise ValueError(f"tarea desconocida: {task}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--task", choices=["stand", "walk", "hack"], default="stand")
    p.add_argument("--steps", type=int, default=300_000, help="pasos totales de simulación")
    p.add_argument("--envs", type=int, default=8, help="entornos en paralelo (CPU)")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    run_dir = RUNS / f"{args.task}_s{args.seed}"
    run_dir.mkdir(parents=True, exist_ok=True)

    venv = make_vec_env(lambda: make_env(args.task), n_envs=args.envs, seed=args.seed)
    # Normalizar observaciones y recompensas ayuda mucho a PPO en humanoides.
    venv = VecNormalize(venv, norm_obs=True, norm_reward=True, clip_obs=10.0)

    model = PPO(
        "MlpPolicy",
        venv,
        n_steps=2048,
        batch_size=512,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.0,
        policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256])),
        tensorboard_log=str(RUNS / "tb"),
        seed=args.seed,
        device="cpu",  # para redes chicas y simulación en CPU, la CPU es más rápida que MPS
        verbose=1,
    )
    model.learn(
        total_timesteps=args.steps,
        tb_log_name=f"{args.task}_s{args.seed}",
        callback=CheckpointCallback(save_freq=max(50_000 // args.envs, 1), save_path=str(run_dir / "ckpt")),
        progress_bar=True,
    )
    model.save(run_dir / "final")
    venv.save(str(run_dir / "vecnormalize.pkl"))
    print(f"Guardado en {run_dir}")


if __name__ == "__main__":
    main()
