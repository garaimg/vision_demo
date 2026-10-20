import os
import cv2
import numpy

VIDEO_ENTRADA = 'video_perro.mp4'
CARPETA_SALIDA = 'output'
VENTANA = 'Practica 1'
FRAMES_SALTO = 10            # frames que se avanzan con la tecla 'a'
DISTANCIA_MISMO_OBJETO = 50  # px: una region nueva mas cerca que esto sustituye a la otra
RADIO_AGARRE = 10            # px alrededor de un vertice en los que un clic lo agarra
RADIO_VERTICE = 6            # tamaño con el que se dibujan los vertices
ESPERA_TECLA_MS = 20
TERMINAR = 0                 # lo que devuelve etiquetar_frame() al pulsar 'q'

# Colores en BGR
ROJO = (0, 0, 255)
VERDE = (0, 255, 0)
AZUL = (255, 0, 0)
AMARILLO = (0, 255, 255)
NEGRO = (0, 0, 0)

puntos_en_curso = []        # puntos de la region que se esta dibujando ahora
regiones_actuales = []      # una region por objeto; None si se borro (asi no cambian los numeros)
vertice_arrastrado = None   # (indice_objeto, indice_vertice) que se esta moviendo


# Geometria

def rectangulo_envolvente(region):
    """Rectangulo mas pequeño que contiene la region: (x_min, y_min, x_max, y_max)."""
    xs = [x for (x, y) in region]
    ys = [y for (x, y) in region]
    return min(xs), min(ys), max(xs), max(ys)


def tramos_de_fila(region, y):
    """Tramos (x_ini, x_fin) de la fila y que quedan dentro de la region."""
    y_centro = y + 0.5  # centro del pixel, asi la linea nunca pasa justo por un vertice
    x_cortes = []
    for i in range(len(region)):
        # lado entre el vertice i y el anterior (con i = 0 es el lado que cierra la figura)
        x1, y1 = region[i]
        x2, y2 = region[i - 1]
        if (y1 < y_centro < y2) or (y2 < y_centro < y1):
            x_cortes.append(x1 + (y_centro - y1) * (x2 - x1) / (y2 - y1))
    x_cortes.sort()
    # los cortes van por parejas: entre el 1º y el 2º se esta dentro, entre el 3º y el 4º tambien...
    tramos = []
    for k in range(0, len(x_cortes) - 1, 2):
        tramos.append((round(x_cortes[k]), round(x_cortes[k + 1])))
    return tramos


def tramos_dentro(region):
    """Todos los tramos (y, x_ini, x_fin) que forman la region."""
    x_min, y_min, x_max, y_max = rectangulo_envolvente(region)
    tramos = []
    for y in range(y_min, y_max + 1):
        for (x_ini, x_fin) in tramos_de_fila(region, y):
            tramos.append((y, x_ini, x_fin))
    return tramos


def esta_dentro(region, x, y):
    for (x_ini, x_fin) in tramos_de_fila(region, y):
        if x_ini <= x <= x_fin:
            return True
    return False


def estan_cerca(region1, region2):
    ax1, ay1, ax2, ay2 = rectangulo_envolvente(region1)
    bx1, by1, bx2, by2 = rectangulo_envolvente(region2)
    # estan lejos si una queda entera a un lado de la otra, aun sumando la distancia
    lejos_x = ax2 + DISTANCIA_MISMO_OBJETO < bx1 or bx2 + DISTANCIA_MISMO_OBJETO < ax1
    lejos_y = ay2 + DISTANCIA_MISMO_OBJETO < by1 or by2 + DISTANCIA_MISMO_OBJETO < ay1
    return not lejos_x and not lejos_y


def distancia_centros(region1, region2):
    ax1, ay1, ax2, ay2 = rectangulo_envolvente(region1)
    bx1, by1, bx2, by2 = rectangulo_envolvente(region2)
    # no se divide entre 2 porque solo se usa para comparar
    return abs((ax1 + ax2) - (bx1 + bx2)) + abs((ay1 + ay2) - (by1 + by2))


# Edicion de regiones

def cerrar_region():
    """Guarda la region dibujada: sustituye al objeto cercano mas proximo o crea uno nuevo."""
    region_nueva = list(puntos_en_curso)
    puntos_en_curso.clear()
    mas_cerca = None
    for i, region in enumerate(regiones_actuales):
        if region is None or not estan_cerca(region, region_nueva):
            continue
        if mas_cerca is None or distancia_centros(region, region_nueva) < distancia_centros(regiones_actuales[mas_cerca], region_nueva):
            mas_cerca = i
    if mas_cerca is None:
        regiones_actuales.append(region_nueva)
    else:
        regiones_actuales[mas_cerca] = region_nueva


