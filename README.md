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
| Pinchar y arrastrar un punto amarillo | Seleccionar su región (se pinta en azul mientras se arrastra) y mover ese punto |
| `C` | Cerrar la región actual |
| `Z` | Deshacer el último punto |
| Clic derecho dentro de una región | Eliminar ese objeto |
| `ESPACIO` | Siguiente frame (mantiene las regiones) |
| `A` | Saltar 10 frames manteniendo las regiones |
| `Q` | Terminar el etiquetado y generar los vídeos |

Al cerrar una región cerca de otra ya existente (a menos de 50 px), la nueva sustituye a la antigua: se considera el mismo objeto que se ha movido. Si está lejos, es un objeto nuevo.

## Salida

- `salida_regiones.avi`: vídeo original con las regiones dibujadas.
- `objeto_N_rect.avi`: recorte del rectángulo mínimo que delimita el objeto N.
- `objeto_N_forma.avi`: recorte del objeto N con solo el contenido de su región (fuera, negro).
- `objeto_N_oculto.avi`: vídeo completo con el objeto N tapado de negro.

## Extras implementados

- **Extracción de regiones:** un vídeo por objeto con el recorte de su rectángulo mínimo (mínimos y máximos de X e Y de sus puntos).
- **Ocultación de regiones:** un vídeo por objeto en el que su región se rellena de negro siguiendo su forma exacta.
- **Reducción del etiquetado manual:** las regiones se mantienen al pasar de frame (`ESPACIO`) o al saltar 10 frames (`A`); solo hay que redibujar cuando el objeto se mueve.
- **Regiones no rectangulares:** las regiones son polígonos de cualquier número de puntos, y el vídeo `_forma` extrae solo su contenido. Para saber qué píxeles quedan dentro, cada fila se recorre buscando dónde la cortan los lados del polígono; entre cada pareja de cortes, los píxeles están dentro.
- **Seleccionar y modificar regiones:** al pinchar en un punto de una región, esta queda seleccionada (en azul mientras se arrastra) y el punto se puede mover. También se puede dibujar una región nueva sobre un objeto para sustituir la anterior.
- **Deshacer el último punto** con la tecla `Z`.
- **Eliminar selecciones** con clic derecho.
