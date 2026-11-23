# CLAUDE.md — instrucciones para el agente del proyecto

## Qué es este proyecto
Objetivo final: un minijuego de fútbol hiperrealista en Unreal Engine 5, con un jugador cuyo
movimiento sale de la física (control por torques/PD, sin animaciones reproducidas) y un balón con
física reglamentaria. Para llegar ahí, el humanoide aprende habilidades motoras y luego a jugar con el balón.
Base: ProtoMotions con Anatomical SOMA + tracker y prior GPC preentrenados. Runtime del juego: MuJoCo
embebido en Unreal y políticas ONNX vía NNE, así que **toda política tiene que funcionar también en MuJoCo**.
Plan completo en `docs/plan.md`; prompt maestro en `prompts/project_brief.md`.

El dueño es Brandon: DevOps que está aprendiendo RL. Escríbele en español, explica los conceptos de RL
de forma breve y práctica cuando aparezcan, y sé honesto si algo no es viable.

## Reglas que no se rompen
1. **Fases con aprobación.** No avances de fase ni cambies el alcance sin que Brandon lo apruebe
   explícitamente en un issue o PR.
2. **Tope de $50/mes en AWS** (incluye GPU, infraestructura y Claude en Bedrock). Nunca propongas
   cambios que suban el gasto sin decir cuánto cuestan y pedir aprobación.
3. **Cero secretos en el repo.** Nada de access keys, tokens ni contraseñas. Los secretos van en
   SSM Parameter Store; el acceso a AWS es por OIDC (Actions) o SSO (local, perfil `humanoid`).
4. **Cuenta AWS correcta.** Solo la cuenta `611606529792`, región `us-east-1`, perfil `humanoid`.
   El Mac tiene perfiles de trabajo: nunca uses `default` ni otro perfil. Corre `make check-account`
   antes de cualquier comando que toque AWS.
5. **Datos y modelos con licencia** (BONES-SEED, checkpoints de NVIDIA; AMASS/SMPL no se usan): nunca
   se suben al repo. Las licencias (EULA de Isaac Sim incluida) las acepta Brandon, nunca el agente.
   Avisa si algo no sirve para un juego comercial (ver `docs/licensing.md`).
9. **Comprueba siempre el costo.** Estima antes y verifica después de cada cambio en AWS. Para
   chequeos de rutina usa `aws budgets describe-budget` (gratis); Cost Explorer cobra $0,01 por consulta.
   Si dejas una AMI nueva, borra las viejas (`make ami-cleanup`).
6. **Un cambio por PR**, con la hipótesis escrita ("cambio X para mover la métrica Y") y la entrada
   correspondiente en `journal/experiments.md`.
7. **No hagas merge, no apliques Terraform y no toques `infra/`, `.github/` ni el presupuesto**
   sin aprobación explícita: esos cambios los revisa Brandon.
8. **Nunca hagas push a `main`.** El repo es privado en GitHub Free y no tiene protección de rama,
   así que esta regla depende de ti: trabaja siempre en una rama `claude/<tema>` y abre un PR.
   Un push a `main` de cualquier autor que no sea brando93 abre un issue de alerta (`guard-main.yml`).

## Prioridad
**Primero funcionalidad con física realista** (que juegue con el balón y que el balón se comporte como uno
real), **después** realismo visual y Unreal. Un nivel de habilidad (B0–B9 en `docs/plan.md`) se da por
dominado con ≥ 90% de éxito en MuJoCo con condiciones aleatorias. Métricas de realismo: deslizamiento de pies, jerk articular,
caídas, puntuación del discriminador y la nota de realismo (1–5) que Brandon pone en los issues.

**Corridas de GPU sin desperdicio (Brandon, 2026-11-23):** ninguna corrida puede terminar peor de lo que empezó.
- Antes de lanzar con cualquier cambio de receta, entrenamiento o modelo de partida: `make preflight` ($0) debe pasar
  y, si el cambio es de fondo, una prueba corta en GPU (`RUN_MODE=preflight`, ~$0,30).
- Toda corrida usa `training/train_safe.py` (normalización congelada, calentamiento del crítico, tasa baja, freno si
  empeora, mejor checkpoint). Sin mejora no se mide ni se graba; si pierde habilidades se rechaza sola.
- Guía de review y etiquetas de defecto: [docs/review_guide.md](docs/review_guide.md).

**Orden de trabajo (Brandon):** primero que se mueva como un humano, natural, con acciones básicas (etapa 1);
luego lo atlético para el fútbol (etapa 2); luego el balón (etapa 3). No saltarse etapas.

**Checklist de habilidades:** [docs/checklist_habilidades.md](docs/checklist_habilidades.md) es el estado oficial de
lo que el humanoide ya sabe hacer. Los checks los calcula `retarget/update_checklist.py` desde una medición
(`make checklist`); nunca se marcan a mano. Un check exige "lo hace" **y** "natural". Tras cada corrida de entrenamiento, actualizarlo y reportar qué
habilidades ganaron o perdieron el check.

## Al analizar un reporte diario
- Compara con los días anteriores, no solo con el de ayer.
- Diagnostica antes de proponer: ¿se cae, patina, está rígido, explota la recompensa?
- Propón como máximo 3 cambios concretos, cada uno con su costo estimado y la métrica que debería mover.
- Si las métricas caen dos días seguidos tras un cambio, propón revertirlo.

## Estructura del repo
- `infra/terraform`, `infra/packer`: infraestructura AWS (requiere aprobación)
- `orchestrator/`: Lambdas (launcher, sweeper, ledger de gasto)
- `jobs/`: script diario en la instancia GPU (entrenar, evaluar, grabar, reportar)
- `configs/`: experimentos en YAML (aquí van la mayoría de los cambios del agente)
- `skills/`: batería de pruebas motoras
- `ball/`: física del balón y tareas B0–B7
- `phase0_basics/`: fundamentos de RL en el Mac (MuJoCo + Stable-Baselines3)
- `prompts/`: prompts versionados (cambios vía PR + `prompts/CHANGELOG.md`)
- `journal/experiments.md`: diario de experimentos
- `docs/`: plan y decisiones

- `infra/terraform/bootstrap`: bucket de estado; `infra/terraform/base`: VPC, S3, IAM, OIDC
- `unreal/` (fase 2.5): proyecto UE5 y plugin MuJoCo; `export/`: ONNX y MJCF para el juego

## Comandos
- `make login` — sesión SSO
- `make check-account` — verifica la cuenta AWS
- `make scan` — busca secretos con gitleaks
- `make hooks` — instala el pre-commit de gitleaks
- `make ami-validate` / `make ami` / `make ami-cleanup` — AMI de entrenamiento con Packer

## Antes de escribir código que dependa de algo externo
Verifica la documentación actual (ProtoMotions, Isaac Lab, MuJoCo, Unreal): ya cambiaron cosas
durante el proyecto. Las lecciones están en `docs/plan.md` → "Lecciones técnicas registradas".
