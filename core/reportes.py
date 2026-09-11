import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from database.models import SessionLocal, Alumno
from core.promedios import evaluar_condicion_academica

def generar_boletin_pdf(cedula_alumno: str, ruta_destino: str) -> bool:
    """
    Genera un boletín académico en formato PDF y lo guarda en la ruta indicada del equipo.
    Incluye las reglas académicas (Promedio >= 10 e Inasistencias <= 4).
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
            spaceAfter=10,
            textColor=colors.HexColor('#1E293B')
        )
        subtitulo_estilo = ParagraphStyle(
            'SubTitulo',
            parent=estilos['Normal'],
            fontSize=11,
            alignment=1,
            spaceAfter=5,
            textColor=colors.HexColor('#475569')
        )
        
        fecha_estilo = ParagraphStyle(
            'Fecha',
            parent=estilos['Normal'],
            fontSize=9,
            alignment=2, # Derecha
            spaceAfter=15,
            textColor=colors.HexColor('#64748B')
        )
        seccion_estilo = ParagraphStyle(
            'Seccion',
            parent=estilos['Heading2'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#0F172A')
        )
        normal_estilo = estilos['Normal']

        # Cabecera institucional con Logo
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "Logo_of_SICE.png")

        titulo_p = Paragraph("LICEO GRAN CACIQUE GUAICAIPURO", titulo_estilo)
        subtitulo_p = Paragraph("SISTEMA INTEGRAL DE CONTROL ESTUDIANTIL (SICE)<br/><b>BOLETÍN OFICIAL DE CALIFICACIONES</b>", subtitulo_estilo)

        if os.path.exists(logo_path):
            try:
                img_logo = RLImage(logo_path, width=60, height=60)
                cabecera_data = [[img_logo, [titulo_p, subtitulo_p]]]
                cabecera_tabla = Table(cabecera_data, colWidths=[70, 450])
                cabecera_tabla.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ]))
                elementos.append(cabecera_tabla)
            except Exception:
                elementos.append(titulo_p)
                elementos.append(subtitulo_p)
        else:
            elementos.append(titulo_p)
            elementos.append(subtitulo_p)

        elementos.append(Paragraph(f"Fecha de Emisión: {fecha_actual}", fecha_estilo))
        elementos.append(Spacer(1, 10))

        # Datos del Estudiante y Representante
        rep_nombre = f"{alumno.representante.nombre} {alumno.representante.apellido}" if alumno.representante else "N/A"
        rep_telefono = alumno.representante.telefono if alumno.representante else "N/A"
        anio_sec = f"{getattr(alumno, 'anio', '1er Año')} - Sección {getattr(alumno, 'seccion', 'A')}"
        inasistencias = getattr(alumno, 'inasistencias', 0) or 0

        info_data = [
            [
                Paragraph(f"<b>Estudiante:</b> {alumno.nombre} {alumno.apellido}", normal_estilo),
                Paragraph(f"<b>Cédula Estudiante:</b> {alumno.cedula}", normal_estilo)
            ],
            [
                Paragraph(f"<b>Nivel Académico:</b> {anio_sec}", normal_estilo),
                Paragraph(f"<b>Inasistencias Acumuladas:</b> {inasistencias} (Máximo: 4)", normal_estilo)
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
        elementos.append(Spacer(1, 15))

        # Tabla de Calificaciones
        elementos.append(Paragraph("Detalle de Calificaciones", seccion_estilo))
        
        tabla_datos = [["Materia", "Lapso", "Calificación (0-20)"]]
        for nota in alumno.notas:
            materia_nom = nota.materia.nombre if nota.materia else "Materia Desconocida"
            tabla_datos.append([materia_nom, str(nota.lapso), f"{nota.calificacion:.2f} pts"])

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

        # Evaluación de Condición Académica
        promedio, inasist, estado, motivo = evaluar_condicion_academica(cedula_alumno)

        color_estado = colors.HexColor('#16A34A') if estado == "APROBADO" else colors.HexColor('#DC2626')
        color_fondo = colors.HexColor('#DCFCE7') if estado == "APROBADO" else colors.HexColor('#FEE2E2')

        resumen_data = [
            [
                Paragraph("<b>PROMEDIO GENERAL ACUMULADO:</b>", normal_estilo), 
                Paragraph(f"<b>{promedio:.2f} / 20 pts</b>", normal_estilo)
            ],
            [
                Paragraph("<b>ESTADO ACADÉMICO FINAL:</b>", normal_estilo),
                Paragraph(f"<font color='{color_estado.hexval()}'><b>{estado}</b></font>", normal_estilo)
            ],
            [
                Paragraph("<b>OBSERVACIÓN OFICIAL:</b>", normal_estilo),
                Paragraph(f"<i>{motivo}</i>", normal_estilo)
            ]
        ]

        resumen_tabla = Table(resumen_data, colWidths=[240, 280])
        resumen_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_fondo),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        elementos.append(resumen_tabla)
        elementos.append(Spacer(1, 40))

        # Firmas
        firmas_data = [
            ["___________________________", "___________________________"],
            ["Firma del Director(a)", "Firma del Representante"],
            ["Sello de la Institución", ""]
        ]
        firmas_tabla = Table(firmas_data, colWidths=[260, 260])
        firmas_tabla.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#475569')),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5), # Espacio debajo de la línea
        ]))
        elementos.append(firmas_tabla)

        doc.build(elementos)
        return True
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return False
    finally:
        db.close()
