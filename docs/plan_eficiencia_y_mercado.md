# Plan: entrenamiento más eficiente y búsqueda de movimientos preentrenados

Documento vivo (modo explorador y planeador): se revisa cada semana y antes de cada cambio de costo.
Nada de esto está implementado todavía. Cada punto se aprueba por separado.
Última revisión: 2026-11-25.

## 1. Adónde va el dinero de una corrida hoy

Corrida 2026-11-25-1812 en g6.2xlarge spot (L4, ~$0,82/h): ~52 min y ~$0,85 en total.

| Fase | Minutos | % | Qué es |
|---|---|---|---|
| Arranque de la instancia | ~7 | 13% | boot, bajar código, set de clips (160 MB) y checkpoint aprobado (320 MB) |
| Arranque de Isaac Sim / Lab | ~13 | 25% | Kit, conversión MJCF→USD, malla del terreno, compilación de Warp y torch |
| Evaluaciones internas | ~10 | 19% | 3 × ~3,3 min, cada una sobre los 208 clips |
| **Entrenamiento real** | **~22** | **42%** | ~120 épocas × ~11 s |

Solo el 42% de lo que se paga es aprendizaje. Esa es la palanca principal, antes de buscar una GPU más barata.

## 2. Palancas de eficiencia, ordenadas por ahorro estimado

| # | Palanca | Ahorro estimado | Costo de probarla | Riesgo |
|---|---|---|---|---|
| E1 | **Cachés en la AMI**: USD convertido, kernels de Warp, caché de Kit y de torch inductor (y el set de clips) | 13 → ~3-4 min de arranque: −~10 min/corrida, ~−17% (~$0,14) | Reconstruir la AMI (~$0,50 una vez); el snapshot crece poco | Bajo: si la caché no sirve, se recompila como hoy |
| E2 | **GPU por precio/rendimiento**: medir épocas/hora en g4dn.2xlarge (T4, ~$0,25-0,29 spot) y g6.xlarge (L4 con 4 vCPU, ~$0,56-0,72) contra g6.2xlarge (~$0,70-0,83) | Si la T4 rinde más de ~35% de la L4, sale más barata por época: hasta −50-60% | `scripts/remote/gpu-bench.sh`, ~$0,15 por tipo | Medio: Isaac Sim 6 en T4 no está verificado |
| E3 | **Subred en us-east-1f**: hoy la g6.2xlarge spot cuesta $0,70 ahí, contra $0,81-0,83 en las otras zonas, y hay una zona más para conseguir capacidad (hoy fallaron todas) | ~−15% por hora y menos días sin corrida | $0 (Terraform, con tu aprobación) | Bajo |
| E4 | **Evaluaciones internas más baratas**: cada 60 épocas en vez de 40, o solo sobre los 88 clips medidos | −3 a −5 min/corrida (~−8%) | $0 | Bajo: la puerta real es measure-run en MuJoCo |
| E5 | **Que cada época enseñe más**: muestrear más los clips que fallan (ProtoMotions ya lo hace con `motion_weights_rules`; verificar que siga activo en el ajuste fino); revisar tasa de aprendizaje y épocas de calentamiento con los datos del nuevo puntaje | Más avance por dólar, no menos dólares | $0 de código; se mide en las corridas diarias | Medio |
| E6 | **Corridas más largas, menos seguido**: el arranque fijo (~20 min) se paga una vez por cada 70 min de entrenamiento en lugar de 35 | −~15% por minuto entrenado | $0 | Hay que respetar el tope diario y el freno temprano |

Orden propuesto: E3 y E4 (gratis), después E1 y E2 (una prueba corta de GPU cada una, con tu sí). E5 y E6 se
deciden con los datos que ya guarda el nuevo puntaje (PR 14).

**Regla:** ningún cambio entra sin medir antes y después el costo por corrida y el avance por dólar.
Nada de GPU sin prueba corta, freno temprano y rechazo si empeora.

## 3. Mercado: movimientos y modelos preentrenados para deporte

