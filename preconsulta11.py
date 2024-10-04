import os
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Mostrar el logo
st.image("escudo_COLOR.jpg", width=100)

# Función para enviar el correo electrónico
def enviar_correo(destinatario, nombre):
    smtp_server = "smtp.gmail.com"
    port = 587  # Puerto para usar TLS
    remitente = "abcdf2024dfabc@gmail.com"
    password = "hjdd gqaw vvpj hbsy"  # Tu contraseña de aplicación

    # Crear el mensaje con la codificación adecuada
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = "Registro Completo"
    
    cuerpo = f"""\
Hola {nombre},

Usted ha solicitado su ingreso al Servicio de Preconsulta del Instituto Nacional de Cardiología Ignacio Chávez. Recuerde que este servicio está diseñado para pacientes mayores de edad, con padecimiento cardiovascular ya diagnosticado y que cuenten con carta de referencia de un centro del segundo nivel de atención.

Para continuar su proceso de atención debe de enviar al correo electrónico: xxx@cardiologia.com.mx los siguientes documentos (preferentemente en formato PDF):
1.- Identificación Oficial (sólo frente). 
2.- Carta de referencia de un centro de salud de segundo nivel.
3.- Consentimiento Informado. Se le adjunta a este correo (sólo es necesario que escriba su nombre y lo firme).

Una vez que envíe los documentos, recibirá en el plazo de 2 días hábiles un correo confirmatorio, donde se le proveerá de todo lo necesario para que tenga una cita virtual (vía zoom).
"""
    mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    # Adjuntar el archivo PDF
    pdf_path = 'ci-vqJz9O0c.pdf'
    with open(pdf_path, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename=pdf_path)
        mensaje.attach(part)

    # Establecer conexión segura con el servidor SMTP
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)  # Iniciar una conexión segura
            server.login(remitente, password)  # Autenticarse en el servidor
            server.sendmail(remitente, destinatario, mensaje.as_string())  # Enviar el correo
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

# Función para guardar los datos en un archivo Excel acumulando registros previos
def guardar_en_excel_acumulado(data):
    file_path = 'consulta_primera_vez.xlsx'
    
    # Leer los datos existentes en el archivo, si existe
    if os.path.exists(file_path):
        existing_data = pd.read_excel(file_path)
        # Concatenar los datos nuevos con los existentes
        data = pd.concat([existing_data, data], ignore_index=True)

    # Guardar los datos combinados en el archivo
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Consulta')
    
    # Leer el archivo para su descarga posterior
    with open(file_path, 'rb') as f:
        return BytesIO(f.read())

# Campos del formulario
nombre_completo = st.text_input("Nombre Completo")
genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
fecha_nacimiento = st.date_input("Fecha de Nacimiento", value=None, min_value=pd.Timestamp('1900-01-01'))

# Lista de países con "Mexico" sin acento y como opción predeterminada
paises_america = ["Argentina", "Bolivia", "Brasil", "Canada", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador", "El Salvador", "Estados Unidos", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Republica Dominicana", "Uruguay", "Venezuela"]
paises_europa = ["Alemania", "España", "Francia", "Italia", "Portugal", "Reino Unido"]

pais_nacimiento = st.selectbox("País de Nacimiento", paises_america + paises_europa, index=paises_america.index("Mexico"))
whatsapp = st.text_input("Número de WhatsApp (10 dígitos, sin espacios ni símbolos)", placeholder="Ejemplo: 5512345678")
correo = st.text_input("Correo Electrónico")
correo_confirmacion = st.text_input("Confirma tu Correo Electrónico")

# Validación y guardado de información
if st.button("Enviar"):
    if not nombre_completo or not whatsapp or not correo or not correo_confirmacion or not fecha_nacimiento:
        st.error("Por favor, completa todos los campos antes de enviar.")
    elif len(whatsapp) != 10 or not whatsapp.isdigit():
        st.error("Por favor, ingresa un número de WhatsApp válido de 10 dígitos, sin espacios ni símbolos.")
    elif correo != correo_confirmacion:
        st.error("Los correos electrónicos no coinciden.")
    else:
        # Utilizar los valores actuales de los campos de entrada
        resultados = {
            "Nombre Completo": nombre_completo,
            "Género": genero,
            "Fecha de Nacimiento": fecha_nacimiento.strftime('%d/%m/%Y'),
            "País de Nacimiento": pais_nacimiento,
            "WhatsApp": whatsapp,
            "Correo Electrónico": correo
        }

        # Convertir a un DataFrame
        df = pd.DataFrame([resultados])
        
        # Guardar los datos en un archivo Excel acumulando los registros
        excel_data = guardar_en_excel_acumulado(df)

        # Guardar el archivo en el estado de sesión para descargarlo más tarde
        st.session_state['excel_data'] = excel_data
        st.session_state['correo'] = correo  # Guardar el correo en el estado de la sesión
        
        # Enviar el correo electrónico al usuario
        if enviar_correo(correo, nombre_completo):
            st.success("¡Su cita de primera vez ha iniciado su proceso!. Revise su correo electrónico, le hemos enviado algunas instrucciones.")
        else:
            st.error("Registro completado, pero hubo un problema al enviar el correo.")

# Botón para descargar el archivo guardado solo si el correo es 'polanco@unam.mx'
if 'excel_data' in st.session_state and 'correo' in st.session_state and st.session_state['correo'] == 'polanco@unam.mx' and correo_confirmacion == 'polanco@unam.mx':
    st.download_button(
        label="Descargar Excel",
        data=st.session_state['excel_data'],
        file_name=f"consulta_primera_vez_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

