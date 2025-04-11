import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pol import Pol
from funciones import fetch_data, add_data, delete_data, update_data

class BibliotecaApp:
    def __init__(self, root, db_connection):
        self.root = root
        self.root.title("Gestión de Biblioteca Universitaria")
        self.root.geometry("1000x700")
        self.db_connection = db_connection
        self.pol = Pol()  # Instanciamos la clase Pol
        self.create_main_menu()

    def create_action_interface(self, action, table_name, columns, id_column):
        if self.db_connection.current_role == 'GERENTE' and action != 'visualizar':
            messagebox.showerror("Acceso denegado", "Su rol solo permite visualización")
            return
            
        if self.db_connection.current_role == 'VENDEDOR' and action == 'eliminar':
            messagebox.showerror("Acceso denegado", "Vendedores no pueden eliminar registros")
            return
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, text=f"{action.capitalize()} en {table_name}", font=("Arial", 16)).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        
        fetch_data(self.db_connection, tree, table_name)
        
        if self.db_connection.current_role == 'VENDEDOR' and action == 'eliminar':
            messagebox.showwarning("Restricción", "Su rol no permite eliminar registros")
            self.create_table_menu(action)
            return
            
        if self.db_connection.current_role == 'GERENTE' and action != 'visualizar':
            messagebox.showwarning("Restricción", "Su rol solo permite visualizar información")
            self.create_table_menu(action)
            return

        if action in ["agregar", "modificar"]:
            if table_name == "prestamo":
                self.create_prestamo_form(action, tree, table_name, columns[1:], id_column)
            else:
                self.create_form(action, tree, table_name, columns[1:], id_column)
        elif action == "eliminar":
            delete_button = tk.Button(
                self.root, text="Eliminar",
                command=lambda: delete_data(self.db_connection, tree, table_name, id_column),
                bg="#ff6666", fg="white"
            )
            delete_button.pack(pady=10)

        back_button = tk.Button(self.root, text="Volver", command=lambda: self.create_table_menu(action))
        back_button.pack(pady=10)

    def create_table_menu(self, action):
        for widget in self.root.winfo_children():
            widget.destroy()

        tablas_disponibles = self.get_tablas_por_rol()
        
        acciones_permitidas = self.get_acciones_por_rol()
        if action not in acciones_permitidas:
            messagebox.showerror("Error", "Acción no permitida para su rol")
            self.create_main_menu()
            return

        tk.Label(self.root, text=f"Seleccione tabla para {action}", font=("Arial", 14)).pack(pady=20)
        
        for table_name, columns in tablas_disponibles.items():
            tk.Button(
                self.root,
                text=table_name.capitalize(),
                width=25,
                command=lambda t=table_name, c=columns: self.create_action_interface(action, t, c, c[0])
            ).pack(pady=5)

        back_button = tk.Button(self.root, text="Volver", command=self.create_main_menu)
        back_button.pack(pady=10)

    def get_tablas_por_rol(self):
        tablas_completas = self.obtener_tablas_y_columnas()
        
        if self.db_connection.current_role == 'VENDEDOR':
            tablas_permitidas = ['usuario', 'libro', 'libro_autor', 'autor', 'categoria', 
                                'tipo_texto', 'prestamo', 'detalle_prestamo']
            return {k: v for k, v in tablas_completas.items() if k in tablas_permitidas}
        
        elif self.db_connection.current_role == 'GERENTE':
            return {'detalle_prestamo': tablas_completas['detalle_prestamo']}
            
        return tablas_completas 

    def get_acciones_por_rol(self):
        if self.db_connection.current_role == 'VENDEDOR':
            return ['visualizar', 'agregar', 'modificar']
        elif self.db_connection.current_role == 'GERENTE':
            return ['visualizar']
        return ['visualizar', 'agregar', 'modificar', 'eliminar'] 

    def create_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        print(f"DEBUG - Rol actual: {self.db_connection.current_role}")
        
        header = tk.Frame(self.root, bg="#f0f0f0", padx=10, pady=10)
        header.pack(fill="x")
        
        tk.Label(header, 
                text=f"Usuario: {self.db_connection.current_user} | Rol: {self.db_connection.current_role}",
                font=("Arial", 12, "bold"),
                bg="#f0f0f0").pack()

        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack()

        if self.db_connection.current_role == 'GERENTE':
            self._create_gerente_interface(main_frame)
        elif self.db_connection.current_role == 'VENDEDOR':
            self._create_vendedor_interface(main_frame)
        elif self.db_connection.current_role == 'DBA':
            self._create_dba_interface(main_frame)
        else:
            messagebox.showerror("Error", f"Rol no reconocido: {self.db_connection.current_role}")
            self.root.destroy()

    def _create_vendedor_interface(self, parent_frame):
        tk.Label(parent_frame, 
                text="OPCIONES DE VENDEDOR",
                font=("Arial", 14, "bold"),
                fg="#2E7D32").pack(pady=(0, 20))

        actions = [
            ("📋 Visualizar Datos", 'visualizar'),
            ("➕ Agregar Registros", 'agregar'),
            ("✏️ Editar Registros", 'modificar')
        ]

        for text, action in actions:
            btn = tk.Button(parent_frame,
                        text=text,
                        width=25,
                        bg="#4CAF50",
                        fg="white",
                        font=("Arial", 11),
                        command=lambda a=action: self.create_table_menu(a))
            btn.pack(pady=5)
        
        tk.Button(parent_frame,
                text="🔒 Cerrar Sesión",
                command=self.volver_al_login,
                bg="#FF5722",
                fg="white",
                font=("Arial", 11),
                width=25).pack(pady=10)
        
