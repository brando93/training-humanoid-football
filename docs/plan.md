# Plan del proyecto — v4 (2026-11-22)

**Prioridad (decidida por Brandon el 2026-11-22):**
1. **Funcionalidad:** un humanoide que sepa jugar con el balón (conducir, controlar, pasar, tirar)
   con **física del balón y del cuerpo lo más realista posible**.
2. **Después**, el realismo visual y la exportación a Unreal Engine 5 para el minijuego.

Mientras tanto, el realismo visual del movimiento no se pule: basta con que el movimiento sea físico y funcional.

**Objetivo final:** un minijuego de fútbol en **Unreal Engine 5**, con un jugador cuyo movimiento sale
de la física (sin animaciones reproducidas) y un balón con física reglamentaria. Un jugador, un balón,
una cancha pequeña, control con gamepad.

Regla general: no se pasa a la siguiente fase o etapa sin la aprobación de Brandon.

## "Saber jugar con el balón" medible
"100%" no es una métrica: se define por niveles con umbrales. Un nivel se da por dominado cuando
cumple su métrica en ≥ 90% de los episodios **en MuJoCo** (la física del juego) con balón y condiciones
aleatorias (masa, presión, césped, posición inicial).

| Nivel | Habilidad | Métrica de dominio |
|---|---|---|
| B0 | Moverse alrededor del balón | Sin pisarlo ni tropezar |
| B1 | Tocar con la zona correcta del pie | Interior / empeine / planta según se pida |
| B2 | Pisar y controlar | Balón bajo control 3 s, sin caer |
| B3 | Parar un balón que llega (primer control) | Queda a < 1 m del pie |
| B4 | Empujar con toques cortos | Dirección < 15° |
| B5 | Patear balón quieto, dirección y fuerza variables | Dirección < 10°, velocidad ±15% |
| B6 | Conducir caminando y trotando | 20 m sin perderlo, cambios de dirección |
| B7 | Recibir y pasar | Pase a < 1 m del objetivo |
| B8 | Tiro a portería | Dentro del arco y fuerza pedida |
| B9 | Secuencia: conducir → controlar → tirar | Jugada completa sin intervención |

## Física del balón "hiperrealista" (Fase F, en el Mac)
Lo que la mayoría de los motores no trae y hay que modelar explícitamente, igual en entrenamiento y en el juego:
- Masa 0,41–0,45 kg, circunferencia 68–70 cm (reglamento), presión → rebote (coeficiente de restitución medido).
- **Resistencia al rodar** sobre césped (sin esto rueda casi para siempre).
- **Arrastre aerodinámico** (incluida la "crisis de arrastre" a alta velocidad) y **efecto Magnus** (balón con efecto).
- Contacto pie-balón: fricción y rigidez del contacto calibradas (dirección y giro del balón al golpearlo).
- Cada propiedad con su prueba automática contra valores de referencia publicados (caída, rodado, tiro con y sin efecto).
- En Isaac Lab (PhysX) no hay aerodinámica: las fuerzas de arrastre y Magnus se aplican como fuerzas externas
  con el mismo código en los dos simuladores, para que el balón se comporte igual al entrenar y al jugar.

## Arquitectura del juego (decisión de diseño)

```
Gamepad → Controlador de juego (UE C++)
            │  "corre hacia allá a 6 m/s", "pasa al punto X con fuerza Y"
            ▼
       Política de tarea (ONNX, vía NNE de Unreal)      ← entrenada con RL en AWS
            ▼
       Tracker / prior de movimiento (ONNX)             ← preentrenado (Anatomical SOMA + GPC)
            ▼  objetivos PD de cada articulación, 30–60 Hz
       MuJoCo embebido en Unreal (plugin C++ propio)    ← humanoide + balón + cancha
            ▼  pose de cada cuerpo, cada frame
       Skeletal mesh (MetaHuman/futbolista) retargeteado ← Unreal solo dibuja
            ▼
       Lumen, cámara, sonido, UI
```

