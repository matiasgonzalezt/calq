from flask import Flask, request, render_template, send_file, jsonify
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Función para calcular las reacciones en los apoyos
def calcular_reacciones(longitud, cargas_puntuales, posiciones_cargas, cargas_distribuidas, desde_distribuidas, hasta_distribuidas):
    # Inicializar sumas de fuerzas y momentos
    suma_fuerzas = 0
    suma_momentos_A = 0  # Momento en el apoyo A (en x=0)
    
    # Calcular efectos de las cargas puntuales
    for i in range(len(cargas_puntuales)):
        P = float(cargas_puntuales[i])
        x = float(posiciones_cargas[i])
        suma_fuerzas += P
        suma_momentos_A += P * x
    
    # Calcular efectos de las cargas distribuidas
    for i in range(len(cargas_distribuidas)):
        w = float(cargas_distribuidas[i])
        x1 = float(desde_distribuidas[i])
        x2 = float(hasta_distribuidas[i])
        L = x2 - x1
        P_dist = w * L  # Fuerza equivalente de la carga distribuida
        x_eq = (x1 + x2) / 2  # Posición del centroide de la carga distribuida
        suma_fuerzas += P_dist
        suma_momentos_A += P_dist * x_eq
    
    # Aplicar ecuaciones de equilibrio
    RB = suma_momentos_A / longitud
    RA = suma_fuerzas - RB
    
    return RA, RB

# Ruta principal que carga el HTML
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para calcular las reacciones y generar el gráfico
@app.route('/grafico', methods=['POST'])
def grafico():
    data = request.get_json()
    longitud = float(data['longitud'])

    cargas_puntuales = data.get('cargas_puntuales', [])
    posiciones_cargas = data.get('posiciones_cargas', [])
    cargas_distribuidas = data.get('cargas_distribuidas', [])
    desde_distribuidas = data.get('desde_distribuidas', [])
    hasta_distribuidas = data.get('hasta_distribuidas', [])

    # Calcular reacciones en los apoyos
    RA, RB = calcular_reacciones(longitud, cargas_puntuales, posiciones_cargas, cargas_distribuidas, desde_distribuidas, hasta_distribuidas)

    # Encontrar el valor máximo de las cargas y reacciones
    max_carga_puntual = max([float(c) for c in cargas_puntuales], default=0)
    max_carga_distribuida = max([float(c) for c in cargas_distribuidas], default=0)
    max_reaccion = max(RA, RB)
    max_valor = max(max_carga_puntual, max_carga_distribuida, max_reaccion)

    # Crear la figura con un tamaño fijo
    fig, ax = plt.subplots(figsize=(longitud + 1, max_valor + 1))  # Fijar el tamaño de la figura

    # Configurar color de fondo
    ax.set_facecolor('#ffffff')  # Fondo blanco

    # Definir una función para dibujar un triángulo
    def dibujar_triangulo(ax, x_centro, y_centro, base=1, altura=1, color='black'):
        # Coordenadas de los vértices del triángulo
        vertices = [
            (x_centro - base / 4, y_centro),  # Vértice inferior izquierdo
            (x_centro + base / 4, y_centro),  # Vértice inferior derecho
            (x_centro, y_centro + altura)     # Vértice superior
        ]
        triangulo = plt.Polygon(vertices, color='black')
        ax.add_patch(triangulo)

    # Dibujar dos triángulos en puntos específicos
    x_triangulo_1 = 0  # Posición en x del primer triángulo
    x_triangulo_2 = longitud  # Posición en x del segundo triángulo
    y_triangulo = -1.5   # Posición en y (debajo de la viga)

    # Dibujar los triángulos
    dibujar_triangulo(ax, x_triangulo_1, y_triangulo, base=1, altura=1, color='blue')  # Triángulo 1
    dibujar_triangulo(ax, x_triangulo_2, y_triangulo, base=1, altura=1, color='blue')  # Triángulo 2


    # Parámetros para el grosor de la línea de las flechas y el tamaño de la cabeza
    arrow_head_width = 0.3  # Tamaño fijo para el ancho de la cabeza de la flecha
    arrow_head_length = 0.6  # Tamaño fijo para la longitud de la cabeza de la flecha
    arrow_line_width = 5.0  # Grosor de la línea de las flechas

    # Dibujar la viga con color y grosor
    ax.plot([0, longitud], [0, 0], color='black', linewidth=15, solid_capstyle='butt', label='Viga')

    # Ajustar el punto de inicio de las flechas para que comience más abajo
    offset_flecha = 2.5  # Valor para ajustar qué tan abajo empieza la flecha

    # Dibujar las reacciones en los apoyos con grosor de línea personalizado
    ax.arrow(0, -RA - offset_flecha, 0, RA, head_width=arrow_head_width, head_length=arrow_head_length,
             fc='#1982C4', ec='#1982C4', linewidth=arrow_line_width)
    ax.text(0, -RA - offset_flecha - 1.5, f'RA = {RA:.2f} kN', color='#1982C4', ha='center', fontsize=12)

    ax.arrow(longitud, -RB - offset_flecha, 0, RB, head_width=arrow_head_width, head_length=arrow_head_length,
             fc='#1982C4', ec='#1982C4', linewidth=arrow_line_width)
    ax.text(longitud, -RB - offset_flecha - 1.5, f'RB = {RB:.2f} kN', color='#1982C4', ha='center', fontsize=12)

    # Ajustar el punto de inicio de las flechas para que comience más abajo
    offset_carga = -0.5  # Valor para ajustar qué tan abajo empieza la flecha

    # Dibujar cargas puntuales con grosor de línea personalizado
    for i in range(len(cargas_puntuales)):
        carga = float(cargas_puntuales[i])
        posicion = float(posiciones_cargas[i])
        ax.arrow(posicion, offset_carga, 0, -carga, head_width=arrow_head_width, head_length=arrow_head_length,
                fc='#BF1A2F', ec='#BF1A2F', linewidth=arrow_line_width)
        ax.text(posicion, -carga - 2, f'p = {carga} kN', color='#BF1A2F', ha='center', fontsize=12)

    # Dibujar cargas distribuidas con rectángulo verde y etiquetar
    for i in range(len(cargas_distribuidas)):
        carga_dist = float(cargas_distribuidas[i])
        desde = float(desde_distribuidas[i])
        hasta = float(hasta_distribuidas[i])
        ax.add_patch(plt.Rectangle((desde, 0), hasta - desde, carga_dist, color='#018E42', alpha=0.6))
        ax.text((desde + hasta) / 2, carga_dist + 0.5, f'q = {carga_dist} kN/m', color='#018E42', ha='center', fontsize=12)
        
    # Estilo del gráfico
    ax.set_xlim(-1, longitud + 1)
    ax.set_ylim(min(-RA, -RB) - 5, 10)
    ax.set_xlabel('Longitud de la viga (m)', fontsize=13)
    ax.set_ylabel('Fuerza (kN)', fontsize=13)
    ax.set_title('Gráfico de Reacciones y Cargas', fontsize=16, fontweight='bold')

    # Líneas de cuadrícula
    ax.grid(True, which='both', linestyle='--', linewidth=1, color='gray', alpha=0.7)

    # Guardar la gráfica en un buffer de memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())  # Guarda con fondo
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