#BLOQUE MODIFICADO POR DARIANA
    def _create_gerente_interface(self, parent_frame):
        tk.Label(parent_frame, 
                text="REPORTES GERENCIALES",
                font=("Arial", 14, "bold"),
                fg="#1565C0").pack(pady=(0, 20))

        options = [
            ("📊 Libros más prestados", self.mostrar_reporte_libros_mas_prestados),
            ("📋 Usuarios Activos", self.mostrar_reporte_usuarios_activos),
            ("📒 Usuarios Con Mas Prestamos", self.mostrar_reporte_usuarios_mas_prestamos),
            ("🗂️ Stock de Libros por Categoria", self.mostrar_reporte_categoria)
        ]

        for text, cmd in options:
            btn = tk.Button(parent_frame,
                        text=text,
                        width=25,
                        bg="#2196F3",
                        fg="white",
                        font=("Arial", 11),
                        command=cmd)
            btn.pack(pady=5)
        
        tk.Button(parent_frame,
                text="🔒 Cerrar Sesión",
                command=self.volver_al_login,
                bg="#FF5722",
                fg="white",
                font=("Arial", 11),
                width=25).pack(pady=10)

    def mostrar_reporte_libros_mas_prestados(self):
        cursor = self.pol.generar_reporte_libros_mas_prestados(self.db_connection)
        if cursor:
            self.pol.mostrar_resultados_reporte(self.root, cursor, "Libros más prestados", self.create_main_menu)

    def mostrar_reporte_usuarios_activos(self):
        cursor = self.pol.generar_reporte_usuarios_estado_activo(self.db_connection)
        if cursor:
            self.pol.mostrar_resultados_reporte(self.root, cursor, "Usuarios con estado activo", self.create_main_menu)

    def mostrar_reporte_usuarios_mas_prestamos(self):
        cursor = self.pol.generar_reporte_usuarios_con_mas_prestamos(self.db_connection)
        if cursor:
            self.pol.mostrar_resultados_reporte(self.root, cursor, "Usuarios con mas prestamos", self.create_main_menu)

    def mostrar_reporte_categoria(self):
        cursor = self.pol.generar_reporte_categorias(self.db_connection)
        if cursor:
            self.pol.mostrar_resultados_reporte(self.root, cursor, "Cantidad de Libros por categoria", self.create_main_menu)
