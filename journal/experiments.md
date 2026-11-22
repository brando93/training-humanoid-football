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
