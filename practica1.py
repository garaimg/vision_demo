import cv2
import numpy

VIDEO = 'video_perro.mp4'
VENTANA = 'Practica 1'
SALTO = 10
MARGEN = 50

VERDE = (0, 255, 0)
ROJO = (0, 0, 255)
AZUL = (255, 0, 0)
AMARILLO = (0, 255, 255)
NEGRO = (0, 0, 0)

# cada region es una lista de puntos (x, y)
# objetos[i] es la region actual del objeto i, o None si se ha borrado
puntos = []
objetos = []
seleccionado = None
agarrado = None   # (objeto, punto) que se esta arrastrando


def rectangulo(region):
    xs = []
    ys = []
    for (x, y) in region:
        xs.append(x)
        ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def tramos_dentro(region):
    # recorro la region fila a fila y miro donde la cortan los lados,
    # entre cada par de cortes los pixeles estan dentro
    x_min, y_min, x_max, y_max = rectangulo(region)
    tramos = []
    for y in range(y_min, y_max + 1):
        fila = y + 0.5
        cortes = []
        for i in range(len(region)):
            x1, y1 = region[i]
            x2, y2 = region[i - 1]
            if (y1 < fila < y2) or (y2 < fila < y1):
                cortes.append(x1 + (fila - y1) * (x2 - x1) / (y2 - y1))
        cortes.sort()
        for k in range(0, len(cortes) - 1, 2):
            tramos.append((y, round(cortes[k]), round(cortes[k + 1])))
    return tramos


def cercanas(r1, r2):
    ax1, ay1, ax2, ay2 = rectangulo(r1)
    bx1, by1, bx2, by2 = rectangulo(r2)
    lejos_x = ax2 + MARGEN < bx1 or bx2 + MARGEN < ax1
    lejos_y = ay2 + MARGEN < by1 or by2 + MARGEN < ay1
    return not lejos_x and not lejos_y


def cerrar_region():
    nueva = list(puntos)
    puntos.clear()
    # si hay un objeto cerca se sustituye, si no es uno nuevo
    for i in range(len(objetos)):
        if objetos[i] is not None and cercanas(objetos[i], nueva):
            objetos[i] = nueva
            return
    objetos.append(nueva)


def punto_cercano(x, y):
    for i in range(len(objetos)):
        if objetos[i] is None:
            continue
        for j in range(len(objetos[i])):
            px, py = objetos[i][j]
            if abs(px - x) <= 10 and abs(py - y) <= 10:
                return (i, j)
    return None


def onMouse(event, x, y, flags, param):
    global seleccionado, agarrado
    x = min(max(x, 0), ancho - 1)
    y = min(max(y, 0), alto - 1)

    if event == cv2.EVENT_LBUTTONDOWN:
        agarrado = None
        if len(puntos) == 0:
            agarrado = punto_cercano(x, y)
        if agarrado is not None:
            seleccionado = agarrado[0]
        else:
            seleccionado = None
            puntos.append((x, y))

    elif event == cv2.EVENT_MOUSEMOVE and agarrado is not None:
        # hago una copia de la region para no cambiar la de los frames anteriores
        i, j = agarrado
        nueva = list(objetos[i])
        nueva[j] = (x, y)
        objetos[i] = nueva

    elif event == cv2.EVENT_LBUTTONUP:
        agarrado = None
        seleccionado = None

    elif event == cv2.EVENT_RBUTTONDOWN:
        for i in range(len(objetos)):
            if objetos[i] is None:
                continue
            for (fy, x1, x2) in tramos_dentro(objetos[i]):
                if fy == y and x1 <= x <= x2:
                    objetos[i] = None
                    return


def dibujar_region(img, region, color, cerrada):
    for i in range(1, len(region)):
        cv2.line(img, region[i - 1], region[i], color, 2)
    if cerrada:
        cv2.line(img, region[-1], region[0], color, 2)
    for p in region:
        cv2.circle(img, p, 6, AMARILLO, -1)
        cv2.circle(img, p, 6, NEGRO, 1)


