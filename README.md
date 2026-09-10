# SICE - Sistema Integral de Control Estudiantil

Sistema local de escritorio desarrollado en Python y CustomTkinter para la gestión académica, control de matrícula, cálculo automatizado de promedios y emisión de boletines oficiales del **Liceo Gran Cacique Guaicaipuro**.

## Características Principales

*   **Autenticación de Administrador:** Control de acceso seguro mediante credenciales.
*   **Gestión de Matrícula por Niveles:** Soporte para Año (1er a 5to Año) y Secciones (A, B, C, D, U).
*   **Consulta y Filtros en Tiempo Real:** Tabla interactiva de estudiantes con búsqueda rápida y doble clic para consultar notas.
*   **Carga Masiva vía Excel (.xlsx):** Generación y procesamiento de plantillas de matrícula escolar con `openpyxl`.
*   **Generación de Boletines en PDF:** Emisión de reportes oficiales de calificaciones con `reportlab`.
*   **Notificaciones por Correo:** Envío automatizado de boletines a representantes vía SMTP.
*   **Persistencia Local:** Base de datos SQLite embebida sin requerimiento de servidores externos.

## Instalación y Uso

1. Clonar el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd sice
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Iniciar la base de datos con datos de prueba (opcional):
   ```bash
   python seed.py
   ```

4. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

*Credenciales por defecto:*
*   **Usuario:** `admin`
*   **Contraseña:** `password`
