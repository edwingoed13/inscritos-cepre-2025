from flask import Flask, jsonify, request, render_template
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__, template_folder='templates')

# Diccionarios para mapear IDs a nombres
nombres_sedes = {1: 'Virtual', 2: 'Juliaca', 3: 'Puno', 4: 'Juli-Chucuito', 5: 'Ayaviri', 6: 'Azángaro', 7: 'Huancané-Moho', 8: 'Ilave'}
nombres_areas = {1: 'Biomédicas', 2: 'Ingenierías', 3: 'Sociales'}
nombres_turnos = {1: 'Mañana', 2: 'Tarde', 3: 'Noche'}

# Diccionario de vacantes disponibles
vacantes_disponibles = {
    ('Virtual', 'Biomédicas', 'Mañana'): 2000,
    ('Virtual', 'Biomédicas', 'Tarde'): 2000,
    ('Virtual', 'Biomédicas', 'Noche'): 2000,
    ('Virtual', 'Ingenierías', 'Mañana'): 2000,
    ('Virtual', 'Ingenierías', 'Tarde'): 2000,
    ('Virtual', 'Ingenierías', 'Noche'): 2000,
    ('Virtual', 'Sociales', 'Mañana'): 2000,
    ('Virtual', 'Sociales', 'Tarde'): 2000,
    ('Virtual', 'Sociales', 'Noche'): 2000,
    ('Juliaca', 'Biomédicas', 'Mañana'): 250,
    ('Juliaca', 'Biomédicas', 'Tarde'): 249,
    ('Juliaca', 'Ingenierías', 'Mañana'): 243,
    ('Juliaca', 'Ingenierías', 'Tarde'): 243,
    ('Juliaca', 'Sociales', 'Mañana'): 278,
    ('Juliaca', 'Sociales', 'Tarde'): 278,
    ('Puno', 'Biomédicas', 'Mañana'): 192,
    ('Puno', 'Biomédicas', 'Tarde'): 180,
    ('Puno', 'Biomédicas', 'Noche'): 90,
    ('Puno', 'Ingenierías', 'Mañana'): 270,
    ('Puno', 'Ingenierías', 'Tarde'): 270,
    ('Puno', 'Ingenierías', 'Noche'): 90,
    ('Puno', 'Sociales', 'Mañana'): 515,
    ('Puno', 'Sociales', 'Tarde'): 515,
    ('Puno', 'Sociales', 'Noche'): 180,
    ('Juli-Chucuito', 'Biomédicas', 'Tarde'): 40,
    ('Juli-Chucuito', 'Ingenierías', 'Tarde'): 59,
    ('Juli-Chucuito', 'Sociales', 'Tarde'): 51,
    ('Ayaviri', 'Biomédicas', 'Tarde'): 55,
    ('Ayaviri', 'Ingenierías', 'Tarde'): 55,
    ('Ayaviri', 'Sociales', 'Tarde'): 96,
    ('Azángaro', 'Biomédicas', 'Tarde'): 50,
    ('Azángaro', 'Ingenierías', 'Tarde'): 60,
    ('Azángaro', 'Sociales', 'Tarde'): 110,
    ('Huancané-Moho', 'Biomédicas', 'Tarde'): 55,
    ('Huancané-Moho', 'Ingenierías', 'Tarde'): 55,
    ('Huancané-Moho', 'Sociales', 'Tarde'): 55,
    ('Ilave', 'Biomédicas', 'Mañana'): 45,
    ('Ilave', 'Ingenierías', 'Mañana'): 45,
    ('Ilave', 'Sociales', 'Mañana'): 56
}

def obtener_token(session):
    url = 'https://sistemas.cepreuna.edu.pe/login'
    respuesta = session.get(url)
    if respuesta.status_code != 200:
        print('Error al obtener el token CSRF.')
        return None

    soup = BeautifulSoup(respuesta.text, 'html.parser')
    token = soup.find('input', {'name': '_token'})['value']
    return token