def etiquetar(frame, num):
    # devuelve cuantos frames hay que avanzar, 0 si se pulsa q
    while True:
        img = frame.copy()
        for i in range(len(objetos)):
            if objetos[i] is None:
                continue
            color = AZUL if i == seleccionado else VERDE
            dibujar_region(img, objetos[i], color, True)
            cv2.putText(img, str(i + 1), objetos[i][0], cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        dibujar_region(img, puntos, ROJO, False)
        cv2.putText(img, 'Frame ' + str(num), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, NEGRO, 2)
        cv2.imshow(VENTANA, img)

        tecla = cv2.waitKey(20) & 0xFF
        if tecla == ord('c') and len(puntos) >= 3:
            cerrar_region()
        elif tecla == ord('z') and len(puntos) > 0:
            puntos.pop()
        elif tecla == ord(' '):
            return 1
        elif tecla == ord('a'):
            return SALTO
        elif tecla == ord('q'):
            return 0


cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(VENTANA, onMouse)
print('clic: punto, arrastrar punto: mover, c: cerrar, z: deshacer, clic dcho: borrar')
print('espacio: siguiente, a: saltar', SALTO, 'frames, q: terminar')

# guardo los objetos que hay en cada frame
regiones_frames = []
etiquetando = True
ok, frame = cap.read()
while ok:
    avance = 1
    if etiquetando:
        avance = etiquetar(frame, len(regiones_frames))
        puntos.clear()
        if avance == 0:
            etiquetando = False
            avance = 1
    for _ in range(avance):
        regiones_frames.append(list(objetos))
        ok, frame = cap.read()
        if not ok:
            break

cv2.destroyWindow(VENTANA)
cap.release()

# tamaño de los videos de cada objeto (el rectangulo mas grande que tenga)
n = len(objetos)
anchos = [1] * n
altos = [1] * n
for regs in regiones_frames:
    for i in range(len(regs)):
        if regs[i] is not None:
            x1, y1, x2, y2 = rectangulo(regs[i])
            anchos[i] = max(anchos[i], x2 - x1 + 1)
            altos[i] = max(altos[i], y2 - y1 + 1)

fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
out = cv2.VideoWriter('salida_regiones.avi', fourcc, fps, (ancho, alto))
out_rect = []
out_forma = []
out_oculto = []
for i in range(n):
    nombre = 'objeto_' + str(i + 1)
    out_rect.append(cv2.VideoWriter(nombre + '_rect.avi', fourcc, fps, (anchos[i], altos[i])))
    out_forma.append(cv2.VideoWriter(nombre + '_forma.avi', fourcc, fps, (anchos[i], altos[i])))
    out_oculto.append(cv2.VideoWriter(nombre + '_oculto.avi', fourcc, fps, (ancho, alto)))

cap = cv2.VideoCapture(VIDEO)
for f in range(len(regiones_frames)):
    ok, frame = cap.read()
    if not ok:
        break
    regs = regiones_frames[f]
    dibujado = frame.copy()

    for i in range(n):
        rect = numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8)
        forma = numpy.zeros((altos[i], anchos[i], 3), dtype=numpy.uint8)
        oculto = frame.copy()

        if i < len(regs) and regs[i] is not None:
            r = regs[i]
            x1, y1, x2, y2 = rectangulo(r)
            dibujar_region(dibujado, r, VERDE, True)
            rect[0:y2 - y1 + 1, 0:x2 - x1 + 1] = frame[y1:y2 + 1, x1:x2 + 1]
            for (y, xa, xb) in tramos_dentro(r):
                oculto[y, xa:xb + 1] = NEGRO
                forma[y - y1, xa - x1:xb - x1 + 1] = frame[y, xa:xb + 1]

        out_rect[i].write(rect)
        out_forma[i].write(forma)
        out_oculto[i].write(oculto)

    out.write(dibujado)

cap.release()
out.release()
for i in range(n):
    out_rect[i].release()
    out_forma[i].release()
    out_oculto[i].release()
print('terminado,', n, 'objetos')
