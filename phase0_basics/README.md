# Fase 0 — Fundamentos de RL (en el Mac, $0)

Objetivo: entender con las manos qué es una observación, una acción, una recompensa y cómo PPO aprende,
antes de tocar ProtoMotions. Usa el humanoide de Gymnasium (MuJoCo), que corre en CPU.

## Instalación
```bash
cd phase0_basics
uv sync
```

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

Tiempo en el M3 Pro: ~10–20 min por cada 300k pasos con 8 entornos (estimado; medido en la primera corrida).

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
