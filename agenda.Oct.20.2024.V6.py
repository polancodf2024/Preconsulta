import streamlit as st
from datetime import datetime, timedelta
from fpdf import FPDF

# Función para verificar disponibilidad
def verificar_disponibilidad(fecha_str, hora_str):
    with open('reservaciones.txt', 'r') as file:
        for linea in file:
            fecha, hora, *_ = linea.strip().split("|")
            if fecha == fecha_str and hora == hora_str:
                return False
    return True

# Función para encontrar la próxima disponibilidad
def encontrar_proxima_disponibilidad(dias_preferidos, turno):
    fecha_actual = datetime.today()
    dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4}
    dias_preferidos_numeros = [dias_semana[dia.lower()] for dia in dias_preferidos]

    for _ in range(365 * 2):
        if fecha_actual.weekday() in dias_preferidos_numeros:
            hora_inicial = 7 if turno == 'Mañana' else 12
            for hora in range(hora_inicial, hora_inicial + 6):
                hora_str = f"{hora:02d}:00"
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
                if verificar_disponibilidad(fecha_str, hora_str):
                    return fecha_str, hora_str
        fecha_actual += timedelta(days=1)
    raise Exception("No se encontró disponibilidad en los próximos dos años.")

# Función para registrar una cita
def registrar_cita(fecha, hora, expediente, paciente, servicio):
    with open('reservaciones.txt', 'a') as f:
        f.write(f"{fecha}|{hora}|{expediente}|{paciente}|{servicio}\n")

# **Nueva Rutina de PDF Proporcionada**
def generar_pdf(paciente, usuario, expediente, citas_asignadas):
    pdf = FPDF()
    pdf.add_page()
    pdf.image('escudo_COLOR.jpg', 10, 8, 33)
    pdf.set_font("Arial", size=12)
    pdf.ln(40)
    pdf.cell(200, 10, txt=f"Nombre del Paciente: {paciente}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Nombre del Usuario: {usuario}", ln=True, align="L")
    pdf.ln(10)

    for i, cita in enumerate(citas_asignadas, start=1):
        fecha, hora, estudio, clinica = cita
        pdf.cell(200, 10, txt=f"Fecha: {fecha}", ln=True)
        pdf.cell(200, 10, txt=f"Horario: {hora}", ln=True)
        pdf.cell(200, 10, txt=f"Estudio: {estudio}", ln=True)
        pdf.cell(200, 10, txt=f"Clínica: {clinica}", ln=True)
        pdf.ln(5)
        if i % 4 == 0:
            pdf.add_page()
            pdf.image('escudo_COLOR.jpg', 10, 8, 33)
            pdf.set_font("Arial", size=12)
            pdf.ln(40)
            pdf.cell(200, 10, txt=f"Nombre del Paciente: {paciente}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Nombre del Usuario: {usuario}", ln=True, align="L")
            pdf.ln(10)

    pdf_file = f"citas_{expediente}.pdf"
    pdf.output(pdf_file)
    return pdf_file

# Función para cargar los usuarios desde 'usuarios.txt'
def cargar_usuarios():
    usuarios = {}
    with open('usuarios.txt', 'r') as f:
        for linea in f:
            password, usuario = map(str.strip, linea.split('|'))
            usuarios[password] = usuario
    return usuarios

# Función para cargar servicios desde 'SERVICIOS.txt'
def cargar_servicios(archivo):
    servicios_por_especialidad = {}
    with open(archivo, 'r') as f:
        for linea in f:
            clave, nombre, especialidad = linea.strip().split('|')
            if especialidad not in servicios_por_especialidad:
                servicios_por_especialidad[especialidad] = []
            servicios_por_especialidad[especialidad].append(f"{clave} - {nombre}")
    return servicios_por_especialidad

# Inicialización del estado de la sesión
if "validado" not in st.session_state:
    st.session_state["validado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "seleccionados" not in st.session_state:
    st.session_state["seleccionados"] = set()

usuarios = cargar_usuarios()  # Cargar usuarios desde archivo

st.title("Sistema de Gestión de Citas Médicas")

# Entrada de contraseña y validación automática al presionar Enter
password = st.text_input("Ingrese su contraseña:", type="password")

if password in usuarios:
    st.session_state["validado"] = True
    st.session_state["usuario"] = usuarios[password]
    st.success(f"Bienvenido(a), {st.session_state['usuario']}")
else:
    if password:
        st.error("Contraseña incorrecta.")

if st.session_state["validado"]:
    expediente = st.text_input("Número de Expediente:")
    paciente = st.text_input("Nombre del Paciente:")
    turno = st.selectbox("Seleccione el turno:", ["Mañana", "Tarde"])
    dias_preferidos = st.multiselect(
        "Días preferentes:", ["lunes", "martes", "miércoles", "jueves", "viernes"]
    )

    servicios_por_especialidad = cargar_servicios("SERVICIOS.txt")
    especialidades = list(servicios_por_especialidad.keys())
    especialidad_seleccionada = st.selectbox("Seleccione la especialidad", especialidades)

    st.subheader("Servicios Disponibles:")
    for servicio in servicios_por_especialidad[especialidad_seleccionada]:
        if st.checkbox(servicio, key=f"chk_{servicio}"):
            st.session_state["seleccionados"].add(servicio)

    st.subheader("Servicios Seleccionados:")
    for servicio in list(st.session_state["seleccionados"]):
        if not st.checkbox(servicio, value=True, key=f"chk_sel_{servicio}"):
            st.session_state["seleccionados"].remove(servicio)

    if expediente and paciente and st.session_state["seleccionados"]:
        if st.button("Generar PDF"):
            try:
                citas_asignadas = []
                for servicio in st.session_state["seleccionados"]:
                    codigo, estudio = servicio.split(" - ")
                    clinica = especialidad_seleccionada
                    fecha, hora = encontrar_proxima_disponibilidad(dias_preferidos, turno)
                    registrar_cita(fecha, hora, expediente, paciente, f"{codigo}|{estudio}|{clinica}")
                    citas_asignadas.append((fecha, hora, estudio, clinica))

                pdf_file = generar_pdf(paciente, st.session_state["usuario"], expediente, citas_asignadas)
                st.success("Citas asignadas correctamente.")
                st.download_button("Descargar PDF", data=open(pdf_file, "rb"), file_name=pdf_file)
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")