def iniciar_sesion(session, email, password):
    token = obtener_token(session)
    if not token:
        return False

    url = 'https://sistemas.cepreuna.edu.pe/login'
    datos = {
        '_token': token,
        'email': email,
        'password': password
    }

    respuesta = session.post(url, data=datos)

    if respuesta.ok and respuesta.url != url:
        print('Inicio de sesión exitoso.')
        return True
    else:
        print('Error al iniciar sesión.')
        return False

def obtener_datos(session):
    todos_los_datos = []
    pagina = 1

    while True:
        url = f'https://sistemas.cepreuna.edu.pe/intranet/inscripcion/estudiante/lista/data?query=%7B%7D&limit=1000&ascending=1&page={pagina}&byColumn=1'
        respuesta = session.get(url)

        if respuesta.status_code != 200:
            print(f'Error al obtener datos de la página {pagina}.')
            break

        datos = respuesta.json()

        if not datos.get('data'):
            break

        # Filtrar solo los registros con "estado": "1"
        datos_filtrados = [registro for registro in datos['data'] if registro.get("estado") == "1"]
        todos_los_datos.extend(datos_filtrados)

        pagina += 1

    return todos_los_datos

def filtrar_datos_por_sede(datos, sede_filtro):
    if not sede_filtro:
        return datos
    return [registro for registro in datos if str(registro.get('sedes_id')) == sede_filtro]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/obtener_datos', methods=['GET'])
def obtener_datos_endpoint():
    email = os.getenv('CEPREUNA_EMAIL')  # Obtiene el email desde las variables de entorno
    password = os.getenv('CEPREUNA_PASSWORD')  # Obtiene la contraseña desde las variables de entorno
    sede_filtro = request.args.get('sede', None)

    with requests.Session() as session:
        if iniciar_sesion(session, email, password):
            datos = obtener_datos(session)
            datos_filtrados = filtrar_datos_por_sede(datos, sede_filtro)

            conteo_areas = defaultdict(int)
            conteo_turnos = defaultdict(lambda: defaultdict(int))
            vacantes_restantes = defaultdict(lambda: defaultdict(int))

            # Obtener el nombre de la sede seleccionada
            sede_nombre = nombres_sedes.get(int(sede_filtro)) if sede_filtro else None

            # Inicializar todas las áreas con 0
            for area_nombre in nombres_areas.values():
                conteo_areas[area_nombre] = 0  # Inicializar con 0

            # Inicializar todos los turnos disponibles para la sede seleccionada con 0
            if sede_nombre:
                for area_nombre in nombres_areas.values():
                    for turno_nombre in nombres_turnos.values():
                        clave = (sede_nombre, area_nombre, turno_nombre)
                        if clave in vacantes_disponibles:
                            conteo_turnos[area_nombre][turno_nombre] = 0  # Inicializar con 0
                            vacantes_restantes[area_nombre][turno_nombre] = vacantes_disponibles[clave]

            # Contar inscritos reales
            for registro in datos_filtrados:
                area_nombre = nombres_areas.get(registro.get('areas_id'), 'Sin Área')
                turno_nombre = nombres_turnos.get(registro.get('turnos_id'), 'Sin Turno')

                conteo_areas[area_nombre] += 1
                conteo_turnos[area_nombre][turno_nombre] += 1

            # Calcular vacantes restantes (solo para la sede seleccionada).
            if sede_nombre:
                for area_nombre in nombres_areas.values():
                    for turno_nombre in nombres_turnos.values():
                        clave = (sede_nombre, area_nombre, turno_nombre)
                        if clave in vacantes_disponibles:
                            vacantes_restantes[area_nombre][turno_nombre] = (
                                vacantes_disponibles[clave] - conteo_turnos[area_nombre][turno_nombre]
                            )

            total_inscritos = sum(conteo_areas.values())

            respuesta = {
                'total_inscritos': total_inscritos,
                'areas': dict(conteo_areas),
                'turnos': {area: dict(turnos) for area, turnos in conteo_turnos.items()},
                'vacantes_restantes': {area: dict(turnos) for area, turnos in vacantes_restantes.items()}
            }

            return jsonify(respuesta)
        else:
            return jsonify({'error': 'No se pudo iniciar sesión'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)





















