import cv2
import numpy

VIDEO_ENTRADA = 'video_perro.mp4'
VENTANA = 'Practica 1'
SALTO = 10              # frames que avanza la tecla A
MARGEN = 50             # px: regiones a menos de esta distancia son el mismo objeto
VERDE = (0, 255, 0)     # colores en BGR
ROJO = (0, 0, 255)
AZUL = (255, 0, 0)
AMARILLO = (0, 255, 255)
NEGRO = (0, 0, 0)

# Una región es una lista de puntos (x, y). Ej: [(10, 20), (50, 20), (30, 60)]
# Cada objeto seleccionado (una persona, el perro...) tiene un número, que es su
# posición en la lista "objetos". Cada objeto tendrá sus propios vídeos.
puntos = []           # región que se está dibujando (sin cerrar)
objetos = []          # región actual de cada objeto (None si se ha borrado)
seleccionado = None   # número del objeto seleccionado (se dibuja en azul)
agarrado = None       # (nº de objeto, nº de punto) que se está moviendo con el ratón


def rectangulo(region):
    # Rectángulo mínimo que contiene la región: mínimos y máximos de X e Y
    xs = []
    ys = []
    for (x, y) in region:
        xs.append(x)
        ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def tramos_dentro(region):
    # Devuelve los trozos de cada fila que quedan dentro de la región: (y, x_inicio, x_fin).
    # En cada fila se buscan las X donde la cortan los lados del polígono.
    # Los cortes van por parejas: en el 1º se entra, en el 2º se sale, etc.
    x_min, y_min, x_max, y_max = rectangulo(region)
    tramos = []
    for y in range(y_min, y_max + 1):
        fila = y + 0.5   # centro del píxel, para no pasar justo por un vértice
        cortes = []
        for i in range(len(region)):
            x1, y1 = region[i]
            x2, y2 = region[i - 1]   # con i = 0 es el último punto: cierra el polígono
            if (y1 < fila < y2) or (y2 < fila < y1):   # el lado cruza la fila
                cortes.append(x1 + (fila - y1) * (x2 - x1) / (y2 - y1))
        cortes.sort()
        for k in range(0, len(cortes) - 1, 2):
            tramos.append((y, round(cortes[k]), round(cortes[k + 1])))
    return tramos


def cercanas(region1, region2):
    # Dos regiones son del mismo objeto si sus rectángulos se tocan o están a
    # menos de MARGEN píxeles. Los rectángulos están separados si uno termina
    # antes de que empiece el otro (en X o en Y).
    ax1, ay1, ax2, ay2 = rectangulo(region1)
    bx1, by1, bx2, by2 = rectangulo(region2)
    separados_x = ax2 + MARGEN < bx1 or bx2 + MARGEN < ax1
    separados_y = ay2 + MARGEN < by1 or by2 + MARGEN < ay1
    return not separados_x and not separados_y


def cerrar_region():
    nueva = list(puntos)
    puntos.clear()
    # Si está cerca de un objeto que ya existe, lo sustituye (el objeto se ha movido)
    for i in range(len(objetos)):
        if objetos[i] is not None and cercanas(objetos[i], nueva):
            objetos[i] = nueva
            return
    objetos.append(nueva)   # si no, es un objeto nuevo


def punto_cercano(x, y):
    # Busca un punto de alguna región a menos de 10 px del ratón.
    # Devuelve (nº de objeto, nº de punto), o None si no hay ninguno.
    for i in range(len(objetos)):
        if objetos[i] is not None:
            for j in range(len(objetos[i])):
                px, py = objetos[i][j]
                if abs(px - x) <= 10 and abs(py - y) <= 10:
                    return (i, j)
    return None


def onMouse(event, x, y, flags, param):
    global seleccionado, agarrado
    x = min(max(x, 0), ancho - 1)   # que no se salga de la imagen al arrastrar
    y = min(max(y, 0), alto - 1)

    if event == cv2.EVENT_LBUTTONDOWN:
        agarrado = None
        if len(puntos) == 0:             # si no se está dibujando, ¿se pincha un punto?
            agarrado = punto_cercano(x, y)
        if agarrado is not None:
            seleccionado = agarrado[0]   # se selecciona su región
        else:
            seleccionado = None
            puntos.append((x, y))        # clic normal: punto nuevo

    elif event == cv2.EVENT_MOUSEMOVE and agarrado is not None:
        # Mover el punto agarrado. Se crea una región nueva en vez de cambiar la
        # antigua, porque la antigua está guardada en los frames anteriores.
        i, j = agarrado
        nueva = list(objetos[i])
        nueva[j] = (x, y)
        objetos[i] = nueva

    elif event == cv2.EVENT_LBUTTONUP:   # soltar el botón: se deja de mover y vuelve a verde
        agarrado = None
        seleccionado = None

    elif event == cv2.EVENT_RBUTTONDOWN:   # clic derecho: borrar el objeto que contiene el clic
        for i in range(len(objetos)):
            if objetos[i] is not None:
                for (fy, x1, x2) in tramos_dentro(objetos[i]):
                    if fy == y and x1 <= x <= x2:
                        objetos[i] = None
                        return


