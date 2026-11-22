# Changelog de prompts

Cada cambio a un prompt se registra aquí: qué cambió, por qué y qué evidencia lo respalda.

## 2026-11-22 (v4)
- `project_brief.md` v4: prioridad de Brandon → primero funcionalidad con balón y física realista,
  después realismo visual y Unreal. Nueva Fase F (física del balón) antes de las habilidades con balón;
  Unreal pasa a la Fase 6. Métricas funcionales por nivel (B0–B9) en vez de "100%".
- Evidencia: el tracker preentrenado ya funciona en MuJoCo (10/10 clips), así que el cuello de botella
  es el balón, no el cuerpo.

## 2026-11-22 (v3.1)
- `project_brief.md` v3.1: precios spot reales (g6.2xlarge ~$0,75/h, no ~$0,45) y opción g4dn.2xlarge;
  regla de comprobar siempre el costo; verificar la documentación actual de herramientas externas;
  las licencias las acepta Brandon; sección "Estado actual" que apunta a `docs/plan.md`.
- `CLAUDE.md`: reglas de costo y licencias, datos actualizados (BONES-SEED en lugar de AMASS), comandos de AMI.
- Evidencia: medición de precios spot del 2026-11-22 y los fallos del build de la AMI (ver `docs/plan.md`).

## 2026-11-22 (v3)
- `project_brief.md` v3: el objetivo final pasa a ser un minijuego hiperrealista en Unreal Engine 5.
  Base cambia de SMPL/MaskedMimic (checkpoint ya no publicado, licencia no comercial) a Anatomical SOMA
  + prior GPC. Runtime: MuJoCo embebido en Unreal, políticas ONNX vía NNE, compuerta de validación en
  MuJoCo. Nuevas fases 2.5 (spike de runtime en Unreal) y 7–8 (vertical slice y empaquetado).
- `docs/plan.md` v3 con la arquitectura del juego y las métricas de "se siente como juego".

## 2026-11-22
- `project_brief.md` v2: prompt maestro con base en ProtoMotions, escalera de habilidades motoras y
  con balón, infraestructura AWS autónoma con tope de $50 y ciclo de revisión con Claude.
- `CLAUDE.md` v1: reglas del agente (fases con aprobación, presupuesto, cero secretos, cuenta AWS correcta).