- **La física del jugador y del balón corre en MuJoCo, no en Chaos.** Una política entrenada en un
  motor falla en otro (brecha sim-to-sim); usar MuJoCo en el juego y en la validación la evita.
  MuJoCo es Apache-2.0 y una librería en C fácil de embeber. No hay plugin oficial para Unreal:
  lo escribimos (C++ delgado: cargar el MJCF, `mj_step`, leer poses).
- **Unreal se encarga de lo visual:** malla de alta calidad retargeteada al esqueleto simulado,
  iluminación, cámara, estadio, sonido. El resto del mundo (porterías, red, público) puede usar Chaos
  siempre que no toque al jugador ni al balón.
- **Inferencia de la política en Unreal con NNE (ONNX).** Un personaje a 30–60 Hz cabe en CPU.
- **Cuerpo simulado: Anatomical SOMA** (tracker *"verified in MuJoCo"* por ProtoMotions). Plan B: SOMA23.

## Entrenamiento y validación
- **Prior y tracker preentrenados** de ProtoMotions (Isaac Lab), adaptados con GPC (PEFT: prior → SFT → RLFT con PPO).
- **Entrenamiento de tareas** en Isaac Lab en AWS (GPU spot). Opción a evaluar en la Fase 2: el backend
  Newton de ProtoMotions, cuya física es más cercana a MuJoCo, para reducir la brecha con el juego.
- **Compuerta de MuJoCo:** ninguna política se da por buena hasta que pasa la misma batería de
  pruebas en MuJoCo (lo que correrá en Unreal). Se automatiza en el reporte diario.
- **Balón idéntico en ambos lados:** mismos parámetros y mismas pruebas de calibración (caída, rodado, golpe).

## Fases

| Fase | Contenido | Éxito | Dónde | Estado |
|---|---|---|---|---|
| 0. Fundamentos | MuJoCo + Gymnasium + SB3 (opcional, solo para aprender) | — | Mac | Opcional, en pausa |
| 1. Infraestructura | Etapas I1–I13 (abajo) | Corrida diaria autónoma con reporte | AWS | I1–I4 ✅, I7 parcial (freno) |
| 2. Modelo preentrenado | Anatomical SOMA tracker en MuJoCo | Sigue clips sin caer | Mac | ✅ 10/10 clips |
| **3a. ¿El cuerpo puede hacerlo?** | Batería de funciones básicas del futbolista (abajo): el tracker imita clips de cada habilidad en MuJoCo | ≥ 90% de los clips de cada habilidad sin caídas, error de posición < 10 cm | Mac, $0 | ✅ Puede hacerlas todas; fiabilidad < 90% en carrera rápida, un pie y levantarse (ver `docs/reports/battery_3a.md`) |
| **3b. Hacerlo cuando se le pide** | Interfaz de comandos: velocidad y dirección (steering con el prior GPC), parar, girar, saltar, patear al aire | Cumple cada comando con tolerancia (abajo) en 90% de los episodios | AWS (GPU) | Espera cuota |
| **3c. Robustez** | Empujones, transiciones entre habilidades, levantarse | Sin caídas ante empujones moderados; se levanta en < 3 s | AWS + compuerta Mac | |
| F. Física del balón | Balón y cancha calibrados (rebote, rodado, arrastre, Magnus, contacto pie-balón) | Pruebas de física dentro de tolerancia | Mac, $0 | Después de la Fase 3 |
| 4. Balón B0–B5 | Moverse cerca, tocar, pisar, parar, empujar, patear | Métrica por nivel en MuJoCo | AWS + compuerta Mac | |
| 5. Balón B6–B9 | Conducir, pasar, tirar, jugada completa | Métrica por nivel en MuJoCo | AWS + compuerta Mac | |
| 6. Runtime en Unreal | Plugin MuJoCo en UE5, políticas ONNX vía NNE | Jugador + balón comandados en vivo a ≥ 60 fps | Mac | |
| 7. Realismo y vertical slice | Clips propios, pulido de estilo, MetaHuman, cancha, gamepad | Partida jugable de 2 min | Mac + AWS | |
| 8. Pulido y empaquetado | Rendimiento, build, trailer | Build en otra máquina | Mac | |
| 9. Futuro | Licencias comerciales, más jugadores, portero | Proyecto aparte | — | |

