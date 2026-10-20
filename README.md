# Práctica 1: Selección de regiones en vídeo

### Autores:
Mikel, Markel, Garai, Xabat

El programa abre un vídeo y permite marcar con el ratón regiones (personas, animales, objetos...) frame a frame. Al terminar genera un vídeo con las regiones dibujadas, otro con todas ellas tapadas de negro y, para cada objeto, dos vídeos con su recorte.

## Manual de uso

Necesita Python con `opencv-python` y `numpy`. Para ejecutarlo:

```
python main.py
```

1. Se abre una ventana con el primer frame de `video_perro.mp4`.
2. Rodea cada objeto haciendo clic en los puntos de su contorno y pulsa `C` para cerrar la región.
3. Avanza con `ESPACIO` (1 frame) o `A` (10 frames). Las regiones se mantienen, así que solo hay que corregirlas cuando el objeto se mueve.
4. Pulsa `Q` al terminar. El resto del vídeo se queda con las últimas regiones y se generan los vídeos en la carpeta `output/`. Tarda alrededor de un minuto.

| Control | Acción |
|---|---|
| Clic izquierdo | Añadir un punto a la región que se está dibujando (en rojo) |
| `C` | Cerrar la región (hacen falta al menos 3 puntos) |
| `Z` | Deshacer el último punto |
| Arrastrar un punto amarillo | Mover ese vértice; la región se ve en azul mientras se mueve |
| Clic derecho dentro de una región | Borrar ese objeto para el resto del vídeo |
| `ESPACIO` | Siguiente frame |
| `A` | Saltar 10 frames |
| `Q` | Terminar y generar los vídeos |

### Vídeos generados (`output/`)

| Archivo | Contenido |
|---|---|
| `salida_regiones.avi` | Vídeo original con las regiones dibujadas |
| `salida_ocultas.avi` | Vídeo original con todos los objetos tapados de negro |
| `objeto_N_rect.avi` | Recorte del rectángulo que rodea al objeto N |
| `objeto_N_forma.avi` | Recorte del objeto N con solo lo que hay dentro de su región; el resto, negro |

## Funcionalidades implementadas

| Funcionalidad | Qué hace |
|---|---|
| Básica | Seleccionar regiones con el ratón y generar un vídeo con ellas dibujadas |
| Extracción de regiones | Un vídeo por objeto con el recorte de su rectángulo |
| Ocultación de regiones | Un vídeo completo con todos los objetos tapados de negro |
| Reducción del etiquetado manual | Las regiones se copian a los frames siguientes (también al saltar con `A`) y solo se corrigen cuando el objeto se mueve |
| Regiones no rectangulares | Polígonos de cualquier número de puntos y un vídeo con solo su contenido |
| Modificar regiones | Arrastrar un vértice para moverlo |
| Deshacer | `Z` quita el último punto |
| Eliminar | Clic derecho dentro de una región |

## Algoritmos

### 1. Cómo se guarda una región

Una región es una lista de puntos `(x, y)` en el orden en que se han pinchado. Por ejemplo, `[(2, 1), (8, 1), (5, 7)]` es un triángulo.

- **Mientras se dibuja,** los puntos se van añadiendo a `puntos_en_curso`. Cada punto se pinta con `cv2.circle` y cada pareja de puntos seguidos se une con `cv2.line`.
- **Al pulsar `C`,** también se une el último punto con el primero y la región pasa a `regiones_actuales`.

En `regiones_actuales`, la posición en la lista es el número del objeto: la posición 0 es el objeto 1, la 1 es el objeto 2, etc.

### 2. Recorrer el vídeo en dos fases

1. **Etiquetado.** Para cada frame se guarda una copia de `regiones_actuales` en `regiones_por_frame`. Así, al final se sabe qué regiones había en cada frame.
2. **Generación.** Se vuelve a leer el vídeo desde el principio y cada frame se procesa con las regiones que se guardaron para él.

Se hace en dos pasadas porque un `VideoWriter` necesita conocer su tamaño antes de escribir el primer frame. Hasta haber visto el vídeo entero no se sabe cuántos objetos hay ni cuánto llega a medir cada uno.

