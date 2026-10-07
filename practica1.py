import cv2
import numpy

VIDEO_ENTRADA = 'video_perro.mp4'
VENTANA = 'Practica 1'
SALTO = 10              # frames que avanza la tecla A
VERDE = (0, 255, 0)     # colores en BGR
ROJO = (0, 0, 255)
NEGRO = (0, 0, 0)

# Una región es una lista de puntos (x, y). Ej: [(10, 20), (50, 20), (30, 60)]
puntos = []        # región que se está dibujando (sin cerrar)
regiones = []      # regiones cerradas del frame actual
agarrado = None    # (nº región, nº vértice) que se está moviendo con el ratón


def distancia(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


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


def vertice_cercano(x, y):
    for r in range(len(regiones)):
        for v in range(len(regiones[r])):
            if distancia(regiones[r][v], (x, y)) < 10:
                return (r, v)
    return None


def onMouse(event, x, y, flags, param):
    global agarrado
    x = min(max(x, 0), ancho - 1)   # que no se salga de la imagen
    y = min(max(y, 0), alto - 1)

    if event == cv2.EVENT_LBUTTONDOWN:
        agarrado = None
        if len(puntos) == 0:             # si no se está dibujando, ¿se pincha un vértice?
            agarrado = vertice_cercano(x, y)
        if agarrado is None:
            puntos.append((x, y))        # clic: punto nuevo

    elif event == cv2.EVENT_MOUSEMOVE and flags & cv2.EVENT_FLAG_LBUTTON:
        if agarrado is not None:         # mover el vértice agarrado
            r, v = agarrado
            regiones[r][v] = (x, y)
        elif len(puntos) > 0 and distancia(puntos[-1], (x, y)) >= 8:
            puntos.append((x, y))        # arrastrar: mano alzada

    elif event == cv2.EVENT_LBUTTONUP:
        agarrado = None

    elif event == cv2.EVENT_RBUTTONDOWN:  # borrar la región que contiene el clic
        for i in range(len(regiones)):
            for (fy, x1, x2) in tramos_dentro(regiones[i]):
                if fy == y and x1 <= x <= x2:
                    del regiones[i]
                    return


def dibujar_region(imagen, region, color, cerrada):
    for i in range(len(region)):
        cv2.circle(imagen, region[i], 3, color, -1)
        if i > 0:
            cv2.line(imagen, region[i - 1], region[i], color, 2)
    if cerrada:
        cv2.line(imagen, region[-1], region[0], color, 2)


def etiquetar_frame(frame, numero):
    # Devuelve cuántos frames avanzar (0 = terminar)
    while True:
        imagen = frame.copy()
        for region in regiones:
            dibujar_region(imagen, region, VERDE, True)
        dibujar_region(imagen, puntos, ROJO, False)
        cv2.putText(imagen, 'Frame ' + str(numero), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, NEGRO, 2)
        cv2.imshow(VENTANA, imagen)

        tecla = cv2.waitKey(20) & 0xFF
        if tecla == ord('c') and len(puntos) >= 3:   # cerrar región
            regiones.append(list(puntos))
            puntos.clear()
        elif tecla == ord('z') and len(puntos) > 0:  # deshacer último punto
            puntos.pop()
        elif tecla == ord(' '):
            return 1
        elif tecla == ord('a'):
            return SALTO
        elif tecla == ord('q'):
            return 0


def interpolar(regiones_a, regiones_b, t):
    # Cada punto avanza en línea recta: p = pa + t * (pb - pa), con t entre 0 y 1
    resultado = []
    for i in range(len(regiones_a)):
        a = regiones_a[i]
        if i < len(regiones_b) and len(regiones_b[i]) == len(a):
            b = regiones_b[i]
        else:
            b = a   # no se pueden emparejar los puntos: la región se queda igual
        nueva = []
        for j in range(len(a)):
            x = round(a[j][0] + t * (b[j][0] - a[j][0]))
            y = round(a[j][1] + t * (b[j][1] - a[j][1]))
            nueva.append((x, y))
        resultado.append(nueva)
    return resultado


# ===================== PASO 1: ETIQUETAR =====================
video = cv2.VideoCapture(VIDEO_ENTRADA)
fps = video.get(cv2.CAP_PROP_FPS)
ancho = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
alto = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(VENTANA, onMouse)
print('Clic: punto | Arrastrar: mano alzada / mover vértice | Clic dcho: borrar región')
print('C: cerrar región | Z: deshacer | ESPACIO: siguiente | A: saltar ' + str(SALTO) + ' | Q: terminar')

claves = []   # frames etiquetados a mano: lista de (nº de frame, regiones)
numero = 0
etiquetando = True
hay_frame, frame = video.read()
while hay_frame:
    avance = 1
    if etiquetando:
        avance = etiquetar_frame(frame, numero)
        copia = []
        for region in regiones:
            copia.append(list(region))   # copia: si luego se mueve un vértice, esta no cambia
        claves.append((numero, copia))
        puntos.clear()
        if avance == 0:                  # Q: el resto del vídeo usa estas regiones
            etiquetando = False
            avance = 1
    for i in range(avance):              # las regiones se mantienen al avanzar
        hay_frame, frame = video.read()
        if not hay_frame:
            break
        numero += 1

total = numero + 1
cv2.destroyWindow(VENTANA)
video.release()

# ===================== PASO 2: REGIONES DE CADA FRAME =====================
# Entre dos frames clave a y b se interpola. Tras el último, se repiten sus regiones.
regiones_por_frame = []
for k in range(len(claves)):
    a, regiones_a = claves[k]
    if k + 1 < len(claves):
        b, regiones_b = claves[k + 1]
    else:
        b, regiones_b = total, regiones_a
    for f in range(a, b):
        regiones_por_frame.append(interpolar(regiones_a, regiones_b, (f - a) / (b - a)))

# ===================== PASO 3: PREPARAR VÍDEOS =====================
# Todos los frames de un vídeo deben medir lo mismo: para cada región se usa
# el rectángulo más grande que tenga en todo el vídeo.
n = 0
for regs in regiones_por_frame:
    n = max(n, len(regs))
anchos = [1] * n
altos = [1] * n
for regs in regiones_por_frame:
    for i in range(len(regs)):
        x1, y1, x2, y2 = rectangulo(regs[i])
        anchos[i] = max(anchos[i], x2 - x1 + 1)
        altos[i] = max(altos[i], y2 - y1 + 1)

codec = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
video_regiones = cv2.VideoWriter('salida_regiones.avi', codec, fps, (ancho, alto))
video_oculto = cv2.VideoWriter('salida_oculta.avi', codec, fps, (ancho, alto))
videos_rect = []
videos_forma = []
for i in range(n):
    videos_rect.append(cv2.VideoWriter('region_' + str(i + 1) + '_rect.avi', codec, fps, (anchos[i], altos[i])))
    videos_forma.append(cv2.VideoWriter('region_' + str(i + 1) + '_forma.avi', codec, fps, (anchos[i], altos[i])))

# ===================== PASO 4: GENERAR VÍDEOS =====================
video = cv2.VideoCapture(VIDEO_ENTRADA)
for f in range(total):
    hay_frame, frame = video.read()
    if not hay_frame:
        break
    dibujado = frame.copy()
    oculto = frame.copy()

    # Fondos negros para los recortes (si la región no existe en este frame, queda negro)
    lienzos_rect = []
    lienzos_forma = []
    for i in range(n):
        lienzos_rect.append(numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8))
        lienzos_forma.append(numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8))

    regs = regiones_por_frame[f]
    for i in range(len(regs)):
        x1, y1, x2, y2 = rectangulo(regs[i])
        tramos = tramos_dentro(regs[i])

        dibujar_region(dibujado, regs[i], VERDE, True)                       # básico
        lienzos_rect[i][0:y2 - y1 + 1, 0:x2 - x1 + 1] = frame[y1:y2 + 1, x1:x2 + 1]  # recorte
        for (y, xa, xb) in tramos:
            oculto[y, xa:xb + 1] = NEGRO                                       # ocultar
            lienzos_forma[i][y - y1, xa - x1:xb - x1 + 1] = frame[y, xa:xb + 1]  # solo la forma

    video_regiones.write(dibujado)
    video_oculto.write(oculto)
    for i in range(n):
        videos_rect[i].write(lienzos_rect[i])
        videos_forma[i].write(lienzos_forma[i])

video.release()
video_regiones.release()
video_oculto.release()
for i in range(n):
    videos_rect[i].release()
    videos_forma[i].release()
print('Hecho. Frames etiquetados a mano:', len(claves), 'de', total)