| Recurso | Qué trae | Licencia y acceso | ¿Nos sirve? |
|---|---|---|---|
| [Soccer-X](https://github.com/Young2647/Soccer-X-Dataset) ([paper](https://arxiv.org/abs/2411.16216)) | Unas 10 h de mocap de fútbol con balón (16 cámaras OptiTrack, 1,08 M frames), en formato SMPL | CC BY-NC-SA 4.0 (no comercial, compartir igual); se pide con un formulario | **El más valioso para las etapas 2 y 3** (patadas, controles, conducción con balón). Necesita: tu aceptación de la licencia, el modelo SMPL (no comercial) y un retargeter SMPL → SOMA. Choca con `docs/licensing.md` ("AMASS/SMPL: no se usan") y con un juego comercial: sirve para prototipo y portafolio, y habría que reemplazarlo antes de vender. **Descartado (2026-11-25)**: el acuerdo solo admite personal de instituciones educativas o de investigación |
| [SoccerBot](https://arxiv.org/abs/2611.06564) (CoRL 2026, [proyecto](https://soccerbot-humanoid.github.io/)) | Receta probada: tracker con Soccer-X (2,5 h filtradas), destilado a un prior latente y una sola política PPO para moverse, conducir, controlar y patear (97% de patadas en sim) | Paper; **sin código, pesos ni datos publicados** | Como receta para la etapa 3: es casi nuestro plan "tracker → prior GPC → habilidades". Confirma el camino, no ahorra entrenamiento |
| [GEAR-SONIC](https://huggingface.co/nvidia/GEAR-SONIC) / [GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl) (NVIDIA, 2026) | Tracker "fundacional" (100 M frames, 9.000 h de GPU): caminar, correr, saltar, gatear | NVIDIA Open Model License; pesos publicados | **No directamente**: es para el robot Unitree G1, no para el cuerpo SOMA. Sirve de referencia de escala |
| [SMPLOlympics](https://www.researchgate.net/publication/381882828_SMPLOlympics_Sports_Environments_for_Physically_Simulated_Humanoids) | Entornos de deporte (incluido fútbol) para humanoides SMPL | Ligado a SMPL | Ideas de recompensas y tareas para la etapa 3 |
| Video → movimiento: [GVHMR](https://zju3dv.github.io/gvhmr), [PromptHMR](https://arxiv.org/abs/2504.06397) | Movimiento 3D desde un video de celular | Revisar licencias (salida en SMPL) | **Para los clips de esprint que faltan**: grabarte o usar video propio. En `docs/licensing.md` "mocap propio (GVHMR)" ya figura como apto para uso comercial; falta confirmar la licencia del código y del modelo |
| BONES-SEED (~142K movimientos) | El dataset con que NVIDIA preentrenó el tracker | Solo académicos o startups < US$1M | Sigue sin usarse (decisión pendiente, ver `docs/licensing.md`) |

**Lo que no existe hoy** (búsqueda del 2026-11-25): un modelo preentrenado de fútbol para el cuerpo SOMA, ni
un dataset de fútbol con licencia comercial y descarga libre. Lo más rápido es Soccer-X, si aceptas el costo de
licencia (no comercial) para la fase de prototipo.

### Cómo se monitorea
Revisión semanal, solo de lectura: papers y releases nuevos (arXiv, Hugging Face, GitHub de NVlabs/ProtoMotions)
sobre trackers, datasets de deporte y video a movimiento. Se agrega una línea a la tabla de arriba con fecha,
licencia y si nos sirve. No se descarga nada sin tu aceptación de la licencia.

## 4. Resultados (2026-11-25)
Brandon decidió: Soccer-X sí, si ayuda y el trámite es fácil; usar las zonas más baratas; hacer las pruebas de GPU si
el balance calidad/costo vale la pena.

- **Soccer-X: descartado por licencia.** El acuerdo (VDI, ShanghaiTech) solo lo puede firmar personal permanente de
  una organización educativa o de investigación; empresas y particulares no califican. Es no comercial, prohíbe
  redistribuir y se pide con un PDF firmado por correo. Brandon no califica. Única vía: escribir a los autores para una
  licencia especial o comercial (sección VIII del acuerdo); decisión de Brandon.
- **E3 hecho.** Subred us-east-1f aplicada (PR #16). La g6.2xlarge spot cuesta ~$0,70 ahí contra ~$0,81-0,82.
- **E2 medido con el pipeline real** (corrida 2026-11-25-2153, preflight de 8 min):

  | Tipo | GPU | s/época | Arranque Isaac | Spot hoy | Resultado |
  |---|---|---|---|---|---|
  | g6.2xlarge (actual) | L4, 8 vCPU, 32 GB | ~11 | ~13 min | $0,70-0,82 | referencia |
  | g6.xlarge | L4, 4 vCPU, 16 GB | ~11 (10 + 1) | ~12 min | $0,56-0,67 | **misma velocidad, ~20 % más barata**; sin falta de memoria |
  | g4dn.2xlarge | T4 | — | — | $0,26-0,28 | sin capacidad spot en 1 h; sin medir |

  Propuesta: la corrida diaria prueba g6.xlarge primero, después g6.2xlarge y g4dn.2xlarge (PR #17). La T4 se vuelve a
  intentar cuando haya capacidad; si rinde más de ~40 % de la L4, sale más barata por época.
- **E1 (caché de arranque): hecho, ahorra poco (PR #18).** No cabe en la AMI: los kernels se compilan en GPU y la AMI se
  construye en CPU. Va en S3 (11 MB por AMI+GPU). Medido en 2 pruebas cortas (2026-11-26, ~$0,60): **~1 min menos por
  corrida** (24 → 23 min), no los ~10 estimados. Compilar no era lo lento. Con las marcas de tiempo nuevas, el arranque
  de ~13 min se reparte así:
  - ~6 s: bajar el código, los datos y el checkpoint.
  - **~5,5 min: Python leyendo el venv (28 GB) desde un disco recién creado del snapshot.** EBS baja los bloques de S3
    la primera vez que se leen (carga perezosa).
  - ~1 min: abrir Isaac Sim.
  - ~4 min: armar la física y la escena de 2048 entornos (no se puede cachear).
  - El resto: compilar (lo que ahora quita la caché).
- **E7 (nuevo, a investigar sin gastar): disco frío.** Es la parte más grande del arranque que todavía se puede atacar.
  Opciones a evaluar en papel antes de cualquier prueba:
  - la tasa de inicialización de volumen de EBS (verificar precio y si aplica a volúmenes de un launch template);
  - leer en paralelo solo los archivos que Python usa al arrancar;
  - adelgazar el venv.
  Fast Snapshot Restore queda descartado: cobra por hora y por zona aunque no haya corridas.

## 5. Decisiones pendientes tuyas
1. ¿Escribir a los autores de Soccer-X para una licencia especial?
2. ¿Hacer merge de PR #17 (g6.xlarge primero)?
3. ¿Hacer merge de PR #18 (caché de arranque, ~1 min menos por corrida)?
4. ¿Investigo E7 (disco frío, ~5 min por corrida) en papel?
