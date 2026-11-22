# Fase 0 — Fundamentos de RL (en el Mac, $0)

Objetivo: entender con las manos qué es una observación, una acción, una recompensa y cómo PPO aprende,
antes de tocar ProtoMotions. Usa el humanoide de Gymnasium (MuJoCo), que corre en CPU.

## Entorno local único
Un solo entorno (Python 3.12, un solo torch) para la Fase 0 **y** para probar ProtoMotions en MuJoCo.

1. Clonar ProtoMotions (una vez, ~120 MB con el tracker anatómico; `third_party/` está en `.gitignore`):
   ```bash
   cd ~/Projects/training-humanoid-football && mkdir -p third_party && cd third_party
   GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none https://github.com/NVlabs/ProtoMotions.git
   cd ProtoMotions && git checkout 13de0cccd06f53ce5c9cf9ec7d1932c7da73610f
   git lfs pull --include="data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/**,data/motion_for_trackers/anatomic_soma_bones_seed_mini.pt"
   ```
2. Instalar el entorno (~300 MB; ~2–5 min según la red):
   ```bash
   make local-env
   ```
3. Usarlo sin activar nada: `uv run python ...` dentro de `phase0_basics/`. O activarlo:
   `source phase0_basics/.venv/bin/activate` (salir con `deactivate`). En VS Code: *Python: Select Interpreter* →
   `phase0_basics/.venv/bin/python`.

Medido en el M3 Pro (2026-11-22): simulación ~6.500 pasos/s por entorno; entrenamiento PPO ~4.900 pasos/s con 8 entornos.

## Compuerta de MuJoCo: Anatomical SOMA en el Mac
```bash
make soma-mujoco-eval
```
Evalúa el tracker preentrenado sobre 10 clips de ejemplo con física MuJoCo en CPU (la que correrá en Unreal).
Resultado del 2026-11-22: **10/10 clips sin caídas** (`success_rate` 1,0), error medio de posición del cuerpo 4,5 cm,
error de rotación medio 0,19 rad (~11°), 7,7% de cuadros con jerk alto.

## Ejercicios

| # | Comando | Qué observar | Éxito |
|---|---|---|---|
| 1. De pie | `uv run python train.py --task stand --steps 300000` | La duración del episodio sube hasta ~1000 pasos | De pie 15 s sin caerse, desplazamiento < 0,5 m |
| 2. Caminar | `uv run python train.py --task walk --steps 1000000` | La recompensa media y la distancia crecen | Camina ≥ 10 s sin caerse |
| 3. Trampa | `uv run python train.py --task hack --steps 300000` | Recompensa alta… pero mira el video | Ver cómo explota la recompensa sin caminar |

Después de cada uno:
```bash
uv run python evaluate.py --task stand
```
Monitorear mientras entrena (otra terminal):
```bash
uv run tensorboard --logdir runs
```
Abrir http://localhost:6006 → `rollout/ep_len_mean` (cuánto aguanta) y `rollout/ep_rew_mean` (recompensa).

Tiempo medido en el M3 Pro: ~1 min por cada 300k pasos con 8 entornos (~4.900 pasos/s).

## Conceptos (versión corta)
- **Observación** (348 números en Humanoid-v5): posiciones y velocidades de las articulaciones, fuerzas de contacto.
  Es todo lo que el agente "sabe" del mundo.
- **Acción** (17 números entre -0,4 y 0,4): el torque de cada motor, 67 veces por segundo.
- **Recompensa**: un número por paso. El agente maximiza la suma. Optimiza exactamente lo que escribiste:
  si la recompensa tiene un hueco, lo encuentra (ejercicio 3).
- **Episodio**: un intento, hasta caerse o hasta 1000 pasos.
- **PPO**: prueba acciones, mide qué tan bien le fue (ventaja) y ajusta la red un poco hacia lo que
  funcionó, sin alejarse demasiado de la versión anterior (el "clip"). Por eso es estable.
- **VecNormalize**: normaliza observaciones y recompensas; sin esto, los humanoides aprenden mucho peor.

## Diagnóstico de problemas comunes
| Síntoma | Causa probable | Qué probar |
|---|---|---|
| `ep_len_mean` no sube | La recompensa por estar vivo no compensa los castigos | Bajar castigos o subir el bono de vida |
| Tiembla o vibra | Castigo de energía muy bajo | Subir el peso de `effort` |
| Se arrastra o se lanza | Recompensa hackeable (ejercicio 3) | Exigir torso alto y terminar el episodio al caer |
| Aprende y luego empeora | `learning_rate` alto | Bajarlo a 1e-4 |
