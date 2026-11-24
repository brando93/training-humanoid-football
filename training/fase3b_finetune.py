"""Receta de AJUSTE FINO del tracker Anatomical SOMA (Fase 3b). Hereda la receta de NVIDIA
(examples/experiments/mimic/anatomical_soma_fsq_mimic.py) y cambia solo lo necesario para afinar sin destruir
lo que el modelo ya sabe:

- Tasa de aprendizaje del actor 10x menor (5e-4 -> 5e-5; la parte Adam 1e-4 -> 1e-5): la receta original es
  para entrenar desde cero; con ella el primer paso tuvo KL 0,99 y deformó la política.
- Evaluación interna cada EVAL_EVERY épocas (40; la original: cada 200), para poder frenar a tiempo y guardar el
  mejor modelo (score_based.ckpt).
El calentamiento del crítico (actor congelado al inicio), el freno por empeoramiento y el límite de tiempo los
aplica training/train_safe.py.

Lección (corrida 2026-11-23-0546, 47/53 -> 0/53 clips): con la tasa original el primer paso de PPO deformó la
política (KL 0,99, 87% de recortes) y las estadísticas de normalización se desplazaron hacia nuestros pocos clips.
(El checkpoint de NVIDIA SÍ trae crítico; el diagnóstico inicial que lo culpaba era incorrecto.)
"""
import os

from examples.experiments.mimic.anatomical_soma_fsq_mimic import *  # noqa: F401,F403
from examples.experiments.mimic import anatomical_soma_fsq_mimic as base

ACTOR_LR = float(os.environ.get("FT_ACTOR_LR", "5e-5"))
ACTOR_ADAM_LR = float(os.environ.get("FT_ACTOR_ADAM_LR", "1e-5"))
EVAL_EVERY = int(os.environ.get("FT_EVAL_EVERY", "40"))  # cada evaluación cuesta ~3,3 min de L4: con 20, casi la mitad del entrenamiento


def agent_config(robot_cfg, env_cfg, args):
    cfg = base.agent_config(robot_cfg, env_cfg, args)
    cfg.model.actor_optimizer.lr = ACTOR_LR
    cfg.model.actor_optimizer.adam_lr = ACTOR_ADAM_LR
    cfg.evaluator.eval_metrics_every = EVAL_EVERY
    return cfg


def configure_robot_and_simulator(robot_cfg, simulator_cfg, args):
    base.configure_robot_and_simulator(robot_cfg, simulator_cfg, args)
    if os.environ.get("LOCAL_SMOKE") == "1":  # prueba local en MuJoCo (no soporta aleatorizar masas)
        simulator_cfg.domain_randomization = None
