import pyodbc
from dataclasses import dataclass
from tkinter import messagebox

@dataclass
class Conexiones:
    serverdb: pyodbc.Connection = None
    current_user: str = None
    current_role: str = None

    def conectar_sqlserver(self, username: str, password: str, rol: str):
        # Datos de conexión
        server = 'MSI\\MSSQLSERVER01'  # Asegúrate de que esta instancia sea correcta
        database = 'BibliotecaUniversitaria'

        try:
            # Cadena de conexión
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )
            # Intentar conectar
            self.serverdb = pyodbc.connect(conn_str)
            self.current_user = username
            self.current_role = rol

            # Verificar los permisos del usuario
            if not self._verificar_permisos_reales():
                messagebox.showerror("Permisos insuficientes", "Los permisos reales no coinciden con el rol asignado.")
                self.cerrar_conexiones()
                return None

            # Conexión exitosa
            messagebox.showinfo("Conexión exitosa", f"Bienvenido {username} ({rol})")
            return self.serverdb

        except pyodbc.Error as e:
            # Mostrar mensaje de error si falla la conexión
            messagebox.showerror("Error de conexión", f"No se pudo conectar a SQL Server:\n{str(e)}")
            print(f"[DEBUG] Detalles del error: {e}")
            self.serverdb = None
            return None

    def _verificar_permisos_reales(self):
        try:
            cursor = self.serverdb.cursor()

            if self.current_role.upper() == 'DBA':
                cursor.execute("SELECT IS_ROLEMEMBER('db_owner', USER_NAME())")
                return cursor.fetchone()[0] == 1

            elif self.current_role.upper() == 'VENDEDOR':
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLE_PRIVILEGES 
                    WHERE GRANTEE = USER_NAME()
                    AND PRIVILEGE_TYPE IN ('INSERT', 'UPDATE')
                    AND TABLE_NAME IN ('prestamo', 'detalle_prestamo', 'libro', 'usuario')
                """)
                return cursor.fetchone()[0] >= 4

            elif self.current_role.upper() == 'GERENTE':
                cursor.execute("SELECT IS_ROLEMEMBER('db_datareader', USER_NAME())")
                return cursor.fetchone()[0] == 1

            return False

        except pyodbc.Error as e:
            print(f"[DEBUG] Error al verificar permisos: {e}")
            return False

    def cerrar_conexiones(self):
        if self.serverdb:
            try:
                self.serverdb.close()
                self.serverdb = None
            except pyodbc.Error as e:
                print(f"[DEBUG] Error al cerrar conexión: {e}")
