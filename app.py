"""Sistema de Inventario y Control de Almacén - Escritorio.

Tecnologías: Python + Tkinter + MySQL Server.
No utiliza PHP, HTML ni navegador.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox

import mysql.connector
from mysql.connector import Error

import database
from modulos.proveedores import ProveedoresView
from modulos.ventas import VentasView


# -------------------------------
# Utilidades
# -------------------------------

def hash_password(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def money(value) -> str:
    try:
        return f"S/ {Decimal(str(value or 0)):.2f}"
    except Exception:
        return "S/ 0.00"


def ask_int(text, field_name):
    try:
        value = int(text)
        if value < 0:
            raise ValueError
        return value
    except ValueError:
        raise ValueError(f"{field_name} debe ser un número entero mayor o igual a 0.")


def ask_decimal(text, field_name):
    try:
        value = Decimal(text)
        if value < 0:
            raise ValueError
        return value
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} debe ser un número válido mayor o igual a 0.")


class AuthStyles:
    """Estilos compartidos para las pantallas de autenticación."""

    PURPLE = "#6864d8"
    BLUE = "#637be8"
    TEXT = "#222222"
    LABEL = "#3f3f46"
    BORDER = "#dddddd"
    WHITE = "#ffffff"
    INPUT_FOCUS = "#e9f1ff"

    @staticmethod
    def configure():
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Auth.TEntry",
            font=("Segoe UI", 11),
            padding=8,
            fieldbackground="white",
            foreground="#222222",
            bordercolor=AuthStyles.BORDER,
            lightcolor=AuthStyles.BORDER,
            darkcolor=AuthStyles.BORDER,
        )
        style.map(
            "Auth.TEntry",
            fieldbackground=[("focus", AuthStyles.INPUT_FOCUS)],
        )
        style.configure(
            "Auth.TCombobox",
            font=("Segoe UI", 11),
            padding=7,
            fieldbackground="white",
            background="white",
            foreground="#222222",
        )
        style.configure(
            "Auth.TButton",
            font=("Segoe UI", 11),
            padding=9,
            background=AuthStyles.BLUE,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Auth.TButton",
            background=[("active", "#536bd7"), ("pressed", "#536bd7")],
            foreground=[("active", "white"), ("pressed", "white")],
        )

    @staticmethod
    def label(parent, text):
        return tk.Label(
            parent, text=text, bg=AuthStyles.WHITE, fg=AuthStyles.LABEL,
            font=("Segoe UI", 10),
        )

    @staticmethod
    def link(parent, text, command):
        lbl = tk.Label(
            parent, text=text, bg=AuthStyles.WHITE, fg="#6d2aa8",
            font=("Segoe UI", 10, "underline"), cursor="hand2",
        )
        lbl.bind("<Button-1>", lambda _e: command())
        return lbl


class LoginWindow:
    """Autenticación en una sola ventana.

    Inicio de sesión y registro son dos vistas del mismo root de Tkinter.
    No se crean ventanas Toplevel adicionales.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio de Sesión - Sistema de Inventario")
        self.root.geometry("520x700")
        self.root.resizable(False, False)
        self.root.configure(bg=AuthStyles.PURPLE)
        AuthStyles.configure()

        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.register_view = None
        self._build_login()

    def _clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.register_view = None

    def _build_login(self):
        self._clear_root()
        self.root.title("Inicio de Sesión - Sistema de Inventario")

        card = tk.Frame(self.root, bg=AuthStyles.WHITE, bd=0, highlightthickness=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=430)

        tk.Label(
            card, text="Inicio de Sesión", bg=AuthStyles.WHITE, fg=AuthStyles.TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(34, 28))

        form = tk.Frame(card, bg=AuthStyles.WHITE)
        form.pack(fill="x", padx=30)

        AuthStyles.label(form, "Correo Electrónico:").pack(anchor="w")
        ttk.Entry(form, textvariable=self.email_var, style="Auth.TEntry").pack(
            fill="x", pady=(6, 16)
        )

        AuthStyles.label(form, "Contraseña:").pack(anchor="w")
        password_entry = ttk.Entry(
            form, textvariable=self.password_var, show="*", style="Auth.TEntry"
        )
        password_entry.pack(fill="x", pady=(6, 20))
        password_entry.bind("<Return>", lambda _event: self.login())

        ttk.Button(
            form, text="Iniciar Sesión", style="Auth.TButton", command=self.login
        ).pack(fill="x", ipady=2)

        bottom = tk.Frame(card, bg=AuthStyles.WHITE)
        bottom.pack(pady=(18, 0))
        tk.Label(
            bottom, text="¿No tienes una cuenta? ", bg=AuthStyles.WHITE,
            fg=AuthStyles.TEXT, font=("Segoe UI", 10)
        ).pack(side="left")
        AuthStyles.link(bottom, "Regístrate", self.open_register).pack(side="left")

    def open_register(self):
        # Cambiamos la vista dentro de la MISMA ventana.
        self._clear_root()
        self.root.title("Registro de Usuario - Sistema de Inventario")
        self.register_view = RegisterWindow(self.root, self.show_login)
        self.register_view.pack(fill="both", expand=True)

    def show_login(self):
        self._build_login()

    def login(self):
        email = self.email_var.get().strip()
        password = self.password_var.get()

        if not email or not password:
            messagebox.showwarning("Datos incompletos", "Ingresa correo y contraseña.", parent=self.root)
            return

        try:
            user = database.fetch_one(
                """SELECT id_usuario, nombres, apellidos, correo, contrasena, rol
                   FROM usuarios
                   WHERE correo = %s AND estado = 'A'
                   LIMIT 1""",
                (email,),
            )

            if not user or user["contrasena"] != hash_password(password):
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.", parent=self.root)
                return

            self.root.destroy()
            main_root = tk.Tk()
            InventoryApp(main_root, user)
            main_root.mainloop()

        except Error as exc:
            messagebox.showerror(
                "Conexión con MySQL",
                f"No se pudo acceder a la base de datos.\n\n{exc}",
                parent=self.root,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self.root)