##FIN DE BLOQUE MODIFICADO >;)
    def mostrar_tabla_gerente(self, table_name):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, 
                text=f"Visualizando: {table_name}",
                font=("Arial", 16)).pack(pady=10)
        
        cursor = self.db_connection.serverdb.cursor()
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, table_name)
        columns = [row[0] for row in cursor.fetchall()]
        
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        
        fetch_data(self.db_connection, tree, table_name)
        
        tk.Button(self.root, 
                text="Volver",
                command=self.create_main_menu,
                bg="#2196F3",
                fg="white").pack(pady=10)

    def volver_al_login(self):
        """Cierra la sesión actual y vuelve al login"""
        self.root.destroy()
        from main import main
        main()

    def _create_dba_interface(self, parent_frame):
        """Interfaz COMPLETA para DBAs"""
        tk.Label(parent_frame, 
                text="ADMINISTRACIÓN COMPLETA",
                font=("Arial", 14, "bold"),
                fg="#BF360C").pack(pady=(0, 20))

        actions = [
            ("👁️ Visualizar", 'visualizar'),
            ("➕ Agregar", 'agregar'),
            ("✏️ Modificar", 'modificar'),
            ("🗑️ Eliminar", 'eliminar')
        ]

        for text, action in actions:
            color = "#D32F2F" if "Eliminar" in text else "#4CAF50"
            btn = tk.Button(parent_frame,
                        text=text,
                        width=20,
                        bg=color,
                        fg="white",
                        font=("Arial", 11),
                        command=lambda a=action: self.create_table_menu(a))
            btn.pack(pady=5)
        
        tk.Button(parent_frame,
                text="🔒 Cerrar Sesión",
                command=self.volver_al_login,
                bg="#FF5722",
                fg="white",
                font=("Arial", 11),
                width=25).pack(pady=10)

    def create_prestamo_form(self, action, tree, table_name, form_columns, id_column):
        frame=tk.Frame(self.root)
        frame.pack(pady=10)
        form_columns=[col for col in form_columns if col!='fecha_modificacion']

        entry_widgets={}
        for i, col in enumerate(form_columns):
            if col=="estado": 
                tk.Label(frame, text=col).grid(row=i, column=0, padx=5, pady=2)
                estado_var=tk.StringVar()
                estado_frame=tk.Frame(frame)
                estado_frame.grid(row=i, column=1, padx=5, pady=2)

                def update_estado_fields(*args):
                    estado=estado_var.get()
                    if estado=="Activo":
                        entry_widgets["fecha_devolucion"].delete(0, tk.END)
                        entry_widgets["fecha_devolucion"].config(state="disabled")
                    else:
                        entry_widgets["fecha_devolucion"].config(state="normal")

                tk.Radiobutton(estado_frame, text="Activo", variable=estado_var, value="Activo", command=update_estado_fields).pack(side="left")
                tk.Radiobutton(estado_frame, text="Devuelto", variable=estado_var, value="Devuelto", command=update_estado_fields).pack(side="left")
                estado_var.trace_add("write", update_estado_fields)
                entry_widgets[col]=estado_var
            else:
                tk.Label(frame, text=col).grid(row=i, column=0, padx=5, pady=2)
                entry=tk.Entry(frame)
                entry.grid(row=i, column=1, padx=5, pady=2)
                entry_widgets[col] = entry

                if "fecha" in col.lower():
                    tk.Label(frame, text="AAAA-MM-DD", fg="gray").grid(row=i, column=2, padx=5, pady=2)

        def handle_add():
            values = []
            for col in form_columns:
                if col == "estado":
                    values.append(entry_widgets[col].get())
                else:
                    values.append(entry_widgets[col].get())

            try:
                fecha_prestamo = datetime.strptime(entry_widgets['fecha_prestamo'].get(), "%Y-%m-%d")
                fecha_devolucion_str = entry_widgets['fecha_devolucion'].get().strip()
                if fecha_devolucion_str:
                    fecha_devolucion = datetime.strptime(fecha_devolucion_str, "%Y-%m-%d")
                    if fecha_prestamo > fecha_devolucion:
                        messagebox.showerror("Error", "La fecha de préstamo debe ser menor que la fecha de devolución.")
                        return
                
                fecha_limite_devolucion = datetime.strptime(entry_widgets['fecha_limite_devolucion'].get(), "%Y-%m-%d")
                if fecha_prestamo > fecha_limite_devolucion:
                    messagebox.showerror("Error", "La fecha de préstamo debe ser menor que la fecha límite de devolución.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use AAAA-MM-DD.")
                return

            add_data(self.db_connection, tree, table_name, form_columns, values)

        def handle_update():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Selecciona un registro para modificar.")
                return

            record_id = tree.item(selected_item)["values"][0]
            values = []
            for col in form_columns:
                if col in entry_widgets:
                    values.append(entry_widgets[col].get())
                else:
                    values.append(None)

            try:
                fecha_prestamo = datetime.strptime(entry_widgets['fecha_prestamo'].get(), "%Y-%m-%d")
                
                fecha_devolucion_str = entry_widgets['fecha_devolucion'].get().strip()
                if fecha_devolucion_str:
                    fecha_devolucion = datetime.strptime(fecha_devolucion_str, "%Y-%m-%d")
                    if fecha_prestamo > fecha_devolucion:
                        messagebox.showerror("Error", "La fecha de préstamo debe ser menor que la fecha de devolución.")
                        return
                
                fecha_limite_devolucion = datetime.strptime(entry_widgets['fecha_limite_devolucion'].get(), "%Y-%m-%d")
                if fecha_prestamo > fecha_limite_devolucion:
                    messagebox.showerror("Error", "La fecha de préstamo debe ser menor que la fecha límite de devolución.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use AAAA-MM-DD.")
                return
            
            update_data(self.db_connection, tree, table_name, form_columns, values, record_id)

        if action=="agregar":
            tk.Button(frame, text="Agregar", command=handle_add).grid(row=len(form_columns), column=0, pady=10)
        elif action=="modificar":
            def load_selected(event):
                selected_item=tree.selection()
                if not selected_item:
                    return
                values=tree.item(selected_item)["values"]
                for i, col in enumerate(form_columns):
                    if col=="estado":
                        entry_widgets[col].set(values[i+1])
                    else:
                        entry_widgets[col].delete(0, tk.END)
                        entry_widgets[col].insert(0, values[i+1])

            tree.bind("<ButtonRelease-1>", load_selected)
            tk.Button(frame, text="Modificar", command=handle_update).grid(row=len(form_columns), column=0, pady=10)

    def create_form(self, action, tree, table_name, columns, id_column):
        form_columns=[col for col in columns if col!='fecha_modificacion']
        frame=tk.Frame(self.root)
        frame.pack(pady=10)

        entry_widgets={}
        for i, col in enumerate(form_columns):
            tk.Label(frame, text=col).grid(row=i, column=0, padx=5, pady=2)
            entry=tk.Entry(frame)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry_widgets[col]=entry

            if "fecha" in col.lower():
                tk.Label(frame, text="AAAA-MM-DD", fg="gray").grid(row=i, column=2, padx=5, pady=2)

        if action=="agregar":
            def handle_add():
                values=[entry_widgets[col].get() for col in form_columns]
                add_data(self.db_connection, tree, table_name, form_columns, values)
            tk.Button(frame, text="Agregar", command=handle_add).grid(row=len(form_columns), column=0, pady=10)

        elif action=="modificar":
            def load_selected(event):
                selected_item=tree.selection()
                if not selected_item:
                    return
                values=tree.item(selected_item)["values"]
                for i, col in enumerate(form_columns):
                    entry_widgets[col].delete(0, tk.END)
                    entry_widgets[col].insert(0, values[i+1])

            def handle_update():
                selected_item=tree.selection()
                if not selected_item:
                    messagebox.showerror("Error", "Selecciona un registro para modificar.")
                    return
                record_id=tree.item(selected_item)["values"][0]
                values=[]
                for col in form_columns:
                    if col in entry_widgets:
                        values.append(entry_widgets[col].get())
                    else:
                        values.append(None)
                update_data(self.db_connection, tree, table_name, form_columns, values, record_id)
            tree.bind("<ButtonRelease-1>", load_selected)
            tk.Button(frame, text="Modificar", command=handle_update).grid(row=len(form_columns), column=0, pady=10)

    def obtener_tablas_y_columnas(self):
        try:
            if not self.db_connection.serverdb:
                print("Reconectando a SQL Server...")
                self.db_connection.conectar_sqlserver()

            conn = self.db_connection.serverdb
            cursor = conn.cursor()

            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' 
                AND TABLE_CATALOG = 'BibliotecaUniversitaria'
                AND TABLE_NAME <> 'sysdiagrams'
            """)
            tablas = [fila[0] for fila in cursor.fetchall()]

            tablas_columnas = {}

            for tabla_nombre in tablas:
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = ? 
                    ORDER BY ORDINAL_POSITION
                """, (tabla_nombre,))
                
                columnas = [col[0] for col in cursor.fetchall()]
                tablas_columnas[tabla_nombre] = columnas

            return tablas_columnas

        except Exception as e:
            print(f"Error al obtener tablas y columnas: {e}")
            return {}