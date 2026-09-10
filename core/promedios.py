from database.models import SessionLocal, Nota

def calcular_promedio_alumno(cedula: str) -> float:
    """Calcula el promedio general de todas las notas de un alumno."""
    db = SessionLocal()
    try:
        notas = db.query(Nota).filter(Nota.cedula_alumno == cedula).all()
        if not notas:
            return 0.0
        
        suma_calificaciones = sum(nota.calificacion for nota in notas)
        promedio = suma_calificaciones / len(notas)
        return round(promedio, 2)
    finally:
        db.close()

def obtener_boletin_texto(cedula: str) -> str:
    """Genera un reporte de texto con las notas y promedio del alumno."""
    db = SessionLocal()
    try:
        from database.models import Alumno
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula).first()
        if not alumno:
            return "Alumno no encontrado."

        anio_sec = f"{getattr(alumno, 'anio', '1er Año')} - Sección {getattr(alumno, 'seccion', 'A')}"
        boletin = f"Boletín de Notas: {alumno.nombre} {alumno.apellido}\n"
        boletin += f"Cédula: {alumno.cedula} | Nivel: {anio_sec}\n"
        boletin += "-" * 45 + "\n"
        
        for nota in alumno.notas:
            boletin += f"Materia: {nota.materia.nombre} | Lapso: {nota.lapso} | Calificación: {nota.calificacion}\n"
            
        promedio = calcular_promedio_alumno(cedula)
        boletin += "-" * 40 + "\n"
        boletin += f"Promedio General: {promedio}\n"
        
        return boletin
    finally:
        db.close()