def buscar_vertice_cercano(x, y):
    """(indice_objeto, indice_vertice) cerca de (x, y), o None."""
    for i, region in enumerate(regiones_actuales):
        if region is None:
            continue
        for j, (vx, vy) in enumerate(region):
            if abs(vx - x) <= RADIO_AGARRE and abs(vy - y) <= RADIO_AGARRE:
                return (i, j)
    return None


def objeto_en(x, y):
    """Indice del objeto que contiene el pixel (x, y), o None."""
    for i, region in enumerate(regiones_actuales):
        if region is not None and esta_dentro(region, x, y):
            return i
    return None


def gestionar_raton(event, x, y, flags, param):
    global vertice_arrastrado
    ancho, alto = param
    # al arrastrar, el raton puede salirse de la imagen
    x = min(max(x, 0), ancho - 1)
    y = min(max(y, 0), alto - 1)

    if event == cv2.EVENT_LBUTTONDOWN:
        # solo se puede agarrar un vertice si no se esta dibujando una region
        vertice_arrastrado = None
        if len(puntos_en_curso) == 0:
            vertice_arrastrado = buscar_vertice_cercano(x, y)
        if vertice_arrastrado is None:
            puntos_en_curso.append((x, y))

    elif event == cv2.EVENT_MOUSEMOVE and vertice_arrastrado is not None:
        # copia de la region para no cambiar la guardada en frames anteriores
        i, j = vertice_arrastrado
        region_nueva = list(regiones_actuales[i])
        region_nueva[j] = (x, y)
        regiones_actuales[i] = region_nueva

    elif event == cv2.EVENT_LBUTTONUP:
        vertice_arrastrado = None

    elif event == cv2.EVENT_RBUTTONDOWN:
        i = objeto_en(x, y)
        if i is not None:
            regiones_actuales[i] = None


# Dibujo y teclado

def dibujar_region(img, region, color, cerrada):
    for i in range(1, len(region)):
        cv2.line(img, region[i - 1], region[i], color, 2)
    if cerrada:
        cv2.line(img, region[-1], region[0], color, 2)
    for vertice in region:
        cv2.circle(img, vertice, RADIO_VERTICE, AMARILLO, -1)
        cv2.circle(img, vertice, RADIO_VERTICE, NEGRO, 1)  # borde para que se vea en fondos claros