### Funciones básicas del futbolista (Fase 3)

Estado al día, con checks calculados desde las mediciones: [checklist de habilidades](checklist_habilidades.md).
Orden (Brandon, 2026-11-22): **etapa 1** moverse como un humano de forma natural con acciones básicas →
**etapa 2** movimiento atlético para el fútbol (sin balón) → **etapa 3** balón. Un check exige "lo hace" **y** "natural".

#### Naturalidad (criterio del check, evaluador en construcción)
Se mide en MuJoCo sobre la simulación, comparando con el humano real del mismo clip:
| Métrica | Qué detecta | Vara |
|---|---|---|
| Pies que patinan en contacto (cm/s) | Deslizamiento irreal | Cerca del humano real |
| Suavidad (jerk normalizado, sim vs. referencia) | Temblor o movimientos robóticos | ≤ referencia + margen |
| Fuerzas articulares (% del tiempo en el límite del motor) | Movimientos "a fuerza bruta" | Rara vez en saturación |
| Fuerza de reacción del suelo (× peso corporal) | Pisadas y aterrizajes irreales | Rangos humanos (caminar ~1,2×, correr ~2–3×) |
| Nota visual de Brandon (1–5) sobre video | Lo que las métricas no ven | ≥ 4 |

Hallazgo 2026-11-22: el jerk solo no basta. Los clips de referencia ya tienen ~20% de ventanas con jerk alto
(hasta 67% en carrera, por ruido del mocap y del retargeting), y la simulación da menos jerk cuando falla pronto.
Por eso la naturalidad combina varias métricas (`retarget/reference_jerk.py` da la referencia de jerk).
Orden de prioridad para el fútbol. **Ya probado en MuJoCo (2026-11-22, clips de ejemplo, 10/10):** caminar,
trotar con giro de 180°, trotar hacia atrás y frenar, salto vertical, salto lateral, caer y levantarse,
agacharse, girar en el lugar.

| Grupo | Habilidades | Comando (3b) y tolerancia |
|---|---|---|
| Postura | De pie estable, postura atlética (rodillas flexionadas) | Mantener 30 s sin caer |
| Locomoción | Caminar, trotar, correr, **sprint** | Velocidad pedida ±10% |
| Cambios de ritmo | Arrancar, **acelerar**, **frenar en seco** | 0 → 5 m/s en < 2 s; frenar de 5 m/s en < 1,5 m |
| Cambios de dirección | Girar en el lugar, girar corriendo, **cortes de 45°/90°**, media vuelta | Rumbo pedido ±10° |
| Desplazamientos | Lateral (*shuffle*), hacia atrás (*backpedal*), pasos cruzados | Velocidad y dirección ±15% |
| Equilibrio | Un pie, **balanceo de pierna** (patada al aire), recuperar ante empujón | Sin caer |
| Salto | Vertical (cabezazo), con carrera, aterrizaje estable | Aterriza sin caer en 95% |
| Suelo | Caer de forma segura y **levantarse** | De pie en < 3 s |

### Habilidades motoras (lista original, referencia)
- Postura: de pie, recuperar equilibrio ante empujones.
- Extremidades: poses objetivo, flexionar/extender, a distintas velocidades.
- Equilibrio dinámico: pasar el peso, un pie, levantar el pie a distintas alturas y velocidades.
- Cuerpo completo: sentadilla, brinco vertical y hacia adelante, aterrizaje estable.
- Locomoción: caminar/correr a varias velocidades, lateral, hacia atrás, frenar, girar a distintas velocidades.
- Robustez: levantarse tras caer, transiciones suaves, terreno irregular.
- Pre-fútbol: patada al aire en un pie, cambios de dirección bruscos, frenar y arrancar, postura de futbolista.

### Escalera con balón (fases 4–5)
Ver la tabla "Saber jugar con el balón medible" (B0–B9) y la Fase F para la física del balón.

