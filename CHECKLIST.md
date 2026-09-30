# SICE - Plan de Desarrollo y Mejoras Pendientes

Documento de seguimiento de requerimientos, mejoras de backend y funcionalidades pendientes para el Sistema Integral de Control Estudiantil (SICE).

---

## 1. Gestión Académica y Materias
- [x] **Catálogo y Pensum por Grado:** Definición formal de las materias que corresponden a cada año escolar (1er a 5to Año).
- [x] **Asignación Automática de Materias:** Al inscribir o importar un estudiante en un año escolar, generar automáticamente sus materias y registros de notas pendientes.
- [ ] **Carga de Calificaciones por Planilla:** Vista para seleccionar (Año + Sección + Materia + Lapso) e ingresar notas de todos los alumnos simultáneamente.
- [ ] **Asignación de Profesores:** Vincular docentes a asignaturas y secciones específicas.

---

## 2. Control de Asistencia y Operaciones
- [x] **Carga Rápida de Inasistencias:** Módulo tipo "Pase de Lista" para registrar faltas por fecha y sección completa de forma quincenal/mensual.
- [x] **Respaldo Local (Backup 1-Clic):** Botón para exportar copias de seguridad fechadas de `sice.db` a una carpeta local o pendrive.
- [ ] **Cierre de Año Escolar y Promoción:** Flujo para culminar el periodo lectivo, promover alumnos aprobados al grado superior y congelar el historial académico.

---

## 3. Seguridad y Arquitectura
- [x] **Hashing de Contraseñas:** Almacenamiento seguro de credenciales con hash SHA-256 en la tabla `usuario`.
- [x] **Control de Roles:** Separación de permisos entre Administrador y Operador con validación en interfaz.
- [x] **Auditoría de Cambios:** Tabla de logs (`AuditoriaLog`) que registra usuario, acción, tabla y marca temporal.

---

## 4. Estado de Despliegue y Sincronización
- [x] Portal web desplegado y activo en PythonAnywhere (`https://alexipalacio.pythonanywhere.com`).
- [x] Endpoint seguro de sincronización remota (`POST /admin/sync-db` con `X-Sync-Token`).
- [x] Sincronización asíncrona desde la aplicación de escritorio (`main.py`).
- [x] Edición de ficha de estudiante y notas con sistema de doble verificación de cambios.
