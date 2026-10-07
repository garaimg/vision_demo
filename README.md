# Práctica 1: Selección de regiones en vídeo

## Uso

```
python practica1.py
```

Primero se etiqueta el vídeo `video_perro.mp4` frame a frame. Al pulsar `Q` (o al llegar al final) se generan todos los vídeos de salida.

## Controles

| Control | Acción |
|---|---|
| Clic izquierdo | Añadir un punto a la región actual |
| Arrastrar | Dibujar el contorno a mano alzada |
| Arrastrar sobre un vértice | Mover ese vértice (modificar una región) |
| Clic derecho dentro de una región | Eliminar la región |
| `C` | Cerrar la región actual |
| `Z` | Deshacer el último punto |
| `ESPACIO` | Siguiente frame (mantiene las regiones) |
| `A` | Saltar 10 frames; los intermedios se interpolan |
| `Q` | Terminar el etiquetado y generar los vídeos |

## Salida

- `salida_regiones.avi`: vídeo original con las regiones dibujadas.
- `salida_oculta.avi`: vídeo original con las regiones rellenas de negro.
- `region_N_rect.avi`: recorte del rectángulo mínimo que delimita la región N.
- `region_N_forma.avi`: recorte de la región N con solo su contenido (fuera de la región, negro).

## Extras implementados

- **Extracción de regiones:** un vídeo por región con el recorte de su rectángulo mínimo (mínimos y máximos de X e Y de sus puntos).
- **Ocultación de regiones:** las regiones se rellenan de negro siguiendo su forma exacta.
- **Reducción del etiquetado manual:** las regiones se mantienen al pasar de frame. Con `A` se salta a un frame posterior, se ajustan los vértices y los frames intermedios se calculan por interpolación lineal de cada punto entre los dos frames etiquetados a mano.
- **Regiones no rectangulares:** polígono punto a punto o dibujo a mano alzada. Para saber qué píxeles quedan dentro, cada fila se recorre buscando dónde la cortan los lados de la región; entre cada pareja de cortes, los píxeles están dentro.
- **Deshacer el último punto** con la tecla `Z`.
- **Modificar regiones** arrastrando sus vértices.
- **Eliminar regiones** con clic derecho dentro de ellas.