class RegisterWindow(tk.Frame):
    """Vista de registro embebida en la misma ventana principal."""
    def __init__(self, parent, on_back):
        super().__init__(parent, bg=AuthStyles.PURPLE)
        self.on_back = on_back

        self.nombres_var = tk.StringVar()
        self.apellidos_var = tk.StringVar()
        self.correo_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.rol_var = tk.StringVar(value="Administrador")
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=AuthStyles.WHITE, bd=0, highlightthickness=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=620)

        tk.Label(
            card, text="Registro de Usuario", bg=AuthStyles.WHITE, fg=AuthStyles.TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(32, 28))

        form = tk.Frame(card, bg=AuthStyles.WHITE)
        form.pack(fill="x", padx=30)

        self._entry(form, "Nombres:", self.nombres_var)
        self._entry(form, "Apellidos:", self.apellidos_var)
        self._entry(form, "Correo Electrónico:", self.correo_var)

        AuthStyles.label(form, "Contraseña:").pack(anchor="w")
        ttk.Entry(form, textvariable=self.password_var, show="*", style="Auth.TEntry").pack(
            fill="x", pady=(6, 16)
        )

        AuthStyles.label(form, "Rol:").pack(anchor="w")
        ttk.Combobox(
            form, textvariable=self.rol_var,
            values=["Administrador", "Vendedor"],
            state="readonly", style="Auth.TCombobox"
        ).pack(fill="x", pady=(6, 18))

        ttk.Button(
            form, text="Registrarse", style="Auth.TButton", command=self.register
        ).pack(fill="x", ipady=2)

        bottom = tk.Frame(card, bg=AuthStyles.WHITE)
        bottom.pack(pady=(12, 0))
        tk.Label(
            bottom, text="¿Ya tienes cuenta? ", bg=AuthStyles.WHITE,
            fg=AuthStyles.TEXT, font=("Segoe UI", 10)
        ).pack(side="left")
        AuthStyles.link(bottom, "Inicia Sesión", self.back_to_login).pack(side="left")

    def _entry(self, parent, label, variable):
        AuthStyles.label(parent, label).pack(anchor="w")
        ttk.Entry(parent, textvariable=variable, style="Auth.TEntry").pack(
            fill="x", pady=(6, 14)
        )

    def register(self):
        nombres = self.nombres_var.get().strip()
        apellidos = self.apellidos_var.get().strip()
        correo = self.correo_var.get().strip()
        password = self.password_var.get()
        rol = "admin" if self.rol_var.get() == "Administrador" else "vendedor"

        if not all([nombres, apellidos, correo, password]):
            messagebox.showwarning("Datos incompletos", "Completa todos los campos.", parent=self)
            return
        if "@" not in correo or "." not in correo.split("@")[-1]:
            messagebox.showwarning("Correo inválido", "Ingresa un correo electrónico válido.", parent=self)
            return
        if len(password) < 4:
            messagebox.showwarning("Contraseña", "La contraseña debe tener al menos 4 caracteres.", parent=self)
            return

        try:
            exists = database.fetch_one("SELECT id_usuario FROM usuarios WHERE correo=%s LIMIT 1", (correo,))
            if exists:
                messagebox.showwarning("Correo registrado", "Ese correo ya está registrado.", parent=self)
                return

            database.execute(
                """INSERT INTO usuarios(nombres, apellidos, correo, contrasena, rol, estado)
                   VALUES(%s, %s, %s, %s, %s, 'A')""",
                (nombres, apellidos, correo, hash_password(password), rol),
            )
            messagebox.showinfo(
                "Registro exitoso",
                "Usuario registrado correctamente. Ahora puedes iniciar sesión.",
                parent=self,
            )
            self.back_to_login()
        except Error as exc:
            messagebox.showerror("Base de datos", f"No se pudo registrar el usuario.\n\n{exc}", parent=self)
        except Exception as exc:
            messagebox.showerror("Registro", str(exc), parent=self)

    def back_to_login(self):
        self.on_back()