### 3. Rectángulo mínimo de una región

El rectángulo más pequeño que contiene la región va de la X más pequeña a la más grande, y de la Y más pequeña a la más grande. Su esquina superior izquierda es `(x_min, y_min)` y la inferior derecha `(x_max, y_max)`.

Con el triángulo del ejemplo: `x_min = 2`, `x_max = 8`, `y_min = 1` e `y_max = 7`. Este rectángulo se usa para recortar la región y para saber qué filas hay que recorrer.

### 4. Qué píxeles están dentro de la región

Es el algoritmo más importante, porque lo usan la ocultación, el vídeo `_forma` y el borrado con clic derecho. La región puede tener cualquier forma, así que no basta con el rectángulo.

**Idea:** se recorre la región **fila a fila**. Imaginamos una línea horizontal que atraviesa la figura de izquierda a derecha. Empieza fuera, y cada vez que cruza un lado cambia: en el primer corte entra, en el segundo sale, en el tercero vuelve a entrar...

**Pasos para cada fila `y`:**

1. **Buscar los cortes.** Para cada lado del polígono (del punto `i` al anterior), se mira si cruza la fila, es decir, si un extremo queda por encima y el otro por debajo. Si la cruza, se calcula en qué X lo hace con una regla de tres:
   ```
   x = x1 + (y - y1) · (x2 - x1) / (y2 - y1)
   ```
2. **Ordenar los cortes** de izquierda a derecha.
3. **Emparejarlos:** del 1.º al 2.º se está dentro, del 3.º al 4.º también, y así sucesivamente. Cada pareja es un **tramo**: un trozo de fila que está entero dentro de la región.

**Ejemplo** con el triángulo `[(2, 1), (8, 1), (5, 7)]` en la fila 4:
- El lado `(2,1)–(8,1)` es horizontal y no cruza la fila.
- El lado `(8,1)–(5,7)` la corta en `x = 6.25`.
- El lado `(5,7)–(2,1)` la corta en `x = 3.75`.
- Ordenados, los cortes son `[3.75, 6.25]`, que se redondean a `4` y `6`. En la fila 4 están dentro los píxeles 4, 5 y 6.

**Dos detalles:**
- **Regiones con entrantes:** en figuras como una "U", una fila puede cortar 4 lados o más. Por eso los cortes se agrupan por parejas y no se toma solo el primero y el último. Así los huecos quedan fuera.
- **Por qué `y + 0.5`:** la fila se mide en el centro del píxel. Los puntos tienen coordenadas enteras, así que esa línea nunca pasa justo por un vértice, que es el caso en el que se contaría un corte doble.

**Dónde se usa:**
- **Ocultar:** cada tramo se pinta de negro con `frame[y, x_ini:x_fin + 1] = NEGRO`.
- **Vídeo `_forma`:** se copian los tramos sobre un fondo negro.
- **Clic derecho:** solo se calculan los tramos de la fila del ratón y se comprueba si su X cae dentro de alguno.

### 5. Recortes y tamaño fijo de los vídeos

- **`_rect`:** se copia el rectángulo mínimo del frame con un corte de NumPy: `frame[y_min:y_max + 1, x_min:x_max + 1]`.
- **`_forma`:** se copian solo los tramos de dentro. A cada coordenada se le resta `x_min` e `y_min` para que el recorte empiece en la esquina `(0, 0)`.

Todos los frames de un vídeo deben medir lo mismo, pero la región cambia de tamaño. Por eso, antes de crear los vídeos se recorren todos los frames y se guarda el **ancho y el alto máximos** de cada objeto. Cada frame del vídeo es un fondo negro de ese tamaño (`numpy.zeros`) con el recorte pegado arriba a la izquierda. Si el objeto no existe en un frame, se escribe el fondo negro tal cual.

### 6. Reducción del etiquetado manual

**El problema:** el vídeo tiene 193 frames. Si hubiera que dibujar las regiones en todos ellos, el etiquetado sería larguísimo. Pero de un frame al siguiente los objetos apenas se mueven, así que la región de un frame sirve casi igual para los siguientes.

**La solución** tiene dos partes: reutilizar la selección en los frames siguientes y corregirla solo cuando el objeto se ha movido.

