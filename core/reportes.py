import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from database.models import SessionLocal, Alumno
from core.promedios import calcular_promedio_alumno

def generar_boletin_pdf(cedula_alumno: str, ruta_destino: str) -> bool:
    """
    Genera un boletín académico en formato PDF y lo guarda en la ruta indicada del equipo.
    """
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula_alumno).first()
        if not alumno:
            return False

        doc = SimpleDocTemplate(
            ruta_destino,
            pagesize=letter,
            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
        )
        
        elementos = []
        estilos = getSampleStyleSheet()

        # Estilos personalizados
        titulo_estilo = ParagraphStyle(
            'TituloPrincipal',
            parent=estilos['Heading1'],
            fontSize=16,
            alignment=1, # Centrado
            spaceAfter=15,
            textColor=colors.HexColor('#1E293B')
        )
        subtitulo_estilo = ParagraphStyle(
            'SubTitulo',
            parent=estilos['Normal'],
            fontSize=11,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#475569')
        )
        seccion_estilo = ParagraphStyle(
            'Seccion',
            parent=estilos['Heading2'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#0F172A')
        )
        normal_estilo = estilos['Normal']

        # Cabecera institucional
        elementos.append(Paragraph("LICEO GRAN CACIQUE GUAICAIPURO", titulo_estilo))
        elementos.append(Paragraph("SISTEMA INTEGRAL DE CONTROL ESTUDIANTIL (SICE)<br/><b>BOLETÍN OFICIAL DE CALIFICACIONES</b>", subtitulo_estilo))
        elementos.append(Spacer(1, 10))

        # Datos del Estudiante y Representante
        rep_nombre = f"{alumno.representante.nombre} {alumno.representante.apellido}" if alumno.representante else "N/A"
        rep_cedula = alumno.representante.cedula if alumno.representante else "N/A"
        rep_telefono = alumno.representante.telefono if alumno.representante else "N/A"

        anio_sec = f"{getattr(alumno, 'anio', '1er Año')} - Sección {getattr(alumno, 'seccion', 'A')}"
        info_data = [
            [
                Paragraph(f"<b>Estudiante:</b> {alumno.nombre} {alumno.apellido}", normal_estilo),
                Paragraph(f"<b>Cédula Estudiante:</b> {alumno.cedula}", normal_estilo)
            ],
            [
                Paragraph(f"<b>Nivel Académico:</b> {anio_sec}", normal_estilo),
                Paragraph(f"<b>Fecha de Nacimiento:</b> {alumno.fecha_nacimiento or 'N/A'}", normal_estilo)
            ],
            [
                Paragraph(f"<b>Representante:</b> {rep_nombre}", normal_estilo),
                Paragraph(f"<b>Teléfono Rep.:</b> {rep_telefono}", normal_estilo)
            ]
        ]
        
        info_tabla = Table(info_data, colWidths=[260, 260])
        info_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        elementos.append(info_tabla)
        elementos.append(Spacer(1, 20))

        # Tabla de Calificaciones
        elementos.append(Paragraph("Detalle de Calificaciones", seccion_estilo))
        
        tabla_datos = [["Materia", "Lapso", "Calificación (0-20)"]]
        for nota in alumno.notas:
            materia_nom = nota.materia.nombre if nota.materia else "Materia Desconocida"
            tabla_datos.append([materia_nom, str(nota.lapso), f"{nota.calificacion:.2f}"])

        if len(tabla_datos) == 1:
            tabla_datos.append(["Sin notas registradas", "-", "-"])

        notas_tabla = Table(tabla_datos, colWidths=[240, 140, 140])
        notas_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        elementos.append(notas_tabla)
        elementos.append(Spacer(1, 15))

        # Promedio General
        promedio = calcular_promedio_alumno(cedula_alumno)
        resumen_data = [
            [Paragraph("<b>PROMEDIO GENERAL ACUMULADO:</b>", normal_estilo), Paragraph(f"<b>{promedio:.2f} pts</b>", normal_estilo)]
        ]
        resumen_tabla = Table(resumen_data, colWidths=[360, 160])
        resumen_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elementos.append(resumen_tabla)

        doc.build(elementos)
        return True
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return False
    finally:
        db.close()
