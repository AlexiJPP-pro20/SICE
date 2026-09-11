import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from sqlalchemy.orm import joinedload
from PIL import Image
import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "Logo_of_SICE.png")

from database.models import init_db, SessionLocal, Usuario, Alumno, Representante, Nota, Materia
from core.promedios import obtener_boletin_texto, evaluar_condicion_academica
from core.notificaciones import enviar_boletin_correo
from core.reportes import generar_boletin_pdf
from core.importador import registrar_alumno_manual, importar_alumnos_excel, generar_plantilla_excel

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Inicializar base de datos
        init_db()

        # Cache en memoria para filtrado ultrarrápido
        self.cached_alumnos_data = []


        # Configuración de ventana
        self.title("SICE - Sistema Integral de Control Estudiantil")
        self.geometry("1100x720")
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        
        self.mostrar_login()

    def mostrar_login(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=10)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        if os.path.exists(LOGO_PATH):
            try:
                img_pil = Image.open(LOGO_PATH)
                self.logo_login_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(90, 90))
                self.lbl_login_logo = ctk.CTkLabel(self.login_frame, text="", image=self.logo_login_img)
                self.lbl_login_logo.pack(pady=(20, 5), padx=25)
            except Exception:
                pass

        self.login_label = ctk.CTkLabel(self.login_frame, text="Iniciar Sesión", font=ctk.CTkFont(size=20, weight="bold"))
        self.login_label.pack(pady=(5, 15), padx=25)

        self.entry_username = ctk.CTkEntry(self.login_frame, placeholder_text="Usuario", width=220)
        self.entry_username.pack(pady=10, padx=25)

        self.entry_password = ctk.CTkEntry(self.login_frame, placeholder_text="Contraseña", show="*", width=220)
        self.entry_password.pack(pady=10, padx=25)

        self.btn_login = ctk.CTkButton(self.login_frame, text="Ingresar al Sistema", width=220, command=self.validar_login)
        self.btn_login.pack(pady=20, padx=25)
        
        self.label_error = ctk.CTkLabel(self.login_frame, text="", text_color="red")
        self.label_error.pack(pady=(0,10), padx=25)

    def validar_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        
        db = SessionLocal()
        user = db.query(Usuario).filter(Usuario.username == username, Usuario.password == password).first()
        db.close()
        
        if user:
            self.login_frame.destroy()
            self.mostrar_app_principal()
        else:
            self.label_error.configure(text="Credenciales inválidas")

    def mostrar_app_principal(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Configuración de estilos Treeview para integración institucional formal
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", 
            background="#0F172A",
            foreground="#E2E8F0",
            fieldbackground="#0F172A",
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading", 
            background="#1E293B",
            foreground="#F8FAFC",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(6, 8)
        )
        style.map("Treeview", 
                  background=[('selected', '#1E3A8A')],
                  foreground=[('selected', '#FFFFFF')])
        style.map("Treeview.Heading",
                  background=[('active', '#334155')])

        # 1. Barra Lateral de Navegación
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        fila_actual = 0
        if os.path.exists(LOGO_PATH):
            try:
                img_pil = Image.open(LOGO_PATH)
                self.logo_sidebar_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(65, 65))
                self.lbl_sidebar_logo = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_sidebar_img)
                self.lbl_sidebar_logo.grid(row=fila_actual, column=0, padx=20, pady=(15, 2))
                fila_actual += 1
            except Exception:
                pass

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SICE", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=fila_actual, column=0, padx=20, pady=(0, 15))
        fila_actual += 1

        self.btn_nav_tabla = ctk.CTkButton(
            self.sidebar_frame, text="📋 Matrícula de Alumnos", 
            command=lambda: self.cambiar_vista("alumnos"), anchor="w"
        )
        self.btn_nav_tabla.grid(row=fila_actual, column=0, padx=15, pady=6, sticky="ew")
        fila_actual += 1

        self.btn_nav_boletin = ctk.CTkButton(
            self.sidebar_frame, text="📄 Consulta de Boletín", 
            command=lambda: self.cambiar_vista("boletin"), anchor="w"
        )
        self.btn_nav_boletin.grid(row=fila_actual, column=0, padx=15, pady=6, sticky="ew")
        fila_actual += 1

        self.btn_nav_manual = ctk.CTkButton(
            self.sidebar_frame, text="✍️ Registro Manual", 
            command=lambda: self.cambiar_vista("manual"), anchor="w"
        )
        self.btn_nav_manual.grid(row=fila_actual, column=0, padx=15, pady=6, sticky="ew")
        fila_actual += 1

        self.btn_nav_excel = ctk.CTkButton(
            self.sidebar_frame, text="📊 Importar Excel", 
            command=lambda: self.cambiar_vista("excel"), anchor="w"
        )
        self.btn_nav_excel.grid(row=fila_actual, column=0, padx=15, pady=6, sticky="ew")

        # Fila flexible para empujar el panel web al fondo
        self.sidebar_frame.grid_rowconfigure(fila_actual + 1, weight=1)

        # Panel de Sincronización con la Nube
        cloud_box = ctk.CTkFrame(
            self.sidebar_frame, 
            fg_color="#0F172A", 
            corner_radius=8, 
            border_width=2, 
            border_color="#334155"
        )
        cloud_box.grid(row=fila_actual + 2, column=0, padx=12, pady=(10, 15), sticky="ew")
        cloud_box.grid_columnconfigure(0, weight=1)

        self.lbl_cloud_status = ctk.CTkLabel(
            cloud_box, 
            text="☁️ Portal en la Nube", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_cloud_status.grid(row=0, column=0, padx=10, pady=(8, 4))

        self.btn_sync_cloud = ctk.CTkButton(
            cloud_box,
            text="☁️ Sincronizar Portal Nube",
            fg_color="#0D9488",
            hover_color="#0F766E",
            command=self.iniciar_sincronizacion_nube
        )
        self.btn_sync_cloud.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        self.btn_abrir_web = ctk.CTkButton(
            cloud_box,
            text="🔗 Abrir Portal Web",
            fg_color="#1E293B",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            command=self.abrir_portal_en_navegador
        )
        self.btn_abrir_web.grid(row=2, column=0, padx=10, pady=(2, 8), sticky="ew")

        # 2. Contenedor Dinámico
        self.container_frame = ctk.CTkFrame(self, corner_radius=10)
        self.container_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.container_frame.grid_columnconfigure(0, weight=1)
        self.container_frame.grid_rowconfigure(0, weight=1)

        # Inicializar vistas
        self.vistas = {}
        self.crear_vista_alumnos()
        self.crear_vista_boletin()
        self.crear_vista_manual()
        self.crear_vista_excel()

        # Cargar datos en memoria y mostrar vista principal
        self.recargar_datos_desde_bd()
        self.cambiar_vista("alumnos")

    def cambiar_vista(self, nombre_vista):
        for nombre, frame in self.vistas.items():
            if nombre == nombre_vista:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        if nombre_vista == "alumnos":
            self.cargar_tabla_alumnos()

    # ------------------ OPTIMIZACIÓN DE DATOS EN MEMORIA ------------------
    def recargar_datos_desde_bd(self):
        """Carga todos los estudiantes en una sola consulta optimizada (Eager Loading)."""
        db = SessionLocal()
        try:
            alumnos = db.query(Alumno).options(
                joinedload(Alumno.representante),
                joinedload(Alumno.notas)
            ).all()

            self.cached_alumnos_data = []
            for alu in alumnos:
                rep_nom = f"{alu.representante.nombre} {alu.representante.apellido}" if alu.representante else "N/A"
                rep_tlf = alu.representante.telefono if alu.representante else "N/A"
                
                notas = alu.notas or []
                prom = sum(n.calificacion for n in notas) / len(notas) if notas else 0.0
                inas = getattr(alu, 'inasistencias', 0) or 0
                
                if inas > 4:
                    estado = "REPROBADO"
                elif notas and prom < 10.0:
                    estado = "REPROBADO"
                else:
                    estado = "APROBADO"

                self.cached_alumnos_data.append({
                    "cedula": alu.cedula,
                    "nombre": alu.nombre,
                    "apellido": alu.apellido,
                    "anio": alu.anio or "1er Año",
                    "seccion": alu.seccion or "A",
                    "inasist": inas,
                    "promedio": prom,
                    "estado": estado,
                    "rep_nombre": rep_nom,
                    "rep_tlf": rep_tlf,
                    "search_key": f"{alu.cedula} {alu.nombre} {alu.apellido} {rep_nom}".lower()
                })
        finally:
            db.close()

        if hasattr(self, 'tree_alumnos'):
            self.cargar_tabla_alumnos()

    # ------------------ VISTA PRINCIPAL: TABLA DE ALUMNOS ------------------
    def crear_vista_alumnos(self):
        frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        self.vistas["alumnos"] = frame

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Cabecera limpia (sin reglas invasivas)
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        lbl_titulo = ctk.CTkLabel(top_bar, text="Matrícula General de Estudiantes", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.grid(row=0, column=0, sticky="w")

        # Barra de búsqueda y filtros por nivel
        search_bar = ctk.CTkFrame(frame, fg_color="transparent")
        search_bar.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        search_bar.grid_columnconfigure(0, weight=1)

        self.entry_filtro = ctk.CTkEntry(
            search_bar, 
            placeholder_text="Filtrar por cédula, nombre o apellido...",
            border_width=2,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.entry_filtro.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry_filtro.bind("<KeyRelease>", lambda event: self.cargar_tabla_alumnos())

        # Filtro de Año
        self.filtro_anio = ctk.CTkOptionMenu(
            search_bar, 
            values=["Todos los Años", "1er Año", "2do Año", "3er Año", "4to Año", "5to Año"],
            width=130,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color="#475569",
            command=lambda x: self.cargar_tabla_alumnos()
        )
        self.filtro_anio.grid(row=0, column=1, padx=(0, 5), sticky="e")

        btn_refresh = ctk.CTkButton(
            search_bar, 
            text="🔄 Actualizar", 
            width=100, 
            border_width=2,
            border_color="#334155",
            fg_color="#1E293B",
            hover_color="#334155",
            command=self.recargar_datos_desde_bd
        )
        btn_refresh.grid(row=0, column=2, padx=(0, 5), sticky="e")

        btn_ver_boletin_sel = ctk.CTkButton(
            search_bar, 
            text="📄 Ver Boletín", 
            fg_color="#1E3A8A", 
            hover_color="#1D4ED8", 
            border_width=2,
            border_color="#2563EB",
            width=110, 
            command=self.abrir_boletin_seleccionado
        )
        btn_ver_boletin_sel.grid(row=0, column=3, padx=(0, 5), sticky="e")

        btn_editar_sel = ctk.CTkButton(
            search_bar,
            text="✏️ Editar Alumno",
            fg_color="#D97706",
            hover_color="#B45309",
            border_width=2,
            border_color="#F59E0B",
            width=120,
            command=self.abrir_modal_editar_alumno
        )
        btn_editar_sel.grid(row=0, column=4, sticky="e")

        # Contenedor de la Tabla con marco formal de 2px
        table_container = ctk.CTkFrame(
            frame, 
            fg_color="#0F172A", 
            corner_radius=6, 
            border_width=2, 
            border_color="#334155"
        )
        table_container.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        columnas = ("cedula", "nombres", "apellidos", "anio", "seccion", "inasist", "promedio", "estado", "rep_nombre", "rep_tlf")
        self.tree_alumnos = ttk.Treeview(table_container, columns=columnas, show="headings", selectmode="browse")

        self.tree_alumnos.heading("cedula", text="Cédula Alumno")
        self.tree_alumnos.heading("nombres", text="Nombres")
        self.tree_alumnos.heading("apellidos", text="Apellidos")
        self.tree_alumnos.heading("anio", text="Año")
        self.tree_alumnos.heading("seccion", text="Sec.")
        self.tree_alumnos.heading("inasist", text="Faltas")
        self.tree_alumnos.heading("promedio", text="Promedio")
        self.tree_alumnos.heading("estado", text="Condición")
        self.tree_alumnos.heading("rep_nombre", text="Representante")
        self.tree_alumnos.heading("rep_tlf", text="Teléfono Rep.")

        self.tree_alumnos.column("cedula", width=105, anchor="center")
        self.tree_alumnos.column("nombres", width=110, anchor="w")
        self.tree_alumnos.column("apellidos", width=110, anchor="w")
        self.tree_alumnos.column("anio", width=75, anchor="center")
        self.tree_alumnos.column("seccion", width=45, anchor="center")
        self.tree_alumnos.column("inasist", width=55, anchor="center")
        self.tree_alumnos.column("promedio", width=75, anchor="center")
        self.tree_alumnos.column("estado", width=100, anchor="center")
        self.tree_alumnos.column("rep_nombre", width=130, anchor="w")
        self.tree_alumnos.column("rep_tlf", width=110, anchor="center")

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree_alumnos.yview)
        scroll_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree_alumnos.xview)
        self.tree_alumnos.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree_alumnos.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree_alumnos.bind("<Double-1>", lambda event: self.abrir_boletin_seleccionado())

        # Configuración de filas alternadas formales
        self.tree_alumnos.tag_configure("fila_par", background="#0F172A")
        self.tree_alumnos.tag_configure("fila_impar", background="#182234")

    def cargar_tabla_alumnos(self):
        """Filtrado ultrarrápido ejecutado 100% en memoria RAM (< 1ms)."""
        for row in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(row)

        filtro_txt = self.entry_filtro.get().strip().lower() if hasattr(self, 'entry_filtro') else ""
        filtro_a = self.filtro_anio.get() if hasattr(self, 'filtro_anio') else "Todos los Años"

        for idx, item in enumerate(self.cached_alumnos_data):
            if filtro_a != "Todos los Años" and item["anio"] != filtro_a:
                continue
            if filtro_txt and filtro_txt not in item["search_key"]:
                continue

            tag_fila = "fila_par" if idx % 2 == 0 else "fila_impar"
            self.tree_alumnos.insert("", "end", values=(
                item["cedula"],
                item["nombre"],
                item["apellido"],
                item["anio"],
                item["seccion"],
                str(item["inasist"]),
                f"{item['promedio']:.2f} pts",
                item["estado"],
                item["rep_nombre"],
                item["rep_tlf"]
            ), tags=(tag_fila,))

    def abrir_boletin_seleccionado(self):
        seleccion = self.tree_alumnos.selection()
        if not seleccion:
            messagebox.showinfo("Información", "Selecciona un estudiante de la tabla.")
            return

        item = self.tree_alumnos.item(seleccion[0])
        cedula_seleccionada = item['values'][0]

        # Cambiar a vista de boletín y consultar automáticamente
        self.cambiar_vista("boletin")
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, str(cedula_seleccionada))
        self.buscar_alumno()

    def abrir_modal_editar_alumno(self):
        """Abre un modal para editar datos del estudiante y notas con doble verificación de cambios."""
        seleccion = self.tree_alumnos.selection()
        if not seleccion:
            messagebox.showinfo("Selección Requerida", "Por favor, seleccione un estudiante de la tabla para editar.")
            return

        item = self.tree_alumnos.item(seleccion[0])
        cedula_sel = str(item['values'][0]).strip()

        db = SessionLocal()
        try:
            alumno = db.query(Alumno).options(
                joinedload(Alumno.representante),
                joinedload(Alumno.notas).joinedload(Nota.materia)
            ).filter(Alumno.cedula == cedula_sel).first()

            if not alumno:
                messagebox.showerror("Error", f"No se encontró el estudiante con cédula {cedula_sel}.")
                return

            val_originales = {
                "nombre": alumno.nombre or "",
                "apellido": alumno.apellido or "",
                "anio": alumno.anio or "1er Año",
                "seccion": alumno.seccion or "A",
                "inasistencias": int(alumno.inasistencias or 0),
                "rep_nombre": alumno.representante.nombre if alumno.representante else "",
                "rep_apellido": alumno.representante.apellido if alumno.representante else "",
                "rep_telefono": alumno.representante.telefono if alumno.representante else "",
                "rep_correo": alumno.representante.correo if alumno.representante else "",
                "notas": {n.id_nota: (float(n.calificacion), n.materia.nombre if n.materia else "Materia", n.lapso) for n in alumno.notas}
            }

            modal = ctk.CTkToplevel(self)
            modal.title(f"Editar Estudiante - C.I. {alumno.cedula}")
            modal.geometry("640x680")
            modal.grab_set()
            modal.focus()

            modal.grid_columnconfigure(0, weight=1)
            modal.grid_rowconfigure(1, weight=1)

            header_frame = ctk.CTkFrame(modal, fg_color="#1E293B", corner_radius=0)
            header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            ctk.CTkLabel(
                header_frame, 
                text=f"✏️ Edición de Ficha Estudiantil — {alumno.cedula}", 
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#F8FAFC"
            ).pack(padx=20, pady=12, anchor="w")

            scroll_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
            scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
            scroll_frame.grid_columnconfigure((0, 1), weight=1)

            # 1. Datos del Alumno
            ctk.CTkLabel(scroll_frame, text="1. Datos del Estudiante", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38BDF8").grid(row=0, column=0, columnspan=2, sticky="w", pady=(5, 5))

            ctk.CTkLabel(scroll_frame, text="Nombres:").grid(row=1, column=0, sticky="w", padx=5)
            ctk.CTkLabel(scroll_frame, text="Apellidos:").grid(row=1, column=1, sticky="w", padx=5)
            e_nombre = ctk.CTkEntry(scroll_frame)
            e_nombre.insert(0, val_originales["nombre"])
            e_nombre.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 10))

            e_apellido = ctk.CTkEntry(scroll_frame)
            e_apellido.insert(0, val_originales["apellido"])
            e_apellido.grid(row=2, column=1, sticky="ew", padx=5, pady=(0, 10))

            ctk.CTkLabel(scroll_frame, text="Año / Grado:").grid(row=3, column=0, sticky="w", padx=5)
            f_sec_inas = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            f_sec_inas.grid(row=3, column=1, rowspan=2, sticky="ew", padx=5)
            f_sec_inas.grid_columnconfigure((0, 1), weight=1)
            ctk.CTkLabel(f_sec_inas, text="Sección:").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(f_sec_inas, text="Inasistencias:").grid(row=0, column=1, sticky="w", padx=(5, 0))

            opt_anio = ctk.CTkOptionMenu(scroll_frame, values=["1er Año", "2do Año", "3er Año", "4to Año", "5to Año"])
            opt_anio.set(val_originales["anio"])
            opt_anio.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 10))

            opt_seccion = ctk.CTkOptionMenu(f_sec_inas, values=["A", "B", "C", "D", "U"], width=80)
            opt_seccion.set(val_originales["seccion"])
            opt_seccion.grid(row=1, column=0, sticky="ew", pady=(0, 10))

            e_inasist = ctk.CTkEntry(f_sec_inas, width=80)
            e_inasist.insert(0, str(val_originales["inasistencias"]))
            e_inasist.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))

            # 2. Representante
            ctk.CTkLabel(scroll_frame, text="2. Datos del Representante", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38BDF8").grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 5))

            ctk.CTkLabel(scroll_frame, text="Nombre Rep.:").grid(row=6, column=0, sticky="w", padx=5)
            ctk.CTkLabel(scroll_frame, text="Apellido Rep.:").grid(row=6, column=1, sticky="w", padx=5)
            e_rep_nom = ctk.CTkEntry(scroll_frame)
            e_rep_nom.insert(0, val_originales["rep_nombre"])
            e_rep_nom.grid(row=7, column=0, sticky="ew", padx=5, pady=(0, 10))

            e_rep_ape = ctk.CTkEntry(scroll_frame)
            e_rep_ape.insert(0, val_originales["rep_apellido"])
            e_rep_ape.grid(row=7, column=1, sticky="ew", padx=5, pady=(0, 10))

            ctk.CTkLabel(scroll_frame, text="Teléfono Rep.:").grid(row=8, column=0, sticky="w", padx=5)
            ctk.CTkLabel(scroll_frame, text="Correo Electrónico:").grid(row=8, column=1, sticky="w", padx=5)
            e_rep_tlf = ctk.CTkEntry(scroll_frame)
            e_rep_tlf.insert(0, val_originales["rep_telefono"])
            e_rep_tlf.grid(row=9, column=0, sticky="ew", padx=5, pady=(0, 10))

            e_rep_cor = ctk.CTkEntry(scroll_frame)
            e_rep_cor.insert(0, val_originales["rep_correo"])
            e_rep_cor.grid(row=9, column=1, sticky="ew", padx=5, pady=(0, 10))

            # 3. Calificaciones
            entradas_notas = {}
            if val_originales["notas"]:
                ctk.CTkLabel(scroll_frame, text="3. Calificaciones Registradas", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38BDF8").grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 5))
                f_notas = ctk.CTkFrame(scroll_frame, fg_color="#0F172A", corner_radius=6, border_width=1, border_color="#334155")
                f_notas.grid(row=11, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
                f_notas.grid_columnconfigure(0, weight=2)
                f_notas.grid_columnconfigure((1, 2), weight=1)

                ctk.CTkLabel(f_notas, text="Materia", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=4, sticky="w")
                ctk.CTkLabel(f_notas, text="Lapso", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=8, pady=4)
                ctk.CTkLabel(f_notas, text="Nota (0-20)", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, padx=8, pady=4)

                for r_idx, (id_n, (nota_val, mat_nom, lapso)) in enumerate(val_originales["notas"].items(), start=1):
                    ctk.CTkLabel(f_notas, text=mat_nom).grid(row=r_idx, column=0, padx=8, pady=2, sticky="w")
                    ctk.CTkLabel(f_notas, text=f"Lapso {lapso}").grid(row=r_idx, column=1, padx=8, pady=2)
                    e_n = ctk.CTkEntry(f_notas, width=70, justify="center")
                    e_n.insert(0, f"{nota_val:.2f}")
                    e_n.grid(row=r_idx, column=2, padx=8, pady=2)
                    entradas_notas[id_n] = e_n

            btn_box = ctk.CTkFrame(modal, fg_color="#1E293B", corner_radius=0)
            btn_box.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
            btn_box.grid_columnconfigure(0, weight=1)

            def guardar_con_doble_verificacion():
                nvo_nombre = e_nombre.get().strip()
                nvo_apellido = e_apellido.get().strip()
                nvo_anio = opt_anio.get()
                nvo_seccion = opt_seccion.get()
                
                try:
                    nvo_inasist = int(e_inasist.get().strip())
                    if nvo_inasist < 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Dato Inválido", "Las inasistencias deben ser un número entero mayor o igual a 0.", parent=modal)
                    return

                nvo_rep_nom = e_rep_nom.get().strip()
                nvo_rep_ape = e_rep_ape.get().strip()
                nvo_rep_tlf = e_rep_tlf.get().strip()
                nvo_rep_cor = e_rep_cor.get().strip()

                nuevas_notas = {}
                for id_n, widget_n in entradas_notas.items():
                    try:
                        val_f = float(widget_n.get().strip())
                        if not (0.0 <= val_f <= 20.0):
                            raise ValueError()
                        nuevas_notas[id_n] = val_f
                    except ValueError:
                        messagebox.showerror("Nota Inválida", "La calificación debe ser un número entre 0.00 y 20.00.", parent=modal)
                        return

                cambios = []
                if nvo_nombre != val_originales["nombre"]:
                    cambios.append(f"• Nombre: '{val_originales['nombre']}' ➔ '{nvo_nombre}'")
                if nvo_apellido != val_originales["apellido"]:
                    cambios.append(f"• Apellido: '{val_originales['apellido']}' ➔ '{nvo_apellido}'")
                if nvo_anio != val_originales["anio"]:
                    cambios.append(f"• Año: '{val_originales['anio']}' ➔ '{nvo_anio}'")
                if nvo_seccion != val_originales["seccion"]:
                    cambios.append(f"• Sección: '{val_originales['seccion']}' ➔ '{nvo_seccion}'")
                if nvo_inasist != val_originales["inasistencias"]:
                    cambios.append(f"• Inasistencias: {val_originales['inasistencias']} ➔ {nvo_inasist}")
                if nvo_rep_nom != val_originales["rep_nombre"]:
                    cambios.append(f"• Nombre Rep.: '{val_originales['rep_nombre']}' ➔ '{nvo_rep_nom}'")
                if nvo_rep_ape != val_originales["rep_apellido"]:
                    cambios.append(f"• Apellido Rep.: '{val_originales['rep_apellido']}' ➔ '{nvo_rep_ape}'")
                if nvo_rep_tlf != val_originales["rep_telefono"]:
                    cambios.append(f"• Teléfono Rep.: '{val_originales['rep_telefono']}' ➔ '{nvo_rep_tlf}'")
                if nvo_rep_cor != val_originales["rep_correo"]:
                    cambios.append(f"• Correo Rep.: '{val_originales['rep_correo']}' ➔ '{nvo_rep_cor}'")

                for id_n, nva_calif in nuevas_notas.items():
                    orig_calif, mat_nom, lapso = val_originales["notas"][id_n]
                    if abs(nva_calif - orig_calif) > 0.001:
                        cambios.append(f"• {mat_nom} (Lapso {lapso}): {orig_calif:.2f} ➔ {nva_calif:.2f}")

                if not cambios:
                    messagebox.showinfo("Sin Cambios", "No se detectó ninguna modificación respecto a los valores actuales.", parent=modal)
                    return

                lista_cambios_str = "\n".join(cambios)
                msj_confirmacion = (
                    f"¿Está completamente seguro(a) de aplicar las siguientes modificaciones?\n\n"
                    f"Estudiante: {val_originales['nombre']} {val_originales['apellido']} (C.I. {cedula_sel})\n\n"
                    f"CAMBIOS DETECTADOS:\n{lista_cambios_str}\n\n"
                    f"⚠️ ADVERTENCIA: Esta acción actualizará los registros oficiales en la base de datos."
                )

                confirmado = messagebox.askyesno("Doble Verificación - Confirmar Modificación", msj_confirmacion, parent=modal)
                if not confirmado:
                    return

                db_write = SessionLocal()
                try:
                    alu_up = db_write.query(Alumno).filter(Alumno.cedula == cedula_sel).first()
                    if not alu_up:
                        messagebox.showerror("Error", "No se encontró el registro para actualizar.", parent=modal)
                        return

                    alu_up.nombre = nvo_nombre
                    alu_up.apellido = nvo_apellido
                    alu_up.anio = nvo_anio
                    alu_up.seccion = nvo_seccion
                    alu_up.inasistencias = nvo_inasist

                    if alu_up.representante:
                        alu_up.representante.nombre = nvo_rep_nom
                        alu_up.representante.apellido = nvo_rep_ape
                        alu_up.representante.telefono = nvo_rep_tlf
                        alu_up.representante.correo = nvo_rep_cor

                    for id_n, nva_calif in nuevas_notas.items():
                        nota_up = db_write.query(Nota).filter(Nota.id_nota == id_n).first()
                        if nota_up:
                            nota_up.calificacion = nva_calif

                    db_write.commit()
                    messagebox.showinfo("Modificación Exitosa", "Los datos fueron actualizados correctamente en la base de datos.", parent=modal)
                    modal.destroy()
                    self.recargar_datos_desde_bd()
                except Exception as ex:
                    db_write.rollback()
                    messagebox.showerror("Error de Base de Datos", f"No se pudieron guardar los cambios:\n{str(ex)}", parent=modal)
                finally:
                    db_write.close()

            btn_cancelar = ctk.CTkButton(
                btn_box, 
                text="Cancelar", 
                fg_color="#334155", 
                hover_color="#475569", 
                command=modal.destroy,
                width=100
            )
            btn_cancelar.pack(side="right", padx=(5, 20), pady=12)

            btn_guardar = ctk.CTkButton(
                btn_box, 
                text="💾 Guardar Modificaciones", 
                fg_color="#16A34A", 
                hover_color="#15803D",
                font=ctk.CTkFont(weight="bold"),
                command=guardar_con_doble_verificacion,
                width=180
            )
            btn_guardar.pack(side="right", padx=5, pady=12)

        finally:
            db.close()

    # ------------------ VISTA 2: CONSULTA DE BOLETÍN ------------------
    def crear_vista_boletin(self):
        frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        self.vistas["boletin"] = frame

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        lbl_titulo = ctk.CTkLabel(frame, text="Consulta de Boletín y Promedios", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        lbl_sub = ctk.CTkLabel(frame, text="Ingresa la cédula del estudiante registrado:")
        lbl_sub.grid(row=1, column=0, padx=20, pady=2, sticky="w")

        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.entry_cedula = ctk.CTkEntry(search_frame, placeholder_text="Ej: V-30123456")
        self.entry_cedula.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.btn_buscar = ctk.CTkButton(search_frame, text="Consultar", command=self.buscar_alumno, width=120)
        self.btn_buscar.grid(row=0, column=1, sticky="e")

        self.textbox_resultado = ctk.CTkTextbox(frame, height=270)
        self.textbox_resultado.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # Opciones de Acción Separadas
        actions_frame = ctk.CTkFrame(frame, fg_color="#1E293B", corner_radius=8)
        actions_frame.grid(row=4, column=0, padx=20, pady=(5, 10), sticky="ew")
        actions_frame.grid_columnconfigure((0, 1), weight=1)

        # Opción 1: Guardar local en PC
        self.btn_exportar_pdf = ctk.CTkButton(
            actions_frame, 
            text="📥 Guardar / Descargar PDF en PC", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB", 
            hover_color="#1D4ED8", 
            height=38,
            command=self.exportar_pdf
        )
        self.btn_exportar_pdf.grid(row=0, column=0, padx=(15, 10), pady=12, sticky="ew")

        # Opción 2: Enviar por Correo
        self.btn_enviar = ctk.CTkButton(
            actions_frame, 
            text="✉️ Enviar Boletín por Correo", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#16A34A", 
            hover_color="#15803D", 
            height=38,
            command=self.enviar_correo
        )
        self.btn_enviar.grid(row=0, column=1, padx=(10, 15), pady=12, sticky="ew")

    # ------------------ VISTA 3: REGISTRO MANUAL ------------------
    def crear_vista_manual(self):
        frame = ctk.CTkScrollableFrame(self.container_frame, fg_color="transparent")
        self.vistas["manual"] = frame
        frame.grid_columnconfigure((0, 1), weight=1)

        lbl_titulo = ctk.CTkLabel(frame, text="Registro Manual de Alumno", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 15), sticky="w")

        # 1. Sección Estudiante
        lbl_sec1 = ctk.CTkLabel(frame, text="Datos del Alumno", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B82F6")
        lbl_sec1.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 5), sticky="w")

        self.m_cedula_alu = ctk.CTkEntry(frame, placeholder_text="Cédula Alumno (Ej: V-30123456)")
        self.m_cedula_alu.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.m_fec_nac = ctk.CTkEntry(frame, placeholder_text="Fecha Nacimiento (DD-MM-AAAA)")
        self.m_fec_nac.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.m_nombre_alu = ctk.CTkEntry(frame, placeholder_text="Nombres del Alumno")
        self.m_nombre_alu.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.m_apellido_alu = ctk.CTkEntry(frame, placeholder_text="Apellidos del Alumno")
        self.m_apellido_alu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Nivel e Inasistencias
        nivel_container = ctk.CTkFrame(frame, fg_color="transparent")
        nivel_container.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        nivel_container.grid_columnconfigure((0, 1, 2), weight=1)

        lbl_anio = ctk.CTkLabel(nivel_container, text="Año / Grado:")
        lbl_anio.grid(row=0, column=0, padx=5, sticky="w")
        self.m_anio = ctk.CTkOptionMenu(
            nivel_container, 
            values=["1er Año", "2do Año", "3er Año", "4to Año", "5to Año"]
        )
        self.m_anio.set("1er Año")
        self.m_anio.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        lbl_sec = ctk.CTkLabel(nivel_container, text="Sección:")
        lbl_sec.grid(row=0, column=1, padx=5, sticky="w")
        self.m_seccion = ctk.CTkOptionMenu(
            nivel_container, 
            values=["A", "B", "C", "D", "U"]
        )
        self.m_seccion.set("A")
        self.m_seccion.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        lbl_inasist = ctk.CTkLabel(nivel_container, text="Inasistencias:")
        lbl_inasist.grid(row=0, column=2, padx=5, sticky="w")
        self.m_inasistencias = ctk.CTkEntry(nivel_container, placeholder_text="0")
        self.m_inasistencias.insert(0, "0")
        self.m_inasistencias.grid(row=1, column=2, padx=5, pady=2, sticky="ew")

        # 2. Sección Representante
        lbl_sec2 = ctk.CTkLabel(frame, text="Datos del Representante", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B82F6")
        lbl_sec2.grid(row=5, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")

        self.m_cedula_rep = ctk.CTkEntry(frame, placeholder_text="Cédula Representante (Ej: V-15444555)")
        self.m_cedula_rep.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        # Teléfono con selector de código (0412, 0414, 0424, 0416, 0426)
        tlf_container = ctk.CTkFrame(frame, fg_color="transparent")
        tlf_container.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        tlf_container.grid_columnconfigure(1, weight=1)

        self.m_cod_tlf = ctk.CTkOptionMenu(tlf_container, values=["0412", "0414", "0424", "0416", "0426"], width=85)
        self.m_cod_tlf.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.m_num_tlf = ctk.CTkEntry(tlf_container, placeholder_text="Teléfono (7 dígitos)")
        self.m_num_tlf.grid(row=0, column=1, sticky="ew")

        self.m_nombre_rep = ctk.CTkEntry(frame, placeholder_text="Nombres del Representante")
        self.m_nombre_rep.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

        self.m_apellido_rep = ctk.CTkEntry(frame, placeholder_text="Apellidos del Representante")
        self.m_apellido_rep.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

        self.m_correo_rep = ctk.CTkEntry(frame, placeholder_text="Correo Electrónico del Representante")
        self.m_correo_rep.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        btn_guardar_manual = ctk.CTkButton(
            frame, text="💾 Registrar Estudiante en el Liceo", fg_color="#2563EB", hover_color="#1D4ED8",
            height=40, font=ctk.CTkFont(size=13, weight="bold"), command=self.guardar_alumno_manual
        )
        btn_guardar_manual.grid(row=9, column=0, columnspan=2, padx=10, pady=(25, 20), sticky="ew")

    # ------------------ VISTA 4: IMPORTAR EXCEL ------------------
    def crear_vista_excel(self):
        frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        self.vistas["excel"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        lbl_titulo = ctk.CTkLabel(frame, text="Carga Masiva de Matrícula (Excel)", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        lbl_desc = ctk.CTkLabel(
            frame, 
            text="Puedes importar cientos de alumnos al instante mediante un archivo Excel (.xlsx).\n"
                 "Incluye columnas de Año, Sección e Inasistencias para procesar estados académicos.",
            justify="left"
        )
        lbl_desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        excel_actions = ctk.CTkFrame(frame, fg_color="transparent")
        excel_actions.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        excel_actions.grid_columnconfigure((0, 1), weight=1)

        btn_plantilla = ctk.CTkButton(
            excel_actions, text="📥 Descargar Plantilla Excel", 
            fg_color="#4B5563", hover_color="#374151", command=self.descargar_plantilla
        )
        btn_plantilla.grid(row=0, column=0, padx=5, sticky="ew")

        btn_seleccionar = ctk.CTkButton(
            excel_actions, text="📂 Seleccionar Archivo e Importar", 
            fg_color="#059669", hover_color="#047857", command=self.procesar_excel
        )
        btn_seleccionar.grid(row=0, column=1, padx=5, sticky="ew")

        self.textbox_excel_log = ctk.CTkTextbox(frame, height=280)
        self.textbox_excel_log.grid(row=3, column=0, padx=20, pady=(15, 10), sticky="nsew")
        self.textbox_excel_log.insert("0.0", "Registro de eventos de importación:\nListo para cargar archivos Excel.\n")

    # ------------------ EVENTOS Y LÓGICA ------------------
    def buscar_alumno(self):
        cedula = self.entry_cedula.get().strip()
        if cedula:
            boletin = obtener_boletin_texto(cedula)
            self.textbox_resultado.delete("0.0", "end")
            self.textbox_resultado.insert("0.0", boletin)
        else:
            messagebox.showwarning("Atención", "Ingresa una cédula válida.")

    def exportar_pdf(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Atención", "Por favor ingresa la cédula del estudiante.")
            return

        nombre_sugerido = f"Boletin_{cedula.replace('-', '_')}.pdf"
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")],
            initialfile=nombre_sugerido,
            title="Guardar Boletín de Calificaciones en PDF"
        )

        if ruta_archivo:
            exito = generar_boletin_pdf(cedula, ruta_archivo)
            if exito:
                self.textbox_resultado.insert("end", f"\n\n[ÉXITO] PDF guardado en:\n{ruta_archivo}")
                messagebox.showinfo("Éxito", f"El archivo PDF se ha guardado correctamente en:\n{ruta_archivo}")
            else:
                self.textbox_resultado.insert("end", "\n\n[ERROR] No se pudo generar el PDF (alumno no encontrado).")
                messagebox.showerror("Error", "No se encontró el alumno especificado.")

    def enviar_correo(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Atención", "Ingresa la cédula del estudiante.")
            return
            
        exito = enviar_boletin_correo(cedula)
        if exito:
            self.textbox_resultado.insert("end", "\n\n[INFO] Intento de envío de correo finalizado.")
            messagebox.showinfo("Correo", "Proceso de envío de correo completado.")
        else:
            self.textbox_resultado.insert("end", "\n\n[ERROR] No se pudo enviar el correo.")
            messagebox.showerror("Error", "Alumno o representante no encontrado.")

    def guardar_alumno_manual(self):
        cedula_alu = self.m_cedula_alu.get().strip()
        nombre_alu = self.m_nombre_alu.get().strip()
        apellido_alu = self.m_apellido_alu.get().strip()
        fec_nac = self.m_fec_nac.get().strip()
        anio_alu = self.m_anio.get().strip()
        seccion_alu = self.m_seccion.get().strip()
        
        try:
            inasistencias_val = int(self.m_inasistencias.get().strip() or 0)
        except ValueError:
            inasistencias_val = 0

        cedula_rep = self.m_cedula_rep.get().strip()
        nombre_rep = self.m_nombre_rep.get().strip()
        apellido_rep = self.m_apellido_rep.get().strip()
        
        num_tlf_puro = self.m_num_tlf.get().strip()
        cod_tlf = self.m_cod_tlf.get().strip()
        tlf_rep = f"{cod_tlf}-{num_tlf_puro}" if num_tlf_puro else ""
        
        correo_rep = self.m_correo_rep.get().strip()

        # Ubicación institucional por defecto para el Liceo Gran Cacique Guaicaipuro
        estado = "La Guaira"
        municipio = "Vargas"
        parroquia = "Catia La Mar"
        detalle_dir = "Ciudad Caribia - Sector II"

        if not cedula_alu or not nombre_alu or not apellido_alu or not cedula_rep:
            messagebox.showwarning("Campos Requeridos", "Por favor completa los campos principales (Cédula, Nombre del Alumno y Cédula del Representante).")
            return

        ok, msg = registrar_alumno_manual(
            cedula_alumno=cedula_alu,
            nombre_alumno=nombre_alu,
            apellido_alumno=apellido_alu,
            fecha_nacimiento=fec_nac,
            anio=anio_alu,
            seccion=seccion_alu,
            inasistencias=inasistencias_val,
            cedula_rep=cedula_rep,
            nombre_rep=nombre_rep,
            apellido_rep=apellido_rep,
            telefono_rep=tlf_rep,
            correo_rep=correo_rep,
            estado=estado,
            municipio=municipio,
            parroquia=parroquia,
            detalle_dir=detalle_dir
        )

        if ok:
            messagebox.showinfo("Éxito", msg)
            # Limpiar campos
            self.m_cedula_alu.delete(0, "end")
            self.m_nombre_alu.delete(0, "end")
            self.m_apellido_alu.delete(0, "end")
            self.m_fec_nac.delete(0, "end")
            self.m_inasistencias.delete(0, "end")
            self.m_inasistencias.insert(0, "0")
            self.m_cedula_rep.delete(0, "end")
            self.m_nombre_rep.delete(0, "end")
            self.m_apellido_rep.delete(0, "end")
            self.m_num_tlf.delete(0, "end")
            self.m_correo_rep.delete(0, "end")
            self.recargar_datos_desde_bd()
        else:
            messagebox.showerror("Error", msg)

    def descargar_plantilla(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel (*.xlsx)", "*.xlsx")],
            initialfile="Plantilla_Matricula_SICE.xlsx",
            title="Guardar Plantilla de Importación Excel"
        )
        if ruta:
            generar_plantilla_excel(ruta)
            messagebox.showinfo("Plantilla Generada", f"Plantilla Excel guardada exitosamente en:\n{ruta}")

    def procesar_excel(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Archivos Excel (*.xlsx)", "*.xlsx")],
            title="Seleccionar Matrícula Escolar Excel"
        )
        if not ruta:
            return

        self.textbox_excel_log.delete("0.0", "end")
        self.textbox_excel_log.insert("end", f"Iniciando importación desde: {ruta}\n" + "-"*50 + "\n")

        exitosos, fallidos, mensajes = importar_alumnos_excel(ruta)

        self.textbox_excel_log.insert("end", f"Registros procesados con éxito: {exitosos}\n")
        self.textbox_excel_log.insert("end", f"Registros con error / duplicados: {fallidos}\n")
        
        if mensajes:
            self.textbox_excel_log.insert("end", "\nDetalles / Errores:\n")
            for m in mensajes:
                self.textbox_excel_log.insert("end", f"- {m}\n")

        messagebox.showinfo("Importación Finalizada", f"Proceso concluido.\nExitosos: {exitosos}\nFallidos/Duplicados: {fallidos}")
        self.recargar_datos_desde_bd()

    # ------------------ GESTIÓN DEL PORTAL EN LA NUBE ------------------
    def abrir_portal_en_navegador(self):
        import webbrowser
        import json
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_config.json")
        portal_url = "https://alexipalacio.pythonanywhere.com"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    portal_url = json.load(f).get("portal_url", portal_url)
            except Exception:
                pass
        webbrowser.open(portal_url)

    def iniciar_sincronizacion_nube(self):
        import json
        import requests
        import threading
        from database.models import DB_PATH
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_config.json")
        portal_url = "http://localhost:8000"
        sync_token = "sice_secret_sync_token_2026"
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    portal_url = cfg.get("portal_url", portal_url).rstrip("/")
                    sync_token = cfg.get("sync_token", sync_token)
            except Exception:
                pass
                
        confirmar = messagebox.askyesno(
            "Sincronizar Portal",
            f"¿Desea sincronizar la base de datos local con el portal web?\n\nDestino: {portal_url}"
        )
        if not confirmar:
            return

        self.btn_sync_cloud.configure(text="⏳ Sincronizando...", state="disabled")

        def sincronizar():
            try:
                if not os.path.exists(DB_PATH):
                    raise Exception(f"No se encontró el archivo de base de datos en: {DB_PATH}")

                url_endpoint = f"{portal_url}/admin/sync-db"
                headers = {"x-sync-token": sync_token}
                
                with open(DB_PATH, "rb") as f:
                    files = {"file": ("sice.db", f, "application/octet-stream")}
                    resp = requests.post(url_endpoint, headers=headers, files=files, timeout=60)

                if resp.status_code == 200:
                    self.after(0, lambda: messagebox.showinfo(
                        "Sincronización Exitosa", 
                        "La base de datos y notas se han sincronizado correctamente con el portal web."
                    ))
                elif resp.status_code == 401:
                    self.after(0, lambda: messagebox.showerror(
                        "Error de Autenticación",
                        "El token de sincronización configurado en 'sync_config.json' no coincide con el del servidor."
                    ))
                else:
                    detalle = resp.text
                    try:
                        detalle = resp.json().get("detail", detalle)
                    except Exception:
                        pass
                    self.after(0, lambda d=detalle: messagebox.showerror(
                        "Error en Servidor",
                        f"El servidor respondió con código {resp.status_code}:\n{d}"
                    ))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Error de Conexión",
                    f"No se pudo completar la sincronización:\n{err}"
                ))
            finally:
                self.after(0, lambda: self.btn_sync_cloud.configure(
                    text="☁️ Sincronizar Portal Nube", state="normal"
                ))

        threading.Thread(target=sincronizar, daemon=True).start()

    def cerrar_aplicacion(self):
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()