**Parte 1: reutilizar la selección.** `regiones_actuales` no se vacía al cambiar de frame, así que el frame siguiente empieza con las mismas regiones que el anterior. Al avanzar, cada frame recibe una copia de las regiones que hay en ese momento:

- **`ESPACIO`:** se guarda 1 copia y se pasa al siguiente frame.
- **`A`:** se guardan 10 copias de golpe y se muestra el frame 10 posiciones más adelante. Esos 10 frames reciben la selección sin tener que verlos ni etiquetarlos.
- **`Q`:** todos los frames que quedan reciben las últimas regiones, sin mostrar más frames.

**Parte 2: corregir solo lo que se mueve.** Cuando un objeto se ha desplazado, hay dos formas de corregirlo:
- arrastrar los vértices que se han quedado fuera;
- dibujar una región nueva encima del objeto. En ese caso no hace falta borrar la antigua: el programa detecta que es el mismo objeto y la sustituye.

**Ejemplo:** usando `A` y corrigiendo la región cada vez, los 193 frames se etiquetan mirando solo unos 20. En los demás, la selección se copia automáticamente.

**Cómo se detecta si la región nueva es del mismo objeto.** Al cerrarla con `C`, el programa sigue estos pasos:

1. **¿Está cerca?** Se comparan los rectángulos de las dos regiones. Están lejos si uno queda entero a un lado del otro (izquierda, derecha, arriba o abajo) con más de 50 px de separación. Por ejemplo, si un rectángulo termina en `x = 300` y el otro empieza en `x = 400`, hay 100 px entre ellos y son objetos distintos. Si se tocan, se solapan o están a 50 px o menos, son el mismo objeto.
2. **Si hay varios cerca,** se elige el de **centro más próximo**. El centro de un rectángulo es el punto medio entre sus esquinas, y la distancia se mide sumando la diferencia en X y la diferencia en Y.
3. **Si hay alguno,** la región nueva lo sustituye y mantiene su número. **Si no hay ninguno,** se añade como objeto nuevo al final de la lista.

### 7. Modificar, deshacer y eliminar

- **Modificar:** al pulsar el botón izquierdo sin estar dibujando, se busca un vértice a menos de 10 px en X y en Y del ratón. Si lo hay, ese vértice sigue al ratón (`EVENT_MOUSEMOVE`) hasta que se suelta el botón (`EVENT_LBUTTONUP`). No se cambia la región original: se crea una copia con el vértice movido. Si se cambiara la original, también cambiaría en los frames anteriores, que guardan esa misma lista.
- **Deshacer:** `Z` quita el último punto de `puntos_en_curso` con `pop()`.
- **Eliminar:** con clic derecho se busca la región que contiene el píxel (algoritmo 4) y se sustituye por `None`. No se quita de la lista para que los demás objetos conserven su número y sus vídeos.

## Decisiones tomadas

- **Solo funciones vistas en clase.** Para dibujar se usan `cv2.line`, `cv2.circle` y `cv2.putText`, y para el vídeo `VideoCapture`, `VideoWriter`, `imshow`, `waitKey` y `setMouseCallback`. El relleno y los recortes se hacen a mano con NumPy, sin funciones de polígonos de OpenCV.
- **Polígonos en lugar de rectángulos.** Rodear un objeto con varios puntos se ajusta mucho mejor a su forma. El rectángulo mínimo se calcula a partir de ellos cuando hace falta.
- **Corregir redibujando.** No hay que borrar la región antigua: basta con dibujar la nueva encima, que es más rápido al etiquetar.
- **Un vídeo por objeto en los recortes y uno común para la ocultación.** Los recortes no tienen sentido juntos, pero en el vídeo oculto interesa ver todo tapado a la vez.
- **Frames negros cuando falta el objeto.** Así los vídeos de cada objeto duran lo mismo que el original y van sincronizados con él.
- **Limitación:** si un objeto se mueve más de 50 px entre dos correcciones, la región nueva se toma como otro objeto. Conviene corregir más a menudo o subir `DISTANCIA_MISMO_OBJETO` en `main.py`.
