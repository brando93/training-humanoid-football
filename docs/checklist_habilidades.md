# Checklist de habilidades del futbolista

Última medición: **Fase 3b: ajuste fino del tracker con clips CMU** (2026-11-23), archivo `reports/runs/2026-11-23-0546/metrics.json`.
**Con check: 0 de 37.** Lo hacen (sin medir aún si es natural): 0.

Orden: primero moverse como un humano de forma natural (etapa 1), luego lo atlético para el fútbol (etapa 2),
luego el balón (etapa 3). Los checks los calcula `retarget/update_checklist.py`; no se editan a mano.

Una habilidad tiene ✅ solo si cumple **las dos** columnas:
- **Lo hace:** imita sus clips en MuJoCo con 100% de éxito en todas las corridas (al menos 5 por clip) y error de posición medio < 10 cm. Formato: éxito · error medio.
- **Natural:** se mueve como un humano real, medido con física: pies que no patinan, suavidad como la del humano real, fuerzas articulares y de contacto en rangos humanos, y la nota visual de Brandon. Hoy cuenta tu nota en el review del PR de cada corrida: ≥ 4/5 = natural. Las métricas físicas se sumarán después.
- Después: **cuando se pide** (responde a órdenes) y **robusto** (aguanta empujones y variantes).
- ✅ logrado · 🟡 a veces · ❌ no · ⬜ sin prueba todavía.

## Etapa 1 — Moverse como un humano, de forma natural

| | Habilidad | Lo hace | Natural | Cuando se pide | Robusto | Detalle |
|---|---|---|---|---|---|---|
| | **Postura y equilibrio** | | | | | |
| ⬜ | Estar de pie quieto, relajado | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ❌ | Equilibrio en un pie | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 49_18 (0/5), 49_19 (0/5), 49_20 (0/5) |
| ⬜ | Agacharse y volver a erguirse | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Caminar** | | | | | |
| ⬜ | Caminar hacia adelante | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ❌ | Caminar hacia atrás | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 111_01 (0/5), 69_34 (0/5), 76_11 (0/5) |
| ❌ | Pasos laterales | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 78_24 (0/5), 78_25 (0/5), 78_26 (0/5), 78_27 (0/5) |
| ⬜ | Girar en el sitio | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ⬜ | Caminar cambiando de dirección | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Correr** | | | | | |
| ⬜ | Trotar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ❌ | Correr | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 104_37 (0/5), 104_48 (0/5), 127_09 (0/5) |
| ❌ | Arrancar desde quieto | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 104_06 (0/5), 104_08 (0/5), 127_04 (0/5) |
| ❌ | Frenar hasta quedar quieto | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 127_05 (0/5), 128_05 (0/5), 16_08 (0/5), 16_57 (0/5) |
| | **Saltar** | | | | | |
| ❌ | Saltar con los dos pies | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 124_11 (0/5), 131_07 (0/5), 143_06 (0/5) |
| | **Suelo** | | | | | |
| ❌ | Levantarse del suelo | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 139_16 (0/5), 139_17 (0/5), 140_01 (0/5), 140_03 (0/5) |
| ⬜ | Caer sin dañarse y recuperarse | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |

## Etapa 2 — Movimiento atlético para el fútbol (sin balón)

| | Habilidad | Lo hace | Natural | Cuando se pide | Robusto | Detalle |
|---|---|---|---|---|---|---|
| | **Velocidad** | | | | | |
| ⬜ | Esprintar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ❌ | Pasar de trote a carrera | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 104_01 (0/5), 127_04 (0/5) |
| ❌ | Correr, parar y volver a correr | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 127_17 (0/5), 127_19 (0/5) |
| | **Agilidad** | | | | | |
| ❌ | Corte de 90° trotando | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 16_41 (0/5), 16_42 (0/5), 16_43 (0/5), 16_44 (0/5) |
| ❌ | Corte de 90° corriendo | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 16_51 (0/5), 16_52 (0/5), 16_53 (0/5), 16_54 (0/5) |
| ❌ | Giro corriendo | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 127_15 (0/5), 127_16 (0/5) |
| ❌ | Desplazamiento lateral rápido | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 127_13 (0/5), 127_14 (0/5) |
| | **Saltos** | | | | | |
| ❌ | Salto con carrera | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 127_21 (0/5), 49_04 (0/5) |
| ❌ | Saltos en un pie | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 132_23 (0/5), 132_24 (0/5) |
| ⬜ | Saltar para cabecear | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Gesto técnico** | | | | | |
| ❌ | Gesto de patada de fútbol (sin balón) | ❌ 0% · — | ⏳ sin nota | ⬜ | ⬜ | falla: 10_01 (0/5), 10_02 (0/5), 10_03 (0/5), 10_05 (0/5), 10_06 (0/5), 11_01 (0/5) |

## Etapa 3 — El balón

| | Habilidad | Lo hace | Natural | Cuando se pide | Robusto | Detalle |
|---|---|---|---|---|---|---|
| | **Física del balón** | | | | | |
| ⬜ | Física del balón validada (rebote, rodamiento, aire, efecto) | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| | **Básicas con balón (B0–B5)** | | | | | |
| ⬜ | Moverse alrededor del balón sin pisarlo ni tropezar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Tocar con la zona del pie que se pide | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Pisar y controlar 3 s sin caer | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Primer control: el balón queda a < 1 m | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Empujar con toques cortos (dirección < 15°) | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Patear balón quieto (dirección < 10°, velocidad ±15%) | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| | **Juego (B6–B9)** | | | | | |
| ⬜ | Conducir 20 m caminando y trotando | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Recibir y pasar (a < 1 m del objetivo) | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Tiro a portería con la fuerza pedida | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
| ⬜ | Jugada completa: conducir, controlar, tirar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Pendiente de su etapa |