class InventoryApp:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title("Sistema de Inventario y Control de Almacén")
        self.root.geometry("1200x760")
        self.root.minsize(1050, 680)
        self.root.configure(bg="#eef2f7")
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self._configure_styles()
        self.current_view = None
        self.show_dashboard()

    def _configure_styles(self):
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.configure("TNotebook.Tab", padding=(12, 8), font=("Segoe UI", 10, "bold"))

    def _clear(self):
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = tk.Frame(self.root, bg="#eef2f7")
        self.current_view.pack(side="right", fill="both", expand=True)
        return self.current_view

    def _shell(self, title, active=None):
        for widget in self.root.winfo_children():
            widget.destroy()

        sidebar = tk.Frame(self.root, bg="#243b53", width=235)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="INVENTARIO", bg="#243b53", fg="white",
                 font=("Segoe UI", 19, "bold")).pack(pady=(28, 0))
        tk.Label(sidebar, text="Tienda de computadoras", bg="#243b53", fg="#bcccdc",
                 font=("Segoe UI", 9)).pack(pady=(3, 25))

        buttons = [
            ("🏠  Dashboard", self.show_dashboard),
            ("💻  Productos", self.show_products),
            ("👥  Clientes", self.show_clients),
            ("🚚  Proveedores", self.show_providers),
            ("📦  Inventario", self.show_inventory),
            ("🛒  Ventas", self.show_sales),
            ("📊  Reportes", self.show_reports),
            ("👤  Usuarios", self.show_users),
        ]
        for text, command in buttons:
            tk.Button(sidebar, text=text, command=command, anchor="w", bd=0,
                      bg="#243b53", fg="white", activebackground="#334e68",
                      activeforeground="white", padx=20, pady=10,
                      font=("Segoe UI", 10), cursor="hand2").pack(fill="x", padx=8, pady=2)

        tk.Frame(sidebar, bg="#334e68", height=1).pack(fill="x", padx=15, pady=18)
        tk.Label(sidebar, text=f"{self.user['nombres']} {self.user['apellidos']}",
                 bg="#243b53", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(0, 3), padx=12)
        tk.Label(sidebar, text=str(self.user.get("rol", "")), bg="#243b53", fg="#9fb3c8",
                 font=("Segoe UI", 9)).pack()
        tk.Button(sidebar, text="Cerrar sesión", command=self.logout, bd=0,
                  bg="#d64545", fg="white", activebackground="#b83232",
                  font=("Segoe UI", 10, "bold"), padx=12, pady=9, cursor="hand2").pack(side="bottom", fill="x", padx=18, pady=18)

        content = tk.Frame(self.root, bg="#eef2f7")
        content.pack(side="right", fill="both", expand=True)
        tk.Label(content, text=title, bg="#eef2f7", fg="#243b53",
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=28, pady=(22, 2))
        tk.Label(content, text="Aplicación de escritorio con Python + MySQL Server",
                 bg="#eef2f7", fg="#7b8794", font=("Segoe UI", 9)).pack(anchor="w", padx=28, pady=(0, 12))
        return content

    def show_dashboard(self):
        view = self._shell("Dashboard")
        cards = tk.Frame(view, bg="#eef2f7")
        cards.pack(fill="x", padx=28, pady=10)
        stats = [
            ("Productos", "SELECT COUNT(*) c FROM productos", "📦"),
            ("Ventas hoy", "SELECT COUNT(*) c FROM ventas WHERE fecha_venta = CURDATE()", "🛒"),
            ("Stock bajo", "SELECT COUNT(*) c FROM productos WHERE stock_actual <= stock_minimo", "⚠"),
            ("Ingresos hoy", "SELECT COALESCE(SUM(total),0) c FROM ventas WHERE fecha_venta = CURDATE()", "S/"),
        ]
        for idx, (label, sql, icon) in enumerate(stats):
            try:
                value = database.fetch_one(sql)["c"]
            except Exception:
                value = "-"
            if label == "Ingresos hoy":
                value = money(value)
            card = tk.Frame(cards, bg="white", highlightbackground="#d9e2ec", highlightthickness=1)
            card.grid(row=0, column=idx, sticky="nsew", padx=6)
            cards.columnconfigure(idx, weight=1)
            tk.Label(card, text=icon, bg="white", fg="#486581", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(16, 2))
            tk.Label(card, text=str(value), bg="white", fg="#102a43", font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=18)
            tk.Label(card, text=label, bg="white", fg="#627d98", font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 16))

        body = tk.Frame(view, bg="white", highlightbackground="#d9e2ec", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=28, pady=12)
        tk.Label(body, text="Ventas recientes", bg="white", fg="#243b53",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=16)
        cols = ("id", "fecha", "vendedor", "comprobante", "total")
        tree = ttk.Treeview(body, columns=cols, show="headings")
        headings = {"id":"ID", "fecha":"Fecha", "vendedor":"Vendedor", "comprobante":"Comprobante", "total":"Total"}
        for c in cols:
            tree.heading(c, text=headings[c])
        tree.column("id", width=70, anchor="center")
        tree.column("total", width=130, anchor="e")
        for row in database.fetch_all(
            """SELECT v.id_venta, v.fecha_venta, CONCAT(u.nombres,' ',u.apellidos) vendedor,
                      v.tipo_comprobante, v.total
               FROM ventas v JOIN usuarios u ON u.id_usuario=v.id_vendedor
               ORDER BY v.id_venta DESC LIMIT 12"""
        ):
            tree.insert("", "end", values=(row["id_venta"], row["fecha_venta"], row["vendedor"], row["tipo_comprobante"], money(row["total"])))
        tree.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    # ---------------- Products ----------------
    def show_products(self):
        view = self._shell("Productos")
        bar = tk.Frame(view, bg="#eef2f7")
        bar.pack(fill="x", padx=28, pady=8)
        search_var = tk.StringVar()
        ttk.Entry(bar, textvariable=search_var, width=32).pack(side="left")
        ttk.Button(bar, text="Buscar", command=lambda: load(search_var.get().strip())).pack(side="left", padx=6)
        ttk.Button(bar, text="Nuevo producto", style="Accent.TButton", command=lambda: self.product_dialog(tree, load)).pack(side="right")

        frame = tk.Frame(view, bg="white")
        frame.pack(fill="both", expand=True, padx=28, pady=8)
        cols = ("id","nombre","categoria","marca","precio","stock","minimo")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        headings = {"id":"ID","nombre":"Producto","categoria":"Categoría","marca":"Marca","precio":"Precio","stock":"Stock","minimo":"Mínimo"}
        widths = {"id":60,"nombre":260,"categoria":130,"marca":120,"precio":100,"stock":90,"minimo":90}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="center" if c in ("id","stock","minimo") else "w")
        tree.pack(fill="both", expand=True, padx=12, pady=12)
        tree.bind("<Double-1>", lambda _e: self._edit_selected_product(tree, load))
        load = None

        def real_load(term=""):
            for item in tree.get_children(): tree.delete(item)
            like = f"%{term}%"
            rows = database.fetch_all(
                """SELECT * FROM productos
                   WHERE nombre_producto LIKE %s OR categoria LIKE %s OR marca LIKE %s
                   ORDER BY id_producto DESC""",
                (like, like, like),
            )
            for row in rows:
                tree.insert("", "end", values=(row["id_producto"], row["nombre_producto"], row["categoria"], row["marca"], money(row["precio_venta"]), row["stock_actual"], row["stock_minimo"]))

        load = real_load
        # Reasignamos el command de búsqueda después de definir load.
        for child in bar.winfo_children():
            if isinstance(child, ttk.Button) and child.cget("text") == "Buscar":
                child.configure(command=lambda: load(search_var.get().strip()))
        real_load()

    def _edit_selected_product(self, tree, load):
        selected = tree.selection()
        if selected:
            pid = tree.item(selected[0])["values"][0]
            self.product_dialog(tree, load, pid)

    def product_dialog(self, tree, refresh, product_id=None):
        win = tk.Toplevel(self.root)
        win.title("Editar producto" if product_id else "Nuevo producto")
        win.geometry("470x510")
        win.transient(self.root)
        win.grab_set()
        fields = [
            ("Producto", "nombre_producto"), ("Categoría", "categoria"), ("Marca", "marca"),
            ("Precio de venta", "precio_venta"), ("Stock actual", "stock_actual"), ("Stock mínimo", "stock_minimo")
        ]
        vars_ = {key: tk.StringVar() for _, key in fields}
        if product_id:
            row = database.fetch_one("SELECT * FROM productos WHERE id_producto=%s", (product_id,))
            if row:
                for _, key in fields: vars_[key].set(str(row[key] if row[key] is not None else ""))

        form = tk.Frame(win, padx=28, pady=18)
        form.pack(fill="both", expand=True)
        for label, key in fields:
            tk.Label(form, text=label, font=("Segoe UI", 10, "bold"), fg="#334e68").pack(anchor="w", pady=(0, 4))
            ttk.Entry(form, textvariable=vars_[key]).pack(fill="x", pady=(0, 12))

        def save():
            try:
                nombre = vars_["nombre_producto"].get().strip()
                if not nombre:
                    raise ValueError("El nombre del producto es obligatorio.")
                categoria = vars_["categoria"].get().strip()
                marca = vars_["marca"].get().strip()
                precio = ask_decimal(vars_["precio_venta"].get(), "Precio de venta")
                stock = ask_int(vars_["stock_actual"].get(), "Stock actual")
                minimo = ask_int(vars_["stock_minimo"].get(), "Stock mínimo")
                if product_id:
                    database.execute(
                        """UPDATE productos SET nombre_producto=%s,categoria=%s,marca=%s,
                           precio_venta=%s,stock_actual=%s,stock_minimo=%s WHERE id_producto=%s""",
                        (nombre,categoria,marca,precio,stock,minimo,product_id),
                    )
                    action = "Actualizó producto"
                    rid = product_id
                else:
                    rid = database.execute(
                        """INSERT INTO productos(nombre_producto,categoria,marca,precio_venta,stock_actual,stock_minimo)
                           VALUES(%s,%s,%s,%s,%s,%s)""",
                        (nombre,categoria,marca,precio,stock,minimo),
                    )
                    action = "Registró producto"
                database.execute("INSERT INTO logs_actividad(id_usuario,accion,tabla_afectada,id_registro,ip_usuario) VALUES(%s,%s,'productos',%s,'127.0.0.1')",
                                 (self.user["id_usuario"], action, rid))
                win.destroy()
                refresh()
            except Exception as exc:
                messagebox.showerror("No se pudo guardar", str(exc), parent=win)

        ttk.Button(form, text="Guardar", style="Accent.TButton", command=save).pack(fill="x", pady=6)
        ttk.Button(form, text="Cancelar", command=win.destroy).pack(fill="x")

    # ---------------- Clients ----------------
    def show_clients(self):
        view = self._shell("Clientes")
        bar = tk.Frame(view, bg="#eef2f7"); bar.pack(fill="x", padx=28, pady=8)
        search = tk.StringVar()
        ttk.Entry(bar, textvariable=search, width=32).pack(side="left")
        ttk.Button(bar, text="Buscar").pack(side="left", padx=6)
        ttk.Button(bar, text="Nuevo cliente", style="Accent.TButton", command=lambda: self.client_dialog(tree, load)).pack(side="right")
        frame = tk.Frame(view, bg="white"); frame.pack(fill="both", expand=True, padx=28, pady=8)
        cols=("id","nombre","telefono","correo")
        tree=ttk.Treeview(frame, columns=cols, show="headings")
        for c,t in zip(cols,("ID","Nombre","Teléfono","Correo")):
            tree.heading(c,text=t); tree.column(c,width=150 if c!="nombre" else 300)
        tree.pack(fill="both", expand=True,padx=12,pady=12)
        def load(term=""):
            for x in tree.get_children(): tree.delete(x)
            like=f"%{term}%"
            rows=database.fetch_all("SELECT * FROM clientes WHERE nombre_cliente LIKE %s OR telefono LIKE %s OR correo LIKE %s ORDER BY id_cliente DESC",(like,like,like))
            for r in rows: tree.insert("","end",values=(r["id_cliente"],r["nombre_cliente"],r["telefono"],r["correo"]))
        for child in bar.winfo_children():
            if isinstance(child, ttk.Button) and child.cget("text")=="Buscar": child.configure(command=lambda: load(search.get().strip()))
        load()
        tree.bind("<Double-1>", lambda _e: self._selected_simple(tree, load, "cliente"))

    def _selected_simple(self, tree, refresh, kind):
        s=tree.selection()
        if not s:return
        row=tree.item(s[0])["values"]
        self.client_dialog(tree, refresh, row[0])

    def client_dialog(self, tree, refresh, client_id=None):
        self.simple_entity_dialog("Cliente", "clientes", "id_cliente", [
            ("Nombre", "nombre_cliente"),("DNI / RUC","documento"),("Teléfono","telefono"),("Correo","correo"),("Dirección","direccion")
        ], tree, refresh, client_id)

    # ---------------- Providers ----------------
    def show_providers(self):
        view = self._shell("Proveedores")
        ProveedoresView(view, self.root, self.user).pack(fill="both", expand=True)

    def simple_entity_dialog(self,title,table,id_col,fields,tree,refresh,row_id=None):
        win=tk.Toplevel(self.root);win.title(("Editar " if row_id else "Nuevo ")+title.lower());win.geometry("460x520");win.transient(self.root);win.grab_set()
        vars_={k:tk.StringVar() for _,k in fields}
        if row_id:
            row=database.fetch_one(f"SELECT * FROM {table} WHERE {id_col}=%s",(row_id,))
            if row:
                for _,k in fields:vars_[k].set(str(row[k] or ""))
        form=tk.Frame(win,padx=28,pady=22);form.pack(fill="both",expand=True)
        entries=[]
        for label,k in fields:
            tk.Label(form,text=label,font=("Segoe UI",10,"bold"),fg="#334e68").pack(anchor="w")
            e=ttk.Entry(form,textvariable=vars_[k]);e.pack(fill="x",pady=(5,14));entries.append(e)
        def save():
            try:
                values=[vars_[k].get().strip() for _,k in fields]
                if not values[0]: raise ValueError(f"{fields[0][0]} es obligatorio.")
                if row_id:
                    set_sql=", ".join(f"{k}=%s" for _,k in fields)
                    database.execute(f"UPDATE {table} SET {set_sql} WHERE {id_col}=%s", tuple(values)+(row_id,))
                    rid=row_id;action=f"Actualizó {title.lower()}"
                else:
                    cols=", ".join(k for _,k in fields); qs=", ".join(["%s"]*len(fields))
                    rid=database.execute(f"INSERT INTO {table}({cols}) VALUES({qs})",tuple(values));action=f"Registró {title.lower()}"
                database.execute("INSERT INTO logs_actividad(id_usuario,accion,tabla_afectada,id_registro,ip_usuario) VALUES(%s,%s,%s,%s,'127.0.0.1')",(self.user["id_usuario"],action,table,rid))
                win.destroy();refresh()
            except Exception as exc:messagebox.showerror("No se pudo guardar",str(exc),parent=win)
        ttk.Button(form,text="Guardar",style="Accent.TButton",command=save).pack(fill="x",pady=5)
        ttk.Button(form,text="Cancelar",command=win.destroy).pack(fill="x")
        entries[0].focus_set()

    # ---------------- Inventory ----------------
    def show_inventory(self):
        view=self._shell("Inventario")
        top=tk.Frame(view,bg="#eef2f7");top.pack(fill="x",padx=28,pady=8)
        ttk.Button(top,text="Actualizar",command=lambda:load()).pack(side="left")
        ttk.Button(top,text="Solo stock bajo",command=lambda:load(True)).pack(side="left",padx=6)
        frame=tk.Frame(view,bg="white");frame.pack(fill="both",expand=True,padx=28,pady=8)
        cols=("producto","categoria","stock","minimo","estado","porcentaje")
        tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,t,w in zip(cols,("Producto","Categoría","Stock actual","Stock mínimo","Estado","% stock"),(280,130,100,100,110,90)):
            tree.heading(c,text=t);tree.column(c,width=w,anchor="center" if c not in ("producto","categoria") else "w")
        tree.pack(fill="both",expand=True,padx=12,pady=12)
        def load(low_only=False):
            for x in tree.get_children():tree.delete(x)
            sql="SELECT nombre_producto,categoria,stock_actual,stock_minimo FROM productos"
            if low_only:sql+=" WHERE stock_actual<=stock_minimo"
            sql+=" ORDER BY stock_actual ASC"
            for r in database.fetch_all(sql):
                minimo=max(int(r["stock_minimo"] or 0),1);stock=int(r["stock_actual"] or 0)
                pct=min(100,(stock/minimo)*100);estado="CRÍTICO" if stock<=minimo else ("BAJO" if stock<=minimo*1.5 else "NORMAL")
                tree.insert("","end",values=(r["nombre_producto"],r["categoria"],stock,r["stock_minimo"],estado,f"{pct:.0f}%"))
        load()

    # ---------------- Sales ----------------
    def show_sales(self):
        view = self._shell("Ventas")
        VentasView(view, self.root, self.user).pack(fill="both", expand=True)

    # ---------------- Reports ----------------
    def show_reports(self):
        view=self._shell("Reportes")
        notebook=ttk.Notebook(view);notebook.pack(fill="both",expand=True,padx=28,pady=10)
        self._report_sales(notebook)
        self._report_products(notebook)
        self._report_low_stock(notebook)

    def _report_sales(self, notebook):
        tab=tk.Frame(notebook,bg="white");notebook.add(tab,text="Ventas por fecha")
        filt=tk.Frame(tab,bg="white",padx=18,pady=16);filt.pack(fill="x")
        start=tk.StringVar(value=datetime.now().replace(day=1).strftime("%Y-%m-%d"));end=tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Label(filt,text="Desde",bg="white").pack(side="left");ttk.Entry(filt,textvariable=start,width=12).pack(side="left",padx=6)
        tk.Label(filt,text="Hasta",bg="white").pack(side="left");ttk.Entry(filt,textvariable=end,width=12).pack(side="left",padx=6)
        frame=tk.Frame(tab,bg="white");frame.pack(fill="both",expand=True,padx=18,pady=5)
        cols=("fecha","ventas","ingreso","promedio");tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,t in zip(cols,("Fecha","Ventas","Ingreso","Promedio")):tree.heading(c,text=t)
        tree.pack(fill="both",expand=True)
        summary=tk.StringVar(value="")
        tk.Label(tab,textvariable=summary,bg="white",fg="#243b53",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=12)
        def run():
            try:
                s=start.get().strip();e=end.get().strip();datetime.strptime(s,"%Y-%m-%d");datetime.strptime(e,"%Y-%m-%d")
                for x in tree.get_children():tree.delete(x)
                rows=database.fetch_all("SELECT fecha_venta fecha,COUNT(*) ventas,COALESCE(SUM(total),0) ingreso,COALESCE(AVG(total),0) promedio FROM ventas WHERE fecha_venta BETWEEN %s AND %s GROUP BY fecha_venta ORDER BY fecha_venta",(s,e))
                tv=ti=Decimal("0")
                for r in rows:
                    tv+=int(r["ventas"]);ti+=Decimal(str(r["ingreso"] or 0));tree.insert("","end",values=(r["fecha"],r["ventas"],money(r["ingreso"]),money(r["promedio"])))
                summary.set(f"Total ventas: {tv}   |   Ingresos: {money(ti)}")
            except Exception as exc:messagebox.showerror("Reporte",str(exc))
        ttk.Button(filt,text="Generar",command=run).pack(side="left",padx=8);run()

    def _report_products(self, notebook):
        tab=tk.Frame(notebook,bg="white");notebook.add(tab,text="Productos vendidos")
        cols=("producto","cantidad","ingreso");tree=ttk.Treeview(tab,columns=cols,show="headings")
        for c,t in zip(cols,("Producto","Cantidad","Ingreso")):tree.heading(c,text=t)
        tree.pack(fill="both",expand=True,padx=18,pady=18)
        for r in database.fetch_all("""SELECT p.nombre_producto producto,COALESCE(SUM(dv.cantidad),0) cantidad,COALESCE(SUM(dv.subtotal_detalle),0) ingreso
                                      FROM detalle_venta dv JOIN productos p ON p.id_producto=dv.id_producto
                                      GROUP BY p.id_producto,p.nombre_producto ORDER BY cantidad DESC"""):
            tree.insert("","end",values=(r["producto"],r["cantidad"],money(r["ingreso"])))

    def _report_low_stock(self, notebook):
        tab=tk.Frame(notebook,bg="white");notebook.add(tab,text="Stock bajo")
        cols=("producto","stock","minimo","faltante");tree=ttk.Treeview(tab,columns=cols,show="headings")
        for c,t in zip(cols,("Producto","Stock","Mínimo","Faltante")):tree.heading(c,text=t)
        tree.pack(fill="both",expand=True,padx=18,pady=18)
        for r in database.fetch_all("SELECT nombre_producto,stock_actual,stock_minimo,(stock_minimo-stock_actual) faltante FROM productos WHERE stock_actual<=stock_minimo ORDER BY stock_actual"):
            tree.insert("","end",values=(r["nombre_producto"],r["stock_actual"],r["stock_minimo"],r["faltante"]))

    # ---------------- Users ----------------
    def show_users(self):
        view=self._shell("Usuarios")
        top=tk.Frame(view,bg="#eef2f7");top.pack(fill="x",padx=28,pady=8)
        ttk.Button(top,text="Nuevo usuario",style="Accent.TButton",command=lambda:self.user_dialog(tree,load)).pack(side="right")
        frame=tk.Frame(view,bg="white");frame.pack(fill="both",expand=True,padx=28,pady=8)
        cols=("id","nombres","apellidos","correo","rol","estado")
        tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,t in zip(cols,("ID","Nombres","Apellidos","Correo","Rol","Estado")):tree.heading(c,text=t);tree.column(c,width=100 if c in ("id","rol","estado") else 190)
        tree.pack(fill="both",expand=True,padx=12,pady=12)
        def load():
            for x in tree.get_children():tree.delete(x)
            for r in database.fetch_all("SELECT id_usuario,nombres,apellidos,correo,rol,estado FROM usuarios ORDER BY id_usuario DESC"):
                tree.insert("","end",values=tuple(r[c] for c in cols))
        load()

    def user_dialog(self, tree, refresh):
        win=tk.Toplevel(self.root);win.title("Nuevo usuario");win.geometry("470x500");win.transient(self.root);win.grab_set()
        fields=[("Nombres","nombres"),("Apellidos","apellidos"),("Correo","correo"),("Contraseña","contrasena"),("Rol","rol")]
        vars_={k:tk.StringVar() for _,k in fields}
        form=tk.Frame(win,padx=28,pady=20);form.pack(fill="both",expand=True)
        for label,k in fields:
            tk.Label(form,text=label,font=("Segoe UI",10,"bold"),fg="#334e68").pack(anchor="w")
            ttk.Entry(form,textvariable=vars_[k],show="*" if k=="contrasena" else "").pack(fill="x",pady=(4,12))
        def save():
            try:
                vals=[vars_[k].get().strip() for _,k in fields]
                if any(not x for x in vals):raise ValueError("Completa todos los campos.")
                execute_sql="INSERT INTO usuarios(nombres,apellidos,correo,contrasena,rol,estado) VALUES(%s,%s,%s,%s,%s,'A')"
                rid=database.execute(execute_sql,(vals[0],vals[1],vals[2],hash_password(vals[3]),vals[4]))
                database.execute("INSERT INTO logs_actividad(id_usuario,accion,tabla_afectada,id_registro,ip_usuario) VALUES(%s,'Registró usuario','usuarios',%s,'127.0.0.1')",(self.user["id_usuario"],rid))
                win.destroy();refresh()
            except Exception as exc:messagebox.showerror("Usuario",str(exc),parent=win)
        ttk.Button(form,text="Guardar",style="Accent.TButton",command=save).pack(fill="x",pady=6);ttk.Button(form,text="Cancelar",command=win.destroy).pack(fill="x")

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar la sesión?"):
            self.root.destroy()
            root=tk.Tk();LoginWindow(root);root.mainloop()


def main():
    ok, message = database.test_connection()
    if not ok:
        # Aún permitimos abrir la ventana de login para que el usuario vea el sistema;
        # al ingresar se mostrará el error real de conexión.
        print("Aviso MySQL:", message)
    root=tk.Tk();LoginWindow(root);root.mainloop()


if __name__ == "__main__":
    main()
