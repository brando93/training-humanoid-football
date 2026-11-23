# Checklist de habilidades del futbolista

Última medición: **Tracker NVIDIA preentrenado, sin ajuste (punto de partida)** (2026-11-22), archivo `reports/runs/2026-11-22-base/metrics.json`.
**Con check: 0 de 37.** Lo hacen (sin medir aún si es natural): 9.

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
| 🟡 | Equilibrio en un pie | 🟡 100% · 10.7 cm | ⏳ sin nota | ⬜ | ⬜ | error ≥ 10 cm |
| ⬜ | Agacharse y volver a erguirse | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Caminar** | | | | | |
| ⬜ | Caminar hacia adelante | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| 🟡 | Caminar hacia atrás | ✅ 100% · 6.8 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| 🟡 | Pasos laterales | ✅ 100% · 10.0 cm | ⏳ sin nota | ⬜ | ⬜ | error ≥ 10 cm; lo hace; falta tu nota de naturalidad |
| ⬜ | Girar en el sitio | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ⬜ | Caminar cambiando de dirección | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Correr** | | | | | |
| ⬜ | Trotar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| 🟡 | Correr | 🟡 33% · 11.1 cm | ⏳ sin nota | ⬜ | ⬜ | falla: 104_37 (0/5), 104_48 (0/5); error ≥ 10 cm |
| 🟡 | Arrancar desde quieto | ✅ 100% · 6.0 cm | ❌ 3/5 | ⬜ | ⬜ | nota del 2026-11-23 (corrida 2026-11-22-base) |
| 🟡 | Frenar hasta quedar quieto | ✅ 100% · 7.6 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| | **Saltar** | | | | | |
| 🟡 | Saltar con los dos pies | 🟡 73% · 10.3 cm | ❌ 2/5 | ⬜ | ⬜ | falla: 124_11 (1/5); error ≥ 10 cm; nota del 2026-11-23 (corrida 2026-11-22-base) |
| | **Suelo** | | | | | |
| 🟡 | Levantarse del suelo | 🟡 75% · 9.5 cm | ❌ 3/5 | ⬜ | ⬜ | falla: 140_03 (0/5); nota del 2026-11-23 (corrida 2026-11-22-base) |
| ⬜ | Caer sin dañarse y recuperarse | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |

## Etapa 2 — Movimiento atlético para el fútbol (sin balón)

| | Habilidad | Lo hace | Natural | Cuando se pide | Robusto | Detalle |
|---|---|---|---|---|---|---|
| | **Velocidad** | | | | | |
| ⬜ | Esprintar | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| ❌ | Pasar de trote a carrera | ❌ 0% · — | ❌ 1/5 | ⬜ | ⬜ | falla: 104_01 (0/5); nota del 2026-11-23 (corrida 2026-11-22-base) |
| 🟡 | Correr, parar y volver a correr | 🟡 50% · 8.8 cm | ❌ 3/5 | ⬜ | ⬜ | falla: 127_17 (0/5); nota del 2026-11-23 (corrida 2026-11-22-base) |
| | **Agilidad** | | | | | |
| 🟡 | Corte de 90° trotando | ✅ 100% · 9.4 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| 🟡 | Corte de 90° corriendo | 🟡 100% · 10.8 cm | ⏳ sin nota | ⬜ | ⬜ | error ≥ 10 cm |
| 🟡 | Giro corriendo | ✅ 100% · 8.2 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| 🟡 | Desplazamiento lateral rápido | ✅ 100% · 9.8 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| | **Saltos** | | | | | |
| 🟡 | Salto con carrera | 🟡 100% · 10.5 cm | ⏳ sin nota | ⬜ | ⬜ | error ≥ 10 cm |
| 🟡 | Saltos en un pie | ✅ 100% · 8.0 cm | ⏳ sin nota | ⬜ | ⬜ | lo hace; falta tu nota de naturalidad |
| ⬜ | Saltar para cabecear | ⬜ sin prueba | ⬜ | ⬜ | ⬜ | Faltan clips |
| | **Gesto técnico** | | | | | |
| 🟡 | Gesto de patada de fútbol (sin balón) | ✅ 100% · 7.3 cm | ❌ 2/5 | ⬜ | ⬜ | nota del 2026-11-23 (corrida 2026-11-22-base) |

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
