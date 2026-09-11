import os
import sys
import shutil
import tempfile
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import joinedload

# Asegurar importaciones del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import SessionLocal, Alumno, DB_PATH, engine
from core.promedios import evaluar_condicion_academica
from core.reportes import generar_boletin_pdf

app = FastAPI(
    title="SICE - Portal Web & API",
    description="Sistema Integral de Control Estudiantil - API de Consulta Web Móvil",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_PORTAL = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SICE - Portal de Calificaciones</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0B132B;
            --bg-card: #1C2541;
            --border-color: #3A506B;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --primary: #2563EB;
            --primary-hover: #1D4ED8;
            --success: #16A34A;
            --danger: #DC2626;
            --success-bg: rgba(22, 163, 74, 0.15);
            --danger-bg: rgba(220, 38, 38, 0.15);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 15px;
        }
        .container {
            width: 100%;
            max-width: 540px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .header {
            text-align: center;
            padding: 10px 0 15px;
        }
        .header h1 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #FFFFFF;
        }
        .header p {
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 4px;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .search-box {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        label {
            font-size: 13px;
            font-weight: 600;
            color: #CBD5E1;
        }
        .input-group {
            display: flex;
            gap: 8px;
        }
        input[type="text"] {
            flex: 1;
            background: #0F172A;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 15px;
            color: #FFF;
            outline: none;
            text-transform: uppercase;
        }
        input[type="text"]:focus {
            border-color: var(--primary);
        }
        button {
            background: var(--primary);
            color: #FFF;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        button:hover {
            background: var(--primary-hover);
        }
        .btn-download {
            width: 100%;
            background: #0284C7;
            padding: 14px;
            font-size: 15px;
            text-decoration: none;
            color: white;
            border-radius: 8px;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            font-weight: 600;
            margin-top: 15px;
        }
        .btn-download:hover {
            background: #0369A1;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-aprobado {
            background: var(--success-bg);
            color: #4ADE80;
            border: 1px solid #16A34A;
        }
        .badge-reprobado {
            background: var(--danger-bg);
            color: #F87171;
            border: 1px solid #DC2626;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 15px;
            font-size: 13px;
        }
        .info-item {
            background: #0F172A;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .info-item span {
            display: block;
            color: var(--text-muted);
            font-size: 11px;
            margin-bottom: 2px;
        }
        .info-item b {
            font-size: 14px;
            color: #FFF;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        th {
            background: #0F172A;
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
        }
        .text-center { text-align: center; }
        .alert {
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            display: none;
            margin-top: 12px;
        }
        .alert-error {
            background: var(--danger-bg);
            border: 1px solid var(--danger);
            color: #FCA5A5;
        }
        .loading {
            text-align: center;
            color: var(--text-muted);
            font-size: 14px;
            display: none;
            padding: 15px;
        }
        footer {
            margin-top: auto;
            padding: 20px 0 10px;
            text-align: center;
            font-size: 11px;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SICE MÓVIL</h1>
            <p>Consulta Oficial de Calificaciones del Estudiante</p>
        </div>

        <div class="card">
            <div class="search-box">
                <label for="cedula">Cédula de Identidad del Alumno</label>
                <div class="input-group">
                    <input type="text" id="cedula" placeholder="Ej: V-30123456" autofocus>
                    <button onclick="buscarEstudiante()">🔍 Consultar</button>
                </div>
            </div>
            <div id="error-msg" class="alert alert-error"></div>
            <div id="loading" class="loading">Buscando expediente académico...</div>
        </div>

        <div id="resultado-card" class="card" style="display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
                <div>
                    <h2 id="res-nombre" style="font-size: 17px; font-weight: 700;"></h2>
                    <p id="res-cedula" style="font-size: 13px; color: var(--text-muted);"></p>
                </div>
                <div id="res-badge"></div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <span>NIVEL ACADÉMICO</span>
                    <b id="res-nivel"></b>
                </div>
                <div class="info-item">
                    <span>INASISTENCIAS</span>
                    <b id="res-inasist"></b>
                </div>
                <div class="info-item">
                    <span>PROMEDIO GENERAL</span>
                    <b id="res-promedio" style="color: #60A5FA;"></b>
                </div>
                <div class="info-item">
                    <span>REPRESENTANTE</span>
                    <b id="res-rep"></b>
                </div>
            </div>

            <h3 style="font-size: 14px; margin-top: 20px; color: #CBD5E1;">Detalle de Asignaturas</h3>
            <table>
                <thead>
                    <tr>
                        <th>Materia</th>
                        <th class="text-center">Lapso</th>
                        <th class="text-center">Nota</th>
                    </tr>
                </thead>
                <tbody id="res-notas"></tbody>
            </table>

            <a id="btn-descargar-pdf" href="#" class="btn-download" target="_blank">
                📥 Descargar Boletín Oficial en PDF
            </a>
        </div>

        <footer>
            Liceo Gran Cacique Guaicaipuro &bull; SICE v1.0
        </footer>
    </div>

    <script>
        async function buscarEstudiante() {
            const input = document.getElementById('cedula');
            let cedula = input.value.trim().toUpperCase();
            const errorDiv = document.getElementById('error-msg');
            const loadingDiv = document.getElementById('loading');
            const resultCard = document.getElementById('resultado-card');

            errorDiv.style.display = 'none';
            resultCard.style.display = 'none';

            if (!cedula) {
                errorDiv.innerText = 'Por favor ingresa la cédula del estudiante.';
                errorDiv.style.display = 'block';
                return;
            }

            loadingDiv.style.display = 'block';

            try {
                const res = await fetch(`/api/v1/estudiante/${encodeURIComponent(cedula)}`);
                loadingDiv.style.display = 'none';

                if (!res.ok) {
                    const data = await res.json();
                    errorDiv.innerText = data.detail || 'Estudiante no encontrado en el sistema.';
                    errorDiv.style.display = 'block';
                    return;
                }

                const data = await res.json();
                mostrarResultado(data);
            } catch (err) {
                loadingDiv.style.display = 'none';
                errorDiv.innerText = 'Error de conexión con el servidor escolar.';
                errorDiv.style.display = 'block';
            }
        }

        function mostrarResultado(data) {
            document.getElementById('res-nombre').innerText = `${data.nombre} ${data.apellido}`;
            document.getElementById('res-cedula').innerText = `C.I. ${data.cedula}`;
            document.getElementById('res-nivel').innerText = `${data.anio} - Sec. ${data.seccion}`;
            document.getElementById('res-inasist').innerText = `${data.inasistencias} faltas`;
            document.getElementById('res-promedio').innerText = `${data.promedio.toFixed(2)} pts`;
            document.getElementById('res-rep').innerText = data.representante.nombre || 'No asignado';

            const badgeDiv = document.getElementById('res-badge');
            if (data.estado === 'APROBADO') {
                badgeDiv.innerHTML = '<span class="badge badge-aprobado">APROBADO</span>';
            } else {
                badgeDiv.innerHTML = '<span class="badge badge-reprobado">REPROBADO</span>';
            }

            const tbody = document.getElementById('res-notas');
            tbody.innerHTML = '';

            if (data.notas && data.notas.length > 0) {
                data.notas.forEach(n => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${n.materia}</td>
                        <td class="text-center">${n.lapso}</td>
                        <td class="text-center"><b>${n.calificacion.toFixed(2)}</b></td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center" style="color: #94A3B8;">Sin calificaciones registradas</td></tr>';
            }

            document.getElementById('btn-descargar-pdf').href = `/api/v1/boletin/${encodeURIComponent(data.cedula)}`;
            document.getElementById('resultado-card').style.display = 'block';
        }

        document.getElementById('cedula').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                buscarEstudiante();
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    """Portal web optimizado para consulta móvil de representantes."""
    return HTML_PORTAL

@app.get("/api/v1/salud")
def health_check():
    """Estado del servicio."""
    db = SessionLocal()
    try:
        total = db.query(Alumno).count()
        return {"estado": "activo", "total_alumnos": total}
    finally:
        db.close()

@app.get("/api/v1/estudiante/{cedula}")
def obtener_estudiante(cedula: str):
    """Consulta los datos académicos de un estudiante mediante su cédula."""
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).options(
            joinedload(Alumno.representante),
            joinedload(Alumno.notas)
        ).filter(Alumno.cedula == cedula).first()

        if not alumno:
            # Búsqueda tolerante sin prefijo
            cedula_limpia = cedula.replace("V-", "").replace("E-", "").replace("V", "").replace("E", "").strip()
            alumno = db.query(Alumno).options(
                joinedload(Alumno.representante),
                joinedload(Alumno.notas)
            ).filter(Alumno.cedula.like(f"%{cedula_limpia}")).first()

        if not alumno:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

        promedio, inasistencias, estado, motivo = evaluar_condicion_academica(alumno.cedula)

        notas_data = []
        for n in (alumno.notas or []):
            materia_nom = n.materia.nombre if n.materia else "Materia Desconocida"
            notas_data.append({
                "materia": materia_nom,
                "lapso": n.lapso,
                "calificacion": n.calificacion
            })

        rep_nombre = f"{alumno.representante.nombre} {alumno.representante.apellido}" if alumno.representante else None
        rep_telefono = alumno.representante.telefono if alumno.representante else None

        return {
            "cedula": alumno.cedula,
            "nombre": alumno.nombre,
            "apellido": alumno.apellido,
            "anio": alumno.anio or "1er Año",
            "seccion": alumno.seccion or "A",
            "inasistencias": inasistencias,
            "promedio": promedio,
            "estado": estado,
            "motivo": motivo,
            "representante": {
                "nombre": rep_nombre,
                "telefono": rep_telefono
            },
            "notas": notas_data
        }
    finally:
        db.close()

@app.get("/api/v1/boletin/{cedula}")
def descargar_boletin_pdf(cedula: str):
    """Genera al vuelo y descarga el boletín académico oficial en PDF."""
    db = SessionLocal()
    try:
        alumno = db.query(Alumno).filter(Alumno.cedula == cedula).first()
        if not alumno:
            cedula_limpia = cedula.replace("V-", "").replace("E-", "").replace("V", "").replace("E", "").strip()
            alumno = db.query(Alumno).filter(Alumno.cedula.like(f"%{cedula_limpia}")).first()

        if not alumno:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"Boletin_{alumno.cedula}.pdf")

        exito = generar_boletin_pdf(alumno.cedula, pdf_path)
        if not exito or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Error al generar el boletín PDF.")

        return FileResponse(
            path=pdf_path,
            filename=f"Boletin_{alumno.cedula}.pdf",
            media_type="application/pdf"
        )
    finally:
        db.close()

SYNC_SECRET_TOKEN = os.environ.get("SYNC_SECRET_TOKEN", "sice_secret_sync_token_2026")

@app.post("/admin/sync-db")
async def sincronizar_base_datos(
    file: UploadFile = File(...),
    x_sync_token: str = Header(None)
):
    """Endpoint protegido para sincronizar/reemplazar el archivo sice.db."""
    if not x_sync_token or x_sync_token != SYNC_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token de sincronización inválido o no proporcionado.")
    
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de base de datos (.db).")
    
    engine.dispose()
    temp_dest = DB_PATH + ".incoming"
    try:
        with open(temp_dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if os.path.exists(DB_PATH):
            backup_path = DB_PATH + ".bak"
            shutil.copy2(DB_PATH, backup_path)
            
        shutil.move(temp_dest, DB_PATH)
        return {"status": "ok", "message": "Base de datos sincronizada exitosamente."}
    except Exception as e:
        if os.path.exists(temp_dest):
            os.remove(temp_dest)
        raise HTTPException(status_code=500, detail=f"Error durante el reemplazo: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
