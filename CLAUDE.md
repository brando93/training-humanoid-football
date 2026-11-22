# CLAUDE.md — instrucciones para el agente del proyecto

## Qué es este proyecto
Un humanoide simulado con física (control por torques/PD, sin animaciones reproducidas) que aprende
habilidades motoras con estilo humano y, después, a interactuar con un balón de fútbol.
Base: ProtoMotions + MaskedMimic preentrenado (humanoide SMPL). Plan completo en `docs/plan.md`;
prompt maestro en `prompts/project_brief.md`.

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
5. **Datos con licencia** (AMASS, SMPL): no comercial y no redistribuible. Nunca se suben al repo.
6. **Un cambio por PR**, con la hipótesis escrita ("cambio X para mover la métrica Y") y la entrada
   correspondiente en `journal/experiments.md`.
7. **No hagas merge, no apliques Terraform y no toques `infra/`, `.github/` ni el presupuesto**
   sin aprobación explícita: esos cambios los revisa Brandon.
8. **Nunca hagas push a `main`.** El repo es privado en GitHub Free y no tiene protección de rama,
   así que esta regla depende de ti: trabaja siempre en una rama `claude/<tema>` y abre un PR.
   Un push a `main` de cualquier autor que no sea brando93 abre un issue de alerta (`guard-main.yml`).

## Prioridad de calidad
El movimiento tiene que verse humano, no robótico ni de muñeco de trapo. Una métrica buena con un
movimiento feo no cuenta como éxito. Métricas de realismo: deslizamiento de pies, jerk articular,
caídas, puntuación del discriminador y la nota de realismo (1–5) que Brandon pone en los issues.

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

## Comandos
- `make login` — sesión SSO
- `make check-account` — verifica la cuenta AWS
- `make scan` — busca secretos con gitleaks
- `make hooks` — instala el pre-commit de gitleaks