def pintar_estado(frame, num_frame):
    """Copia del frame con los objetos, la region en curso y el numero de frame."""
    img = frame.copy()
    arrastrado = None
    if vertice_arrastrado is not None:
        arrastrado = vertice_arrastrado[0]
    for i, region in enumerate(regiones_actuales):
        if region is None:
            continue
        color = AZUL if i == arrastrado else VERDE
        dibujar_region(img, region, color, True)
        cv2.putText(img, str(i + 1), region[0], cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    dibujar_region(img, puntos_en_curso, ROJO, False)
    cv2.putText(img, 'Frame ' + str(num_frame), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, NEGRO, 2)
    return img


def etiquetar_frame(frame, num_frame):
    """Muestra el frame hasta pulsar espacio, a o q. Devuelve cuantos frames avanzar."""
    while True:
        cv2.imshow(VENTANA, pintar_estado(frame, num_frame))
        tecla = cv2.waitKey(ESPERA_TECLA_MS) & 0xFF
        if tecla == ord('c') and len(puntos_en_curso) >= 3:
            cerrar_region()
        elif tecla == ord('z') and len(puntos_en_curso) > 0:
            puntos_en_curso.pop()
        elif tecla == ord(' '):
            return 1
        elif tecla == ord('a'):
            return FRAMES_SALTO
        elif tecla == ord('q'):
            return TERMINAR


# Fases del programa

def etiquetar_video(ruta):
    """Fase 1: deja etiquetar el video. Devuelve (regiones_por_frame, fps, ancho, alto)."""
    cap = cv2.VideoCapture(ruta)
    fps = cap.get(cv2.CAP_PROP_FPS)
    ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(VENTANA, gestionar_raton, (ancho, alto))
    print('clic: punto, arrastrar vertice: mover, c: cerrar, z: deshacer, clic dcho: borrar')
    print('espacio: siguiente, a: saltar', FRAMES_SALTO, 'frames, q: terminar')

    # regiones_por_frame[f] = copia de regiones_actuales en el frame f
    regiones_por_frame = []
    etiquetando = True
    ok, frame = cap.read()
    while ok:
        frames_a_avanzar = 1
        if etiquetando:
            frames_a_avanzar = etiquetar_frame(frame, len(regiones_por_frame))
            puntos_en_curso.clear()  # una region sin cerrar no pasa al siguiente frame
            if frames_a_avanzar == TERMINAR:
                # con 'q' el resto del video se queda con las ultimas regiones
                etiquetando = False
                frames_a_avanzar = 1
        # con 'a' los frames saltados reciben las mismas regiones sin etiquetarlos
        for _ in range(frames_a_avanzar):
            regiones_por_frame.append(list(regiones_actuales))
            ok, frame = cap.read()
            if not ok:
                break

    cv2.destroyWindow(VENTANA)
    cap.release()
    return regiones_por_frame, fps, ancho, alto


def region_de(regiones_frame, i):
    """Region del objeto i en un frame, o None si aun no existia o se borro."""
    if i < len(regiones_frame):
        return regiones_frame[i]
    return None


def tamano_maximo(regiones_por_frame, num_objetos):
    """Fase 2: ancho y alto maximos de cada objeto (VideoWriter necesita un tamaño fijo)."""
    anchos_max = [1] * num_objetos
    altos_max = [1] * num_objetos
    for regiones_frame in regiones_por_frame:
        for i in range(num_objetos):
            region = region_de(regiones_frame, i)
            if region is not None:
                x1, y1, x2, y2 = rectangulo_envolvente(region)
                anchos_max[i] = max(anchos_max[i], x2 - x1 + 1)
                altos_max[i] = max(altos_max[i], y2 - y1 + 1)
    return anchos_max, altos_max


def crear_video(nombre, fps, tamano):
    fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
    return cv2.VideoWriter(CARPETA_SALIDA + '/' + nombre, fourcc, fps, tamano)


def frame_negro(ancho, alto):
    return numpy.zeros((alto, ancho, 3), dtype=numpy.uint8)


def generar_videos(ruta, regiones_por_frame, fps, ancho, alto):
    """Fase 3: escribe todos los videos en CARPETA_SALIDA."""
    num_objetos = len(regiones_por_frame[-1])  # la lista solo crece, el ultimo frame tiene todos
    anchos_max, altos_max = tamano_maximo(regiones_por_frame, num_objetos)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    video_regiones = crear_video('salida_regiones.avi', fps, (ancho, alto))
    video_ocultas = crear_video('salida_ocultas.avi', fps, (ancho, alto))
    videos_rect = []
    videos_forma = []
    for i in range(num_objetos):
        tamano = (anchos_max[i], altos_max[i])
        videos_rect.append(crear_video('objeto_' + str(i + 1) + '_rect.avi', fps, tamano))
        videos_forma.append(crear_video('objeto_' + str(i + 1) + '_forma.avi', fps, tamano))

    # se vuelve a leer el video desde el principio
    cap = cv2.VideoCapture(ruta)
    for regiones_frame in regiones_por_frame:
        ok, frame = cap.read()
        if not ok:
            break
        frame_regiones = frame.copy()
        frame_oculto = frame.copy()

        for i in range(num_objetos):
            # si el objeto no esta en este frame, sus videos reciben un frame negro
            frame_rect = frame_negro(anchos_max[i], altos_max[i])
            frame_forma = frame_negro(anchos_max[i], altos_max[i])
            region = region_de(regiones_frame, i)
            if region is not None:
                x1, y1, x2, y2 = rectangulo_envolvente(region)
                dibujar_region(frame_regiones, region, VERDE, True)
                # el recorte va arriba a la izquierda, si es mas pequeño que el video, sobra negro
                frame_rect[0:y2 - y1 + 1, 0:x2 - x1 + 1] = frame[y1:y2 + 1, x1:x2 + 1]
                for (y, x_ini, x_fin) in tramos_dentro(region):
                    frame_oculto[y, x_ini:x_fin + 1] = NEGRO
                    # se resta x1, y1 para colocar el pixel dentro del recorte
                    frame_forma[y - y1, x_ini - x1:x_fin - x1 + 1] = frame[y, x_ini:x_fin + 1]
            videos_rect[i].write(frame_rect)
            videos_forma[i].write(frame_forma)

        video_regiones.write(frame_regiones)
        video_ocultas.write(frame_oculto)

    # sin release los archivos pueden quedar corruptos
    cap.release()
    video_regiones.release()
    video_ocultas.release()
    for i in range(num_objetos):
        videos_rect[i].release()
        videos_forma[i].release()
    print('terminado,', num_objetos, 'objetos. Videos en la carpeta', CARPETA_SALIDA)


if __name__ == '__main__':
    regiones_por_frame, fps, ancho, alto = etiquetar_video(VIDEO_ENTRADA)
    generar_videos(VIDEO_ENTRADA, regiones_por_frame, fps, ancho, alto)
