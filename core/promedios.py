from database.models import SessionLocal, Nota, Alumno

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


def evaluar_condicion_academica(cedula: str) -> tuple[float, int, str, str]:
    """
    Evalúa las reglas académicas del Liceo:
    - Inasistencias > 4 -> REPROBADO (Exceso de Inasistencias)
    - Promedio < 10.0 -> REPROBADO (Promedio Insuficiente)
    - Promedio >= 10.0 y Inasistencias <= 4 -> APROBADO
    Retorna: (promedio, inasistencias, estado, motivo)
    """
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula).first()
        if not alumno:
            return 0.0, 0, "NO ENCONTRADO", "Estudiante no registrado"

        promedio = calcular_promedio_alumno(cedula)
        inasistencias = getattr(alumno, 'inasistencias', 0) or 0

        if inasistencias > 4:
            estado = "REPROBADO"
            motivo = f"Reprobado automáticamente por acumular {inasistencias} inasistencias (Límite: 4)."
        elif promedio < 10.0:
            estado = "REPROBADO"
            motivo = f"Reprobado por promedio insuficiente ({promedio:.2f} pts < 10.0 pts)."
        else:
            estado = "APROBADO"
            motivo = f"Aprobado satisfactoriamente con {promedio:.2f} pts."

        return promedio, inasistencias, estado, motivo
    finally:
        db.close()


def obtener_boletin_texto(cedula: str) -> str:
    """Genera un reporte de texto con las notas, inasistencias y condición del alumno."""
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula).first()
        if not alumno:
            return "Alumno no encontrado."

        anio_sec = f"{getattr(alumno, 'anio', '1er Año')} - Sección {getattr(alumno, 'seccion', 'A')}"
        promedio, inasistencias, estado, motivo = evaluar_condicion_academica(cedula)

        boletin = "=" * 50 + "\n"
        boletin += f"LICEO GRAN CACIQUE GUAICAIPURO\n"
        boletin += f"BOLETÍN OFICIAL DE CONTROL ESTUDIANTIL\n"
        boletin += "=" * 50 + "\n"
        boletin += f"Estudiante: {alumno.nombre} {alumno.apellido}\n"
        boletin += f"Cédula: {alumno.cedula} | Nivel: {anio_sec}\n"
        boletin += f"Inasistencias Acumuladas: {inasistencias} / 4 permitidas\n"
        boletin += "-" * 50 + "\n"
        boletin += "CALIFICACIONES:\n"
        
        if alumno.notas:
            for nota in alumno.notas:
                materia_nom = nota.materia.nombre if nota.materia else "Materia"
                boletin += f" - {materia_nom} | Lapso {nota.lapso}: {nota.calificacion:.2f} pts\n"
        else:
            boletin += " - Sin calificaciones registradas a la fecha.\n"
            
        boletin += "-" * 50 + "\n"
        boletin += f"PROMEDIO GENERAL: {promedio:.2f} pts\n"
        boletin += f"ESTADO FINAL: [{estado}]\n"
        boletin += f"OBSERVACIÓN: {motivo}\n"
        boletin += "=" * 50 + "\n"
        
        return boletin
    finally:
        db.close()
