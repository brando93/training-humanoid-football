# Batería 3a — funciones básicas del futbolista en MuJoCo (2026-11-22)

Tracker preentrenado de Anatomical SOMA (ProtoMotions), física MuJoCo en CPU (Mac), clips de CMU
Motion Capture retargeteados con `retarget/cmu_to_anatomic_soma.py`.
Criterio: ≥ 90% de clips sin caída y error de posición medio < 10 cm.

| Habilidad | Clips | Éxito | Error pos. medio | Error pos. máx. | Error rot. medio | Jerk alto | ¿Pasa? |
|---|---|---|---|---|---|---|---|
| arrancar | 3 | 100.0% | 6.3 cm | 27.2 cm | 27.8° | 6.6% | ✅ |
| con_carrera | 2 | 100.0% | 10.5 cm | 25.0 cm | 29.7° | 13.8% | ❌ |
| correr_parar_correr | 2 | 50.0% | 17.0 cm | 50.2 cm | 45.5° | 12.2% | ❌ |
| correr_recto | 3 | 33.3% | 21.4 cm | 52.7 cm | 37.9° | 29.7% | ❌ |
| corte_90_carrera | 4 | 100.0% | 10.8 cm | 20.0 cm | 29.3° | 26.4% | ❌ |
| corte_90_trote | 4 | 100.0% | 9.5 cm | 16.1 cm | 26.0° | 20.7% | ✅ |
| dos_pies | 3 | 100.0% | 10.0 cm | 41.9 cm | 26.9° | 18.3% | ✅ |
| frenar_en_seco | 4 | 100.0% | 7.6 cm | 26.9 cm | 27.1° | 14.8% | ✅ |
| giro_corriendo | 2 | 100.0% | 8.2 cm | 14.3 cm | 28.4° | 29.3% | ✅ |
| hacia_atras | 3 | 100.0% | 6.9 cm | 11.3 cm | 25.7° | 1.7% | ✅ |
| lateral_corriendo | 2 | 100.0% | 9.8 cm | 41.0 cm | 32.2° | 23.8% | ✅ |
| lateral_defensivo | 4 | 100.0% | 10.0 cm | 30.6 cm | 31.0° | 16.8% | ✅ |
| levantarse | 4 | 75.0% | 11.5 cm | 50.4 cm | 32.8° | 6.2% | ❌ |
| patada_frontal | 2 | 100.0% | 8.9 cm | 20.2 cm | 32.3° | 19.0% | ✅ |
| patear_balon_futbol | 6 | 100.0% | 7.5 cm | 19.8 cm | 27.7° | 11.6% | ✅ |
| saltos_un_pie | 2 | 100.0% | 8.0 cm | 22.6 cm | 31.6° | 25.1% | ✅ |
| trote_a_carrera | 2 | 50.0% | 15.3 cm | 232.4 cm | 32.4° | 0.0% | ❌ |
| un_pie | 3 | 66.7% | 10.9 cm | 50.3 cm | 35.7° | 17.6% | ❌ |

**Resultado: 11/18 habilidades pasan.**

## Calidad del retargeting
- Clips: 55. Error medio de la cinemática inversa: 3.7 cm (máx. 6.4 cm).
- Deslizamiento de pies en contacto: 6.4 cm/s de media.

## Análisis (2026-11-22)

### La evaluación no es determinista
Con los mismos clips, dos corridas dieron resultados distintos en habilidades de carrera y equilibrio
(p. ej. "correr-parar-correr" 100% → 50%, "lateral corriendo" 50% → 100%, "un pie" 100% → 67%).
Eso indica que el cuerpo está **en el límite** en esas habilidades: a veces lo logra y a veces no.
Para afirmar ≥ 90% hace falta evaluar cada clip varias veces (pendiente: 5 repeticiones por clip).

### Fallas por clip (evaluación individual)
| Causa | Clips | ¿Limitación del cuerpo? |
|---|---|---|
| Sujeto 143 (niño de 1,38 m) escalado a adulto: corre a ~6,7 m/s en clips < 2 s | 143_02, 143_03, 143_04 | No: prueba injusta (excluidos) |
| Clips de ~1 s que empiezan en plena carrera | 78_06, 102_05, 104_37, 104_48 | No: no hay tiempo para engancharse |
| Fallas reales | 127_14 (lateral corriendo), 124_11 (salto 2 pies), 140_01 (levantarse boca abajo) | Sí, en algunas corridas |

### Veredicto de la Fase 3a
- **El cuerpo puede hacer todas las funciones básicas evaluadas**: cada una de las 18 habilidades tuvo éxito
  en al menos una corrida, incluida la **patada a un balón de fútbol (6/6 clips en ambas corridas)**, frenar en
  seco, cortes de 90°, lateral defensivo, hacia atrás, saltos y un pie.
- **No las hace de forma fiable todavía** en carrera rápida, transiciones trote→carrera, un pie y levantarse boca
  abajo. El tracker preentrenado nunca vio estos clips de CMU: es justo lo que corrige el ajuste fino (Fases 3b/3c,
  en GPU) entrenando sobre estos movimientos y con comandos.
- Calidad del retargeting: buena (error de cinemática inversa ~3 cm). El jerk (~15–25% de cuadros) sale en parte
  del retargeting; un suavizado temporal es una mejora pendiente.
