# Práctica 1: Selección de regiones en vídeo

### Autores:
Mikel, Markel, Garai, Xabat

El programa abre un vídeo, deja seleccionar con el ratón regiones (personas, animales, objetos...) frame a frame y, al terminar, genera un vídeo con las regiones dibujadas y otros vídeos con cada región recortada u ocultada.

## Manual de uso

Necesita Python con `opencv-python` y `numpy`. Para ejecutarlo:

```
python main.py
```

1. Se abre una ventana con el primer frame de `video_perro.mp4`.
2. Rodea cada objeto haciendo clic en los puntos de su contorno y pulsa `C` para cerrar la región.
3. Pasa de frame con `ESPACIO` o salta 10 frames con `A`. Las regiones se mantienen; solo hay que corregirlas cuando el objeto se mueve.
4. Pulsa `Q` cuando acabes. El resto del vídeo usa las últimas regiones y se generan los vídeos en la carpeta `output/` (tarda alrededor de un minuto).

| Control | Acción |
|---|---|
| Clic izquierdo | Añadir un punto a la región que se está dibujando (en rojo) |
| `C` | Cerrar la región (hacen falta al menos 3 puntos) |
| `Z` | Deshacer el último punto |
| Arrastrar un punto amarillo | Mover ese vértice; la región se pinta en azul mientras se mueve |
| Clic derecho dentro de una región | Borrar ese objeto para el resto del vídeo |
| `ESPACIO` | Siguiente frame |
| `A` | Saltar 10 frames |
| `Q` | Terminar y generar los vídeos |

### Vídeos generados (`output/`)

- `salida_regiones.avi`: el vídeo original con las regiones dibujadas.
- `salida_ocultas.avi`: el vídeo original con todos los objetos tapados de negro.
- `objeto_N_rect.avi`: recorte del rectángulo que rodea al objeto N.
- `objeto_N_forma.avi`: recorte del objeto N con solo lo que hay dentro de su región; el resto, negro.

## Funcionamiento básico

**Selección de regiones.** Cada región es una lista de puntos `(x, y)`. Cada clic añade un punto a `puntos_en_curso` y se dibuja con `cv2.circle`; los puntos se unen con `cv2.line`. Al pulsar `C`, se une el último punto con el primero y la región pasa a `regiones_actuales`, donde la posición en la lista es el número del objeto.

**Dos fases.** Primero se etiqueta todo el vídeo y después se generan las salidas. En cada frame se guarda una copia de `regiones_actuales` en `regiones_por_frame`. Al terminar, se vuelve a leer el vídeo desde el principio y en cada frame se dibujan las regiones guardadas para ese frame. Hacerlo en dos fases permite saber, antes de crear los vídeos, cuántos objetos hay y qué tamaño necesita cada uno.

## Funcionalidades extra

**Extracción de regiones.** El rectángulo más pequeño que contiene una región se obtiene con la X y la Y mínimas y máximas de sus puntos. Ese trozo se copia del frame con un recorte de NumPy (`frame[y1:y2, x1:x2]`). Como un `VideoWriter` necesita que todos los frames midan lo mismo, cada vídeo usa el rectángulo más grande que haya tenido su objeto en todo el vídeo. Los recortes más pequeños se pegan sobre un fondo negro creado con `numpy.zeros`.

**Ocultación de regiones.** Hay que saber qué píxeles están dentro de cada región, aunque no sea un rectángulo. Para ello se recorre la región fila a fila: en cada fila se calcula en qué X la cortan los lados del polígono (con una regla de tres) y se ordenan esos cortes. Van por parejas: entre el primero y el segundo se está dentro, entre el tercero y el cuarto también, y así sucesivamente. Esos tramos se pintan de negro en un único vídeo, para todos los objetos a la vez.

**Reducción del etiquetado manual.** Las regiones no se borran al cambiar de frame: el siguiente frame empieza con las mismas regiones. Con `A` se saltan 10 frames y todos reciben las regiones actuales, y con `Q` el resto del vídeo también. Así solo hay que intervenir cuando un objeto se mueve. Para corregirlo basta con redibujarlo encima: si la región nueva está a menos de 50 px de un objeto existente (comparando sus rectángulos), se considera el mismo objeto y lo sustituye. Si hay varios cerca, sustituye al de centro más próximo. Si no hay ninguno, es un objeto nuevo.

**Regiones no rectangulares.** Las regiones son polígonos de los puntos que se quieran. El vídeo `_forma` copia solo los tramos de dentro, calculados con el mismo método que la ocultación.

**Modificar, deshacer y eliminar.**
- **Modificar:** al pinchar a menos de 10 px de un vértice, ese vértice sigue al ratón mientras se mantiene el botón pulsado.
- **Deshacer:** `Z` quita el último punto de la región en curso.
- **Eliminar:** con clic derecho se busca qué región contiene ese píxel (mirando solo los tramos de esa fila) y se marca como `None`.

## Decisiones tomadas

- **Solo funciones vistas en clase:** las regiones se dibujan con `cv2.line` y `cv2.circle`, y el relleno y los recortes se hacen a mano con NumPy. No se han usado funciones de polígonos de OpenCV.
- **Las regiones se sustituyen, no se modifican:** cuando se mueve un vértice se crea una copia de la región. Así los frames anteriores conservan la región que tenían.
- **Los objetos borrados quedan como `None`:** no se quitan de la lista para que los demás objetos mantengan su número y su vídeo.
- **Frames negros cuando falta el objeto:** si un objeto todavía no existe o ya se ha borrado en un frame, sus vídeos `_rect` y `_forma` reciben un frame negro. Así todos los vídeos duran lo mismo que el original.
- **Objetos que se mueven mucho:** si un objeto se mueve más de 50 px entre dos correcciones, la región nueva se toma como otro objeto. Conviene corregir más a menudo o subir `DISTANCIA_MISMO_OBJETO`.
