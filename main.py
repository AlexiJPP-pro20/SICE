import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import init_db, SessionLocal, Usuario, Alumno
from core.promedios import obtener_boletin_texto
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

        # Configuración de ventana
        self.title("SICE - Sistema Integral de Control Estudiantil")
        self.geometry("1050x700")
        
        self.mostrar_login()

    def mostrar_login(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=10)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.login_label = ctk.CTkLabel(self.login_frame, text="SICE - Iniciar Sesión", font=ctk.CTkFont(size=20, weight="bold"))
        self.login_label.pack(pady=20, padx=25)

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

        # Configuración de estilos Treeview para integración estética
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", 
            background="#1E293B",
            foreground="#F8FAFC",
            fieldbackground="#1E293B",
            rowheight=32,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading", 
            background="#0F172A",
            foreground="#38BDF8",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview", background=[('selected', '#2563EB')])

        # 1. Barra Lateral de Navegación
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SICE", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 15))

        self.btn_nav_tabla = ctk.CTkButton(
            self.sidebar_frame, text="📋 Matrícula de Alumnos", 
            command=lambda: self.cambiar_vista("alumnos"), anchor="w"
        )
        self.btn_nav_tabla.grid(row=1, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_boletin = ctk.CTkButton(
            self.sidebar_frame, text="📄 Consulta de Boletín", 
            command=lambda: self.cambiar_vista("boletin"), anchor="w"
        )
        self.btn_nav_boletin.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_manual = ctk.CTkButton(
            self.sidebar_frame, text="✍️ Registro Manual", 
            command=lambda: self.cambiar_vista("manual"), anchor="w"
        )
        self.btn_nav_manual.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_excel = ctk.CTkButton(
            self.sidebar_frame, text="📊 Importar Excel", 
            command=lambda: self.cambiar_vista("excel"), anchor="w"
        )
        self.btn_nav_excel.grid(row=4, column=0, padx=15, pady=6, sticky="ew")

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

        # Mostrar tabla de alumnos por defecto tras iniciar sesión
        self.cambiar_vista("alumnos")

    def cambiar_vista(self, nombre_vista):
        for nombre, frame in self.vistas.items():
            if nombre == nombre_vista:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        if nombre_vista == "alumnos":
            self.cargar_tabla_alumnos()

    # ------------------ VISTA PRINCIPAL: TABLA DE ALUMNOS ------------------
    def crear_vista_alumnos(self):
        frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        self.vistas["alumnos"] = frame

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Cabecera y Filtros
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        lbl_titulo = ctk.CTkLabel(top_bar, text="Matrícula General de Estudiantes", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.grid(row=0, column=0, sticky="w")

        lbl_info = ctk.CTkLabel(top_bar, text="Doble clic en un estudiante para consultar su boletín directamente", text_color="#94A3B8")
        lbl_info.grid(row=1, column=0, sticky="w")

        # Barra de búsqueda y filtros por nivel
        search_bar = ctk.CTkFrame(frame, fg_color="transparent")
        search_bar.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        search_bar.grid_columnconfigure(0, weight=1)

        self.entry_filtro = ctk.CTkEntry(search_bar, placeholder_text="Filtrar por cédula, nombre o apellido...")
        self.entry_filtro.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry_filtro.bind("<KeyRelease>", lambda event: self.cargar_tabla_alumnos())

        # Filtro de Año
        self.filtro_anio = ctk.CTkOptionMenu(
            search_bar, 
            values=["Todos los Años", "1er Año", "2do Año", "3er Año", "4to Año", "5to Año"],
            width=130,
            command=lambda x: self.cargar_tabla_alumnos()
        )
        self.filtro_anio.grid(row=0, column=1, padx=(0, 5), sticky="e")

        btn_refresh = ctk.CTkButton(search_bar, text="🔄 Actualizar", width=100, command=self.cargar_tabla_alumnos)
        btn_refresh.grid(row=0, column=2, padx=(0, 5), sticky="e")

        btn_ver_boletin_sel = ctk.CTkButton(
            search_bar, text="📄 Ver Boletín", fg_color="#2563EB", hover_color="#1D4ED8", width=110, command=self.abrir_boletin_seleccionado
        )
        btn_ver_boletin_sel.grid(row=0, column=3, sticky="e")

        # Contenedor de la Tabla (Treeview)
        table_container = ctk.CTkFrame(frame, fg_color="#1E293B", corner_radius=8)
        table_container.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        columnas = ("cedula", "nombres", "apellidos", "anio", "seccion", "fec_nac", "rep_cedula", "rep_nombre", "rep_tlf")
        self.tree_alumnos = ttk.Treeview(table_container, columns=columnas, show="headings", selectmode="browse")

        self.tree_alumnos.heading("cedula", text="Cédula Alumno")
        self.tree_alumnos.heading("nombres", text="Nombres")
        self.tree_alumnos.heading("apellidos", text="Apellidos")
        self.tree_alumnos.heading("anio", text="Año")
        self.tree_alumnos.heading("seccion", text="Sec.")
        self.tree_alumnos.heading("fec_nac", text="Fecha Nac.")
        self.tree_alumnos.heading("rep_cedula", text="Cédula Rep.")
        self.tree_alumnos.heading("rep_nombre", text="Representante")
        self.tree_alumnos.heading("rep_tlf", text="Teléfono Rep.")

        self.tree_alumnos.column("cedula", width=105, anchor="center")
        self.tree_alumnos.column("nombres", width=120, anchor="w")
        self.tree_alumnos.column("apellidos", width=120, anchor="w")
        self.tree_alumnos.column("anio", width=80, anchor="center")
        self.tree_alumnos.column("seccion", width=50, anchor="center")
        self.tree_alumnos.column("fec_nac", width=95, anchor="center")
        self.tree_alumnos.column("rep_cedula", width=100, anchor="center")
        self.tree_alumnos.column("rep_nombre", width=140, anchor="w")
        self.tree_alumnos.column("rep_tlf", width=110, anchor="center")

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree_alumnos.yview)
        scroll_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree_alumnos.xview)
        self.tree_alumnos.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree_alumnos.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree_alumnos.bind("<Double-1>", lambda event: self.abrir_boletin_seleccionado())

    def cargar_tabla_alumnos(self):
        for row in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(row)

        filtro_txt = self.entry_filtro.get().strip().lower() if hasattr(self, 'entry_filtro') else ""
        filtro_a = self.filtro_anio.get() if hasattr(self, 'filtro_anio') else "Todos los Años"

        db = SessionLocal()
        try:
            query = db.query(Alumno)
            if filtro_a != "Todos los Años":
                query = query.filter(Alumno.anio == filtro_a)
            
            alumnos = query.all()
            for alu in alumnos:
                rep_nom = f"{alu.representante.nombre} {alu.representante.apellido}" if alu.representante else "N/A"
                rep_ced = alu.representante.cedula if alu.representante else "N/A"
                rep_tlf = alu.representante.telefono if alu.representante else "N/A"
                fec_nac = alu.fecha_nacimiento or "-"
                anio_val = alu.anio or "1er Año"
                sec_val = alu.seccion or "A"

                match = (
                    not filtro_txt or 
                    filtro_txt in alu.cedula.lower() or 
                    filtro_txt in alu.nombre.lower() or 
                    filtro_txt in alu.apellido.lower() or
                    filtro_txt in rep_nom.lower()
                )

                if match:
                    self.tree_alumnos.insert("", "end", values=(
                        alu.cedula,
                        alu.nombre,
                        alu.apellido,
                        anio_val,
                        sec_val,
                        fec_nac,
                        rep_ced,
                        rep_nom,
                        rep_tlf
                    ))
        finally:
            db.close()

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

        # Nivel: Año y Sección
        nivel_container = ctk.CTkFrame(frame, fg_color="transparent")
        nivel_container.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        nivel_container.grid_columnconfigure((0, 1), weight=1)

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
                 "La plantilla incluye Año (1ero a 5to) y Sección para organizar los niveles estudiantiles.",
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
            self.m_cedula_rep.delete(0, "end")
            self.m_nombre_rep.delete(0, "end")
            self.m_apellido_rep.delete(0, "end")
            self.m_num_tlf.delete(0, "end")
            self.m_correo_rep.delete(0, "end")
            self.cargar_tabla_alumnos()
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
        self.cargar_tabla_alumnos()

if __name__ == "__main__":
    app = App()
    app.mainloop()
