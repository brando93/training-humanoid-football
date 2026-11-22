# Licencias y aceptaciones

## EULA de NVIDIA Isaac Sim (la acepta Brandon, no el agente)
Isaac Sim pide aceptar su licencia la primera vez que arranca. La AMI **no** la acepta al construirse.

1. Después del primer build de la AMI, el agente extrae el texto de la licencia del paquete instalado
   y te lo muestra (o léelo en la documentación oficial de Isaac Sim).
2. Si estás de acuerdo, guarda tu aceptación (comando para ti, no para el agente):
   ```bash
   aws ssm put-parameter --name /humanoid/isaacsim/eula_accepted --type String --value yes --profile humanoid
   ```
3. `/opt/humanoid/env.sh` en la instancia solo exporta `OMNI_KIT_ACCEPT_EULA=YES` si ese parámetro vale `yes`.
   Para retirar la aceptación: `aws ssm delete-parameter --name /humanoid/isaacsim/eula_accepted --profile humanoid`.

### Qué implica para este proyecto (resumen propio, no sustituye leer el texto)
La licencia de Isaac Sim 6.0.0.1 es el **NVIDIA Omniverse License Agreement** (archivo `isaacsim/LICENSE.txt`
del paquete `isaacsim-kernel`). Puntos que nos afectan:
- Un individuo puede usarlo **también con fines comerciales**, colaborando con como máximo una persona más
  sin comprar licencias de suscripción.
- **No se puede redistribuir** Isaac Sim (ni copias en repositorios públicos). Por eso:
  - la AMI `humanoid-trainer-*` debe quedarse **privada** (nunca compartirla ni hacerla pública);
  - el repo no incluye ningún archivo de Isaac Sim.
- Lo que generamos con él (videos, capturas, modelos y assets propios) sí se puede distribuir. Las políticas
  entrenadas corren en el juego con MuJoCo, **sin Isaac Sim dentro del juego**.
- No se permite hacer ingeniería inversa ni quitar avisos de copyright.

## Componentes y uso en un juego comercial

| Componente | Licencia | ¿Juego comercial? |
|---|---|---|
| ProtoMotions, MuJoCo, SOMA-X (código) | Apache-2.0 | Sí |
| Isaac Lab | BSD-3 (código); Isaac Sim con EULA propia | Solo se usa para entrenar, no va dentro del juego |
| Checkpoints de NVIDIA (tracker, prior GPC) | NVIDIA Open Model License | Parece que sí, con aviso de licencia y guardrails. **Verificar el texto completo** |
| BONES-SEED | Licencia propia de Bones Studio | **Sin confirmar** (Bones vende licencias comerciales) |
| AMASS / SMPL | No comercial | No: no se usan |
| Mocap propio (GVHMR) | Nuestro | Sí |
| Unreal Engine 5 | EULA de Epic | Gratis hasta US$1M de ingresos brutos por producto; luego 5% |

Para prototipo y portafolio todo sirve. Antes de vender: confirmar la NVIDIA Open Model License,
obtener licencia comercial de BONES-SEED o reentrenar con mocap propio.
No es asesoría legal.
