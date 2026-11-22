# Plan del proyecto

Regla general: no se pasa a la siguiente fase o etapa sin la aprobación de Brandon.

## Fases de entrenamiento

| Fase | Contenido | Éxito |
|---|---|---|
| 0. Fundamentos (Mac, gratis) | MuJoCo + Gymnasium + Stable-Baselines3: estar de pie, caminar, ver trampas de recompensa | Humanoide camina 10 s sin caer y se entiende por qué |
| 1. Infraestructura | Etapas I1–I13 (abajo) | Corrida diaria autónoma con reporte |
| 2. Modelo preentrenado | MaskedMimic SMPL corriendo y comandado | Video con ≥ 5 habilidades con física |
| 3. Batería motora | Pruebas automáticas: postura, extremidades, cuerpo completo, locomoción, robustez | Reporte pasa/falla por habilidad |
| 4. Pulido artesanal | Ajuste fino con clips propios (GVHMR) y recompensas | Toda la batería en verde, incluido pre-fútbol |
| 5. Balón B0–B5 | Calibrar el balón; conciencia, tocar, pisar, parar, empujar, patear quieto | Cada nivel cumple su métrica (B5: dirección < 10°, velocidad ±20%, 80%) |
| 6. Conducción y pase B6–B7 | Conducir, recibir y pasar | Abierto (nivel investigación) |
| 7. Demo | Video multiángulo, export FBX a Unreal, ONNX | Video final |
| 8. Futuro | Juego básico en Unreal; datos y esqueleto comerciales | Proyecto aparte |

### Habilidades motoras (batería de la fase 3)
- Postura: de pie, recuperar equilibrio ante empujones.
- Extremidades: poses objetivo, flexionar/extender, a distintas velocidades.
- Equilibrio dinámico: pasar el peso, un pie, levantar el pie a distintas alturas y velocidades.
- Cuerpo completo: sentadilla, brinco vertical y hacia adelante, aterrizaje estable.
- Locomoción: caminar/correr a varias velocidades, lateral, hacia atrás, frenar, girar a distintas velocidades.
- Robustez: levantarse tras caer, transiciones suaves, terreno irregular.
- Pre-fútbol: patada al aire en un pie, cambios de dirección bruscos, frenar y arrancar.

### Escalera con balón (fases 5–6)
B0 moverse cerca sin tropezar · B1 tocar con la zona correcta del pie · B2 pisar y controlar ·
B3 parar un balón que llega · B4 empujar con toques cortos · B5 patear balón quieto ·
B6 conducir · B7 recibir y pasar.
Balón: 0,43 kg, radio 0,11 m; randomización de masa, radio, rebote y fricción; frenado de rodado calibrado.

## Etapas de infraestructura

| Etapa | Contenido | Estado |
|---|---|---|
| I1 | Cuenta y seguridad: SSO, Budgets, CloudTrail, cuotas GPU, SES | ✅ (cuotas y SES pendientes de terceros) |
| I2 | GitHub: repo, gitleaks, alerta de push a main, OIDC | En curso (repo, gitleaks y alerta listos; falta OIDC) |
| I3 | Terraform base: VPC sin NAT, S3, IAM, launch template | |
| I4 | AMI con Packer (driver NVIDIA, Isaac Lab, ProtoMotions) | |
| I5 | Job diario: launcher, scheduler, ledger, timeout duro | |
| I6 | Reporte: HTML, gráficas, video, SES | |
| I7 | Guardrails: Budget Action, sweeper, prueba de sobregasto | |
| I8 | Semana de prueba y conciliación de costos | |
| I9 | Issue diario en GitHub | |
| I10 | Claude analista (Bedrock + OIDC) | |
| I11 | Claude ejecutor (`@claude` → PR) | |
| I12 | Gestor semanal y evals de prompts | |
| I13 | Claude Code local con Bedrock + SSO | |

## Decisión: repo privado sin protección de rama (2026-11-22)
GitHub Free no ofrece protección de rama ni push protection en repos privados. Se aceptó quedarse
privado sin pagar GitHub Pro. Controles que compensan:
- gitleaks en pre-commit local y en CI sobre todo el historial.
- `guard-main.yml`: abre un issue si alguien distinto de brando93 hace push a `main`.
- En I11, el workflow de Claude solo trabaja en ramas `claude/*`, con `@claude` limitado a brando93.
- Si el repo se hace público o se pasa a Pro, activar protección de `main` y push protection.

## Presupuesto (tope $50/mes)
GPU spot g6.2xlarge ~2,1 h/día ≈ $29 · infraestructura ≈ $6 · Claude en Bedrock ≈ $6–8 · margen ≈ $7.

## Horario
Entrenamiento a las 10:00 de Costa Rica (16:00 UTC). Issue con el reporte hacia las 12:30.
Modelos: Sonnet 5.5 para el análisis diario; Opus 5.5 para PRs y revisión semanal.