### Métricas de "se siente como juego"
- Latencia de control: del botón al primer cambio visible < 100 ms.
- Respuesta: tiempo de 0 a sprint, radio de giro a velocidad, tiempo de frenado.
- Robustez jugable: caídas por minuto de juego ≈ 0 salvo contacto o tropiezo justificado.
- Rendimiento: física + 2 inferencias ONNX < 4 ms por frame en el Mac M3 Pro.

## Licencias (ver detalle en `docs/licensing.md` cuando exista)
- Código: ProtoMotions, MuJoCo, SOMA-X → Apache-2.0. Unreal Engine: gratis hasta US$1M de ingresos, luego 5%.
- Checkpoints de NVIDIA → NVIDIA Open Model License (parece permitir uso comercial con aviso y guardrails; **verificar el texto completo**).
- BONES-SEED → licencia propia, uso comercial **no confirmado** (Bones vende licencias comerciales).
- Mocap propio (GVHMR) → nuestro. Es la ruta segura para un juego comercial.
- Prototipo y portafolio: todo sirve. Antes de vender algo: licencia comercial de Bones o reentrenar con mocap propio.

## Etapas de infraestructura

| Etapa | Contenido | Estado |
|---|---|---|
| I1 | Cuenta y seguridad: SSO, Budgets, CloudTrail, cuotas GPU, SES | ✅ (cuotas y SES pendientes de terceros) |
| I2 | GitHub: repo, gitleaks, alerta de push a main, OIDC | ✅ |
| I3 | Terraform base: VPC sin NAT, S3, IAM (launch template pasa a I4) | ✅ |
| I4 | AMI con Packer (driver NVIDIA, Isaac Lab fijado, ProtoMotions, MuJoCo) + launch template | ✅ AMI `ami-04f81edc1c266cea8` (snapshot 106,6 GB ≈ $5,33/mes); launch template `humanoid-trainer` (spot one-time, terminar al apagar, apagado forzado 90 min, disco cifrado que se borra); `scripts/launch-trainer.sh` prueba zonas por precio. Prueba L4: ~5.500 pasos/s con 2048 entornos, arranque ~13 min |
| I5 | Job diario: launcher, scheduler, ledger, timeout duro | ✅ `daily-train.yml` (10:07 CST, se salta si hay review pendiente) + `train-3b.sh` + `launch-trainer.sh --run`; ledger en el freno de costos |
| I6 | Reporte: HTML, gráficas, video, SES; incluye la compuerta de MuJoCo | ✅ como PR: `make_run_report.py` (GIF por habilidad en la rama `media`, checklist, comparación con el aprobado, costo); medición MuJoCo ×5 en la instancia. Sin SES por ahora (el PR notifica) |
| I7 | Guardrails: Budget Action, sweeper, prueba de sobregasto | Freno ✅ `humanoid-cost-guard` (Lambda cada 10 min: corrida > 100 min, GPU/día > $3 o factura ≥ $45 → termina GPU y bloquea el lanzador); probado terminando una instancia real. Falta: aviso por correo al frenar |
| I8 | Semana de prueba y conciliación de costos | |
| I9 | Issue diario en GitHub | ✅ reemplazado por un PR por corrida (`run-pr.yml`): review con nota de naturalidad 1–5 (`apply-review.yml`) y merge = modelo aprobado (`promote-run.yml`) |
| I10 | Claude analista (Bedrock + OIDC) | |
| I11 | Claude ejecutor (`@claude` → PR) | |
| I12 | Gestor semanal y evals de prompts | |
| I13 | Claude Code local con Bedrock + SSO | |

## Estructura del repo (con Unreal)
- `unreal/` — proyecto UE5 (se agrega en la Fase 2.5). Los assets binarios pesados van con Git LFS o fuera del repo.
- `unreal/Plugins/MuJoCoRuntime/` — plugin C++: MuJoCo embebido + puente con NNE.
- `export/` — exportar políticas a ONNX y el MJCF del jugador y la cancha para Unreal.

