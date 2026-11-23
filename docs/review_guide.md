# Guía de review de una corrida

Cada corrida de entrenamiento llega como un PR con un clip por habilidad: **izquierda = modelo aprobado,
derecha = modelo nuevo**. Tu review no califica acciones sueltas: corrige las reglas con las que el modelo se
entrena (datos y recompensa) y decide qué modelo pasa a ser el oficial.

## Qué poner por habilidad
```yaml
naturalidad:
  arrancar: {nota: 3, vs_anterior: mejor, defectos: [final_inestable]}
```
- **nota (1–5):** naturalidad absoluta. 5 indistinguible de una persona · 4 natural con detalles menores ·
  3 se nota artificial · 2 robótico o raro · 1 antinatural. **≥ 4 cuenta como "natural"** en el checklist.
- **vs_anterior:** `mejor`, `igual` o `peor` frente al modelo aprobado (izquierda). Es lo más fiable: comparar
  es más fácil que calificar en absoluto.
- **defectos:** etiquetas de lo que se ve mal (puedes poner varias). Deja vacío lo que no quieras calificar.

## Etiquetas y qué ajuste disparan
| Etiqueta | Qué se ve | Qué se ajusta |
|---|---|---|
| `patina` | Los pies se deslizan apoyados | Penalizar deslizamiento en contacto; revisar contactos del clip |
| `rigido` | Robótico, poco fluido, brazos o tronco tiesos | Más peso a seguir rotaciones; menos castigo a la amplitud |
| `brusco` | Tirones, movimientos espasmódicos | Más peso a la suavidad de acciones; revisar ruido del clip |
| `se_cae` | Pierde el equilibrio o se cae | Clip (¿es físicamente posible?), terminación, entrenamiento de equilibrio |
| `final_inestable` | Al terminar el clip queda a punto de caer | Recortar o extender el final del clip para que acabe en una postura estable |
| `postura_rara` | Ángulos o posturas que una persona no haría | Retargeting (cinemática inversa) y límites articulares |
| `brazos_raros` | Brazos fuera de lugar | Pesos de brazos en el retargeting y la recompensa |
| `falla` | No completa el movimiento | Datos: cambiar o arreglar el clip |
| `otro` | Algo distinto | Explícalo en `comentarios` |

## Decisión
- **Merge:** el modelo nuevo pasa a ser el aprobado y la siguiente corrida parte de él.
- **Cerrar sin merge:** se descarta; la siguiente corrida vuelve a partir del aprobado.

Antes de llegar a ti, una corrida ya pasó tres filtros automáticos:
1. **Sin mejora en la evaluación interna:** no se mide ni se graba, y no hay PR.
2. **Empeora durante el entrenamiento:** se detiene sola y se queda con su mejor punto.
3. **Pierde alguna habilidad que el aprobado ya hacía:** llega marcada **⛔ rechazada** y cerrada. No hace falta revisarla.
