# Diario de experimentos

Formato de cada entrada:

```
## AAAA-MM-DD — <título corto>
- Hipótesis: cambio X para mover la métrica Y
- Cambio: PR #N, config/commit
- Resultado: métricas antes → después, nota de realismo
- Decisión: mantener / revertir / iterar
```

## 2026-11-22 — Arranque
- Infraestructura I1 lista en AWS; repo creado. Sin entrenamientos todavía.

## 2026-11-22 — Infraestructura I2–I4
- I2: OIDC funcionando (tras ajustar al formato de subject inmutable). I3: VPC sin NAT, S3, IAM; costo fijo $0.
- Cambio de base: el checkpoint SMPL de MaskedMimic ya no existe → Anatomical SOMA + prior GPC.
- Objetivo final redefinido: minijuego en Unreal 5 con MuJoCo embebido (plan v3).
- Corrección de costo: spot g6.2xlarge ~$0,75/h (no ~$0,45) → ~1,3 h/día; g4dn.2xlarge ~$0,26/h como alternativa a evaluar.
- Build de la AMI: 3 intentos fallidos (variables de Packer, instalación de Isaac Lab, choque de numpy), cada uno
  terminado solo y con costo de centavos. Gasto del mes tras el día: $0,28.

## 2026-11-22 — Compuerta de MuJoCo en el Mac (primer resultado real)
- Hipótesis: el tracker preentrenado de Anatomical SOMA (entrenado en Isaac Lab) se sostiene en MuJoCo, la física del juego.
- Cambio: entorno local único (Python 3.12) + `make soma-mujoco-eval`, en CPU y sin GPU.
- Resultado: 10/10 clips de BONES-SEED (mini) sin caídas; error de posición medio 4,5 cm (máx. 14 cm);
  rotación 0,19 rad (~11°) de media, 0,75 rad de máximo; error articular medio 0,11 rad; 7,7% de cuadros con jerk alto.
- Decisión: la ruta Isaac Lab → MuJoCo → Unreal es viable. El jerk y los picos de rotación son lo que hay que vigilar
  para el realismo. Siguiente: verlo en video y empezar la Fase 0.
- Fase 0 medida: PPO ~4.900 pasos/s en el M3 Pro; "de pie" (300k) ~1 min.

## 2026-11-22 — Primer video de SOMA en MuJoCo (Mac)
- Grabado desde el visor de MuJoCo (`mjpython`, tecla L) con dos proyectiles (tecla J): 17,5 s a 30 fps.
- Visual: sigue de cerca los marcadores de referencia; incluye un clip de levantarse del suelo; tras los proyectiles
  sigue en pie (`OK` en todos los pasos). Cuadros en `docs/media/2026-11-22-soma-mujoco-frames.jpg`.
- ProtoMotions también guarda el movimiento simulado (`.motion`): base para exportar animación a Unreal.
- Pendiente: la nota de realismo (1–5) de Brandon.

## 2026-11-22 — Fase 3a: batería de funciones básicas con clips de CMU
- Hipótesis: el tracker preentrenado puede ejecutar las funciones básicas de un futbolista con datos que nunca vio.
- Cambio: retargeting propio CMU (ASF/AMC) → Anatomical SOMA (`retarget/`), 55 clips, error IK ~3 cm; batería en
  MuJoCo en paralelo (`retarget/run_battery_3a.py`).
- Resultado: todas las 18 habilidades lograron éxito al menos una vez; patada de fútbol 6/6. Fiabilidad < 90% en
  carrera rápida, trote→carrera, un pie y levantarse boca abajo. La evaluación es estocástica (resultados cambian
  entre corridas). Clips del sujeto 143 (niño) y clips < 1 s descartados como pruebas injustas.
- Decisión: pasar a 3b/3c (ajuste fino en GPU con estos clips + comandos) cuando AWS apruebe la cuota.
  Pendientes locales: 5 repeticiones por clip para estadística fiable y suavizado del retargeting.
