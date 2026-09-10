import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.promedios import obtener_boletin_texto
from database.models import SessionLocal, Alumno

# Configuración por defecto (ideal usar variables de entorno en producción)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sice.notificaciones@gmail.com"
SENDER_PASSWORD = "tu_app_password_aqui" # Reemplazar con contraseña de aplicación real

def enviar_boletin_correo(cedula_alumno: str) -> bool:
    """Envía el boletín de notas al correo del representante."""
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula_alumno).first()
        if not alumno or not alumno.representante:
            print("Error: Alumno o Representante no encontrado.")
            return False

        correo_destino = alumno.representante.correo
        boletin = obtener_boletin_texto(cedula_alumno)

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = correo_destino
        msg['Subject'] = f"SICE - Boletín de Notas: {alumno.nombre} {alumno.apellido}"

        # Cuerpo del mensaje
        msg.attach(MIMEText(boletin, 'plain'))

        # Conexión al servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        # server.login(SENDER_EMAIL, SENDER_PASSWORD) # Descomentar cuando haya credenciales reales
        # server.send_message(msg)
        server.quit()
        
        print(f"Correo preparado para enviar a {correo_destino}")
        print("NOTA: El envío real está deshabilitado hasta configurar credenciales válidas en core/notificaciones.py")
        return True
        
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
    finally:
        db.close()
