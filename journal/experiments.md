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

## 2026-11-22 — Fiabilidad ×5, suavizado descartado, GPU en AWS y freno de costos
- Evaluación ×5 por clip (`retarget/eval_repeat.py`): 47/54 clips 100%. Fallas fijas en 4 clips de carrera cortos
  que empiezan en plena carrera (104_01 además traía 0,46 s sin datos: `clean_trial` lo recorta, sigue fallando).
  Inestables reales: 124_11, 144_05, 140_03.
- Suavizado del retargeting: no baja el jerk de la simulación (14,9% → 16,1%) y empeora "un pie"; descartado.
  El jerk viene del tracker → se ataca con ajuste fino (3b).
- Video: `retarget/record_clip.py` graba el tracker en MuJoCo; compilación de 11 clips (39 s) para Brandon.
- AWS: cuota G aprobada (8 vCPU spot y bajo demanda); EULA de Isaac Sim aceptada por Brandon (SSM).
  g4dn.2xlarge sin capacidad spot en us-east-1a–d; g6.2xlarge (L4) sí en us-east-1d a $0,73/h.
- Prueba L4 (`scripts/remote/gpu-bench.sh`, 2048 entornos, 30 iteraciones, 55 clips CMU): arranque ~13 min
  (Isaac Sim + compilación de torch), luego ~12 s por época de 65.536 pasos → ~5.500 pasos/s (~20M/h).
  Costo de la prueba ≈ $0,40.
- Freno de costos desplegado y probado: con límite de 1 min terminó la instancia real; límite restaurado a 100 min.
- Siguiente: Fase 3b (ajuste fino del tracker con los 55 clips desde el checkpoint preentrenado), medir con la
  batería de MuJoCo antes/después. Mejorar arranque (caché de shaders/compilación en la AMI).

## 2026-11-23 — Corrida 3b fallida, entrenamiento seguro y prueba corta en GPU
- Corrida `2026-11-23-0546` (~$1,10): 47/53 → 0/53 clips. Causas verificadas: tasa del actor de la receta desde
  cero (5e-4 Muon, KL 0,99 en el primer paso), normalización desplazada hacia nuestros 53 clips, evaluación cada
  200 épocas y uso del último checkpoint. (Primer diagnóstico, "falta el crítico", era incorrecto: sí viene.)
- Cambio: `training/train_safe.py` + `training/fase3b_finetune.py` (normalización congelada, calentamiento del
  crítico, tasa 5e-5, freno, mejor checkpoint), `make preflight` ($0) y prueba corta en GPU.
- Prueba corta L4 (~$0,30, 8 min): crítico 1.493 → 624 de error, varianza explicada 0,90 → 0,96, recompensa
  2,5 → 3,46 con el actor congelado (en la fallida bajó a 0,7). Evaluación interna 0,906 → 0,887 con el actor
  congelado = ruido de ±0,02 (el margen del freno de 0,05 lo cubre). No llegó a descongelar el actor (época 9):
  el reloj contaba la compilación y cada evaluación de 53 clips tarda minutos → reloj desde la época 1,
  evaluación cada 20 épocas.
- Decisión: la corrida completa ya está protegida (freno + mejor checkpoint + salida sin mejora, peor caso ≈ $0,55
  sin daño); reactivar el ciclo diario tras el merge.

## 2026-11-24 — Corrida 2026-11-24-0250 y plan de costo/calidad
- **Resultado:** 47 → 49/53 clips al 100% (ganó 124_11 dos pies y 140_03 levantarse), sin pérdidas, jerk 14,9 → 13,6%.
  Evaluación interna 0,906 → 0,925 (época 60). Aprobada con merge (PR 8); review de Brandon: checklist 12/37.
- **Falla de pipeline:** la medición y los clips (CPU) no terminaron antes del apagado forzado de 90 min. Rescatados en la
  Mac en 11 min con `scripts/rescue-run.sh` (ahora `scripts/measure-run.sh`).
- **Dónde se fue el tiempo de GPU (87 min, $1,29):** arranque 13 · entrenamiento puro 19 · evaluaciones internas 17
  (5 × ~200 s) · medición/clips en GPU 36+. Solo 22% fue aprendizaje.
- **`final_inestable` era un artefacto del video:** los clips de carrera duran 1,5–3,7 s y se grababan 8 s; al terminar
  el clip ProtoMotions reinicia el episodio. Ahora el video dura una pasada del clip.
- **Cambios:** la GPU solo entrena (TRAINED) y GitHub Actions mide y graba ($0, `measure-run.yml`); evaluación interna cada
  40 épocas; entrenamiento con `data/cmu_soma_train.pt` (49 clips, sin 104_01/104_37/104_48/127_17, que fallan por datos).
  Estimado: ~$0,65 por corrida (~50 min de GPU) en vez de $1,29.

## 2026-11-24 (tarde) — Tanda 2: más clips para practicar

- **Clips:** de 53 medidos + 0 extra a **88 medidos + 120 solo para entrenar** (CMU, uso libre). Set de GPU `cmu_soma_train_v2.pt`: 208 clips (antes 49).
- **Reemplazos:** los 4 clips rotos (104_01, 104_37, 104_48, 127_17) se cambiaron por clips sanos de las mismas habilidades.
- **Esprint:** sin clips. Las carreras de CMU duran ~1,2 s y no pasan de ~4,5 m/s; un esprint real supera 7 m/s.
- **Medición sin entrenar** (modelo aprobado 2026-11-24-0250, ×5, 43 clips nuevos, 10 min en la Mac):

| Habilidad | Resultado |
|---|---|
| De pie, girar en el sitio, caminar girando, saltar para alcanzar, trote a carrera, correr-parar-correr | Ya lo hacen: 100%, error < 10 cm |
| Trotar | 100%, pero error de 12,5 cm |
| Agacharse | 75% (falla 23_14) |
| Caminar | 75% (falla 16_15, error de 34 cm: revisar el retarget) |
| Correr recto | 75% (falla 127_08) |
| Caer sin dañarse | 50%, error de 18 cm |

- **Determinismo:** con el modelo ajustado, las 5 repeticiones dan siempre el mismo resultado (0 clips mixtos de 96; el error varía ≤ 4 cm). El tracker base tenía 2 clips mixtos de 54.
- **Problema de capacidad:** medir 88 clips ×5 cuesta ~440 evaluaciones (~29 s de CPU cada una). En un runner de 2 núcleos son ~1,5–2 h por corrida, más de lo que dan los 2.000 min/mes gratis de un repo privado. Los cron bajaron de 24 a 5 despertares al día. Falta decidir cómo medir.
