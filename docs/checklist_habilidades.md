# Checklist de habilidades del futbolista

Última medición: **Tracker NVIDIA preentrenado, sin ajuste** (2026-11-22), archivo `data/cmu_motions/repeat_baseline_v0.json`.
**Nivel 1 logrado: 9 de 36 habilidades.**

Los checks los calcula `retarget/update_checklist.py`; no se editan a mano.

- **Nivel 1, puede hacerlo:** imita sus clips de mocap en MuJoCo con **100% de éxito en todas las corridas** (al menos 5 por clip) y error de posición medio < 10 cm.
- **Nivel 2, cuando se pide:** lo hace ante una orden (dirección, velocidad, momento). Fase 3c.
- **Nivel 3, robusto:** lo mantiene con empujones y variantes. Fase 3c.
- ✅ logrado · 🟡 a veces · ❌ nunca · ⬜ sin prueba todavía. Formato: éxito · error medio.

## Cuerpo (Fase 3)

| | Habilidad | Nivel 1: puede hacerlo | Nivel 2: cuando se pide | Nivel 3: robusto | Detalle |
|---|---|---|---|---|---|
| | **Postura y equilibrio** | | | | |
| ⬜ | Estar de pie y mantener el equilibrio | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| 🟡 | Equilibrio en un pie | 🟡 100% · 10.7 cm | ⬜ | ⬜ | error ≥ 10 cm |
| ✅ | Saltos en un pie | ✅ 100% · 8.0 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| | **Locomoción** | | | | |
| ⬜ | Caminar | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| ⬜ | Trotar | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| 🟡 | Correr recto | 🟡 33% · 11.1 cm | ⬜ | ⬜ | falla: 104_37 (0/5), 104_48 (0/5); error ≥ 10 cm |
| ⬜ | Esprintar | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| ❌ | Pasar de trote a carrera | ❌ 0% · — | ⬜ | ⬜ | falla: 104_01 (0/5) |
| | **Cambios de ritmo** | | | | |
| ✅ | Arrancar desde quieto | ✅ 100% · 6.0 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| ✅ | Frenar en seco | ✅ 100% · 7.6 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| 🟡 | Correr, parar y volver a correr | 🟡 50% · 8.8 cm | ⬜ | ⬜ | falla: 127_17 (0/5) |
| | **Cambios de dirección** | | | | |
| ⬜ | Girar en el sitio (pivote) | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| ✅ | Corte de 90° trotando | ✅ 100% · 9.4 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| 🟡 | Corte de 90° corriendo | 🟡 100% · 10.8 cm | ⬜ | ⬜ | error ≥ 10 cm |
| ✅ | Giro corriendo | ✅ 100% · 8.2 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| | **Desplazamientos** | | | | |
| ✅ | Desplazamiento lateral defensivo | ✅ 100% · 10.0 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| ✅ | Lateral corriendo | ✅ 100% · 9.8 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| ✅ | Hacia atrás | ✅ 100% · 6.8 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| | **Salto** | | | | |
| 🟡 | Salto con dos pies | 🟡 73% · 10.3 cm | ⬜ | ⬜ | falla: 124_11 (1/5); error ≥ 10 cm |
| 🟡 | Salto con carrera | 🟡 100% · 10.5 cm | ⬜ | ⬜ | error ≥ 10 cm |
| ⬜ | Saltar para cabecear | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |
| | **Patada (sin balón)** | | | | |
| ✅ | Gesto de patada de fútbol | ✅ 100% · 7.3 cm | ⬜ | ⬜ | check desde 2026-11-22 |
| 🟡 | Patada frontal | 🟡 80% · 8.2 cm | ⬜ | ⬜ | falla: 144_05 (3/5) |
| | **Suelo** | | | | |
| 🟡 | Levantarse del suelo | 🟡 75% · 9.5 cm | ⬜ | ⬜ | falla: 140_03 (0/5) |
| ⬜ | Caer sin dañarse y recuperarse | ⬜ sin prueba | ⬜ | ⬜ | Faltan clips o métrica |

## Con balón (Fases F, 4 y 5)

| | Habilidad | Nivel 1: puede hacerlo | Nivel 2: cuando se pide | Nivel 3: robusto | Detalle |
|---|---|---|---|---|---|
| | **Física del balón** | | | | |
| ⬜ | Física del balón validada (rebote, rodamiento, aire, efecto) | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| | **Básicas con balón (B0–B5)** | | | | |
| ⬜ | Moverse alrededor del balón sin pisarlo ni tropezar | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Tocar con la zona del pie que se pide | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Pisar y controlar 3 s sin caer | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Primer control: el balón queda a < 1 m | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Empujar con toques cortos (dirección < 15°) | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Patear balón quieto (dirección < 10°, velocidad ±15%) | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| | **Juego (B6–B9)** | | | | |
| ⬜ | Conducir 20 m caminando y trotando | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Recibir y pasar (a < 1 m del objetivo) | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Tiro a portería con la fuerza pedida | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
| ⬜ | Jugada completa: conducir, controlar, tirar | ⬜ sin prueba | ⬜ | ⬜ | Pendiente de su fase |