def dibujar_region(imagen, region, color, cerrada):
    # Primero las líneas y después los puntos, para que los puntos queden encima
    for i in range(1, len(region)):
        cv2.line(imagen, region[i - 1], region[i], color, 2)
    if cerrada:
        cv2.line(imagen, region[-1], region[0], color, 2)
    for punto in region:
        cv2.circle(imagen, punto, 6, AMARILLO, -1)   # punto amarillo
        cv2.circle(imagen, punto, 6, NEGRO, 1)       # con borde negro para que se note


def etiquetar_frame(frame, numero):
    # Devuelve cuántos frames avanzar (0 = terminar)
    while True:
        imagen = frame.copy()
        for i in range(len(objetos)):
            if objetos[i] is not None:
                color = VERDE
                if i == seleccionado:
                    color = AZUL
                dibujar_region(imagen, objetos[i], color, True)
                cv2.putText(imagen, str(i + 1), objetos[i][0], cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        dibujar_region(imagen, puntos, ROJO, False)
        cv2.putText(imagen, 'Frame ' + str(numero), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, NEGRO, 2)
        cv2.imshow(VENTANA, imagen)

        tecla = cv2.waitKey(20) & 0xFF
        if tecla == ord('c') and len(puntos) >= 3:   # cerrar región
            cerrar_region()
        elif tecla == ord('z') and len(puntos) > 0:  # deshacer último punto
            puntos.pop()
        elif tecla == ord(' '):
            return 1
        elif tecla == ord('a'):
            return SALTO
        elif tecla == ord('q'):
            return 0


# PASO 1: ETIQUETAR
video = cv2.VideoCapture(VIDEO_ENTRADA)
fps = video.get(cv2.CAP_PROP_FPS)
ancho = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
alto = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(VENTANA, onMouse)
print('Clic: añadir punto | Arrastrar un punto: seleccionar y modificar su región')
print('C: cerrar región | Z: deshacer punto | Clic dcho: borrar objeto')
print('ESPACIO: siguiente frame | A: saltar ' + str(SALTO) + ' frames | Q: terminar')

# Para cada frame se guarda una copia de la lista de objetos.
# (Basta con list(objetos) porque una región nunca se modifica: se sustituye por otra.)
regiones_por_frame = []
etiquetando = True
hay_frame, frame = video.read()
while hay_frame:
    avance = 1
    if etiquetando:
        avance = etiquetar_frame(frame, len(regiones_por_frame))
        puntos.clear()
        if avance == 0:          # Q: el resto del vídeo usa la selección actual
            etiquetando = False
            avance = 1
    # Los frames que se avanzan reutilizan la selección actual
    for i in range(avance):
        regiones_por_frame.append(list(objetos))
        hay_frame, frame = video.read()
        if not hay_frame:
            break

cv2.destroyWindow(VENTANA)
video.release()

# PASO 2: PREPARAR VÍDEOS
n = len(objetos)   # número de objetos distintos

# Todos los frames de un vídeo deben medir lo mismo: para cada objeto se usa
# el rectángulo más grande que tenga en todo el vídeo.
anchos = [1] * n
altos = [1] * n
for regs in regiones_por_frame:
    for i in range(len(regs)):
        if regs[i] is not None:
            x1, y1, x2, y2 = rectangulo(regs[i])
            anchos[i] = max(anchos[i], x2 - x1 + 1)
            altos[i] = max(altos[i], y2 - y1 + 1)

codec = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
video_regiones = cv2.VideoWriter('salida_regiones.avi', codec, fps, (ancho, alto))
videos_rect = []
videos_forma = []
videos_oculto = []
for i in range(n):
    nombre = 'objeto_' + str(i + 1)
    videos_rect.append(cv2.VideoWriter(nombre + '_rect.avi', codec, fps, (anchos[i], altos[i])))
    videos_forma.append(cv2.VideoWriter(nombre + '_forma.avi', codec, fps, (anchos[i], altos[i])))
    videos_oculto.append(cv2.VideoWriter(nombre + '_oculto.avi', codec, fps, (ancho, alto)))

# PASO 3: GENERAR VÍDEOS
video = cv2.VideoCapture(VIDEO_ENTRADA)
for f in range(len(regiones_por_frame)):
    hay_frame, frame = video.read()
    if not hay_frame:
        break
    regs = regiones_por_frame[f]
    dibujado = frame.copy()

    for i in range(n):
        # Si el objeto no existe en este frame, sus recortes quedan negros
        # y su vídeo oculto es el frame original
        rect = numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8)
        forma = numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8)
        oculto = frame.copy()

        if i < len(regs) and regs[i] is not None:
            region = regs[i]
            x1, y1, x2, y2 = rectangulo(region)
            dibujar_region(dibujado, region, VERDE, True)                    # regiones dibujadas
            rect[0:y2 - y1 + 1, 0:x2 - x1 + 1] = frame[y1:y2 + 1, x1:x2 + 1]   # recorte rectangular
            for (y, xa, xb) in tramos_dentro(region):
                oculto[y, xa:xb + 1] = NEGRO                                  # ocultar
                forma[y - y1, xa - x1:xb - x1 + 1] = frame[y, xa:xb + 1]      # solo la forma

        videos_rect[i].write(rect)
        videos_forma[i].write(forma)
        videos_oculto[i].write(oculto)

    video_regiones.write(dibujado)

video.release()
video_regiones.release()
for i in range(n):
    videos_rect[i].release()
    videos_forma[i].release()
    videos_oculto[i].release()
print('Hecho:', n, 'objetos en', len(regiones_por_frame), 'frames')
