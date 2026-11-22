# Changelog de prompts

Cada cambio a un prompt se registra aquí: qué cambió, por qué y qué evidencia lo respalda.

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