## Pendientes externos
- Cuotas de GPU familia G (8 vCPU on-demand y spot): casos de soporte abiertos con AWS.
- Verificación del email en SES (clic en el correo de AWS).
- Aceptación de la EULA de Isaac Sim por Brandon (`docs/licensing.md`).
- Revisión de la NVIDIA Open Model License y de la licencia de BONES-SEED antes de cualquier uso comercial.

## Lecciones técnicas registradas
- OIDC: el repo usa subjects inmutables de GitHub (`repo:brando93@45773752/training-humanoid-football@1467320856:...`);
  todo rol nuevo debe confiar en ese prefijo.
- Isaac Lab en el commit fijado: la raíz es un proyecto uv con `package = false`. `uv pip install -e .` falla
  y `uv sync` no resuelve (choque con el extra `teleop`). Se instala con `uv pip install -r pyproject.toml --extra isaacsim`.
- ProtoMotions choca con los pines de Isaac Sim (p. ej. `numpy==2.3.1`): se instala con `--overrides`
  de las versiones que dejó Isaac Lab, igual que hace Isaac Lab.
- Compuerta de MuJoCo en el Mac (2026-11-22): tracker Anatomical SOMA 10/10 clips sin caídas, error medio 4,5 cm (`make soma-mujoco-eval`).
- Entorno local: uno solo (Python 3.12) para la Fase 0 y ProtoMotions con MuJoCo; descargas pesadas de a una y visibles.
- torch queda en CUDA 13 (`cu130`): necesita driver NVIDIA 580 o posterior (la AMI trae 620.70.06).
- El primer snapshot de la AMI (~107 GB) tardó ~40 min: Packer necesita `aws_polling` con más intentos.
- El snapshot es completo (no incremental) porque parte de una AMI de AWS: cada AMI que conservemos cuesta ~$5/mes.

## Decisión: repo privado sin protección de rama (2026-11-22)
GitHub Free no ofrece protección de rama ni push protection en repos privados. Se aceptó quedarse
privado sin pagar GitHub Pro. Controles que compensan:
- gitleaks en pre-commit local y en CI sobre todo el historial.
- `guard-main.yml`: abre un issue si alguien distinto de brando93 hace push a `main`.
- En I11, el workflow de Claude solo trabaja en ramas `claude/*`, con `@claude` limitado a brando93.
- Si el repo se hace público o se pasa a Pro, activar protección de `main` y push protection.

## Presupuesto (tope $50/mes)

| Concepto | Costo al mes |
|---|---|
| GPU spot | ~$29 |
| Infraestructura (snapshot de la AMI ~$5,33 medido, S3, disco e IP temporales) | ~$8 |
| Claude en Bedrock | ~$6–8 |
| Margen | ~$5 |

**Precios spot reales en us-east-1 (medidos el 2026-11-22, mediana de 24 h):**

| Instancia | GPU | RAM | $/h | Horas con $29 |
|---|---|---|---|---|
| g6.2xlarge | L4 24 GB | 32 GB | ~0,75 | ~39 h/mes (~1,3 h/día) |
| g4dn.2xlarge | T4 16 GB | 32 GB | ~0,26 | ~110 h/mes (~3,7 h/día) |
| g6.xlarge | L4 24 GB | 16 GB | ~0,60 | RAM probablemente insuficiente para Isaac Sim |

Decisión pendiente para la Fase 2: benchmark de **pasos de entrenamiento por dólar** en g4dn.2xlarge
vs g6.2xlarge (no está confirmado que Isaac Sim 6 funcione bien en T4). La AMI sirve para ambas.
El launcher calcula cada día las horas según el presupuesto restante, así que el tope se respeta
con cualquier tipo de instancia.

Reglas de costo: estimar antes y verificar después de cada cambio en AWS; para chequeos de rutina
usar la API de Budgets (gratis), no Cost Explorer ($0,01 por consulta). Todo lo de Unreal corre en el Mac: $0.

## Horario
Entrenamiento a las 10:00 de Costa Rica (16:00 UTC). Issue con el reporte hacia las 12:30.
Modelos: Sonnet 5.5 para el análisis diario; Opus 5.5 para PRs y revisión semanal.
