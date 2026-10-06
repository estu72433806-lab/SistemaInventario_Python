"""Módulo Ventas: historial, registro de venta y comprobante PDF.

    VentasView   -> pantalla principal (tabla + botones Nueva venta / Imprimir / Ver PDF)
    VentaDialog  -> ventana "Registrar venta" (incluye el manejador de "Guardar venta")
"""

from __future__ import annotations

import re
import tkinter as tk
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from tkinter import messagebox, ttk

from mysql.connector import Error as MySQLError

import database
from .comprobantes import generar_comprobante_pdf, numero_comprobante
from .comun import CENT, IGV_RATE, abrir_archivo, mensaje_error_mysql

BG = "#eef2f7"
CONSUMIDOR_FINAL = "Consumidor final (sin datos)"


def money(valor) -> str:
    return f"S/ {Decimal(str(valor or 0)):.2f}"


def _hora_txt(valor) -> str:
    """TIME de MySQL llega como timedelta; lo mostramos como HH:MM:SS."""
    if hasattr(valor, "total_seconds"):
        s = int(valor.total_seconds())
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
    return str(valor or "")


def _generar_y_abrir(parent, id_venta: int, preguntar: bool = False, titulo: str = "Comprobante"):
    """Genera el PDF y lo abre (o pregunta antes). Muestra errores claros."""
    try:
        ruta = generar_comprobante_pdf(id_venta)
    except ImportError:
        messagebox.showerror(titulo, "Falta instalar la librería de PDF.\n\npip install reportlab",
                             parent=parent)
        return None
    except MySQLError as exc:
        messagebox.showerror(titulo, mensaje_error_mysql(exc), parent=parent)
        return None
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror(titulo, f"No se pudo generar el PDF.\n\n{exc}", parent=parent)
        return None
    if not preguntar or messagebox.askyesno(
            titulo, f"Venta N.° {id_venta} registrada.\nComprobante generado:\n{ruta}\n\n¿Deseas abrir el PDF ahora?", parent=parent):
        try:
            abrir_archivo(ruta)
        except OSError as exc:
            messagebox.showerror(titulo, f"El PDF se guardó pero no se pudo abrir.\n\n{exc}", parent=parent)
    return ruta


# =============================================================
# Pantalla principal de Ventas
# =============================================================
class VentasView(tk.Frame):
    def __init__(self, parent, root, user: dict):
        super().__init__(parent, bg=BG)
        self.root, self.user = root, user
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg=BG)
        barra.pack(fill="x", padx=28, pady=8)
        ttk.Button(barra, text="Nueva venta", style="Accent.TButton",
                   command=self.nueva_venta).pack(side="left")
        self.btn_pdf = ttk.Button(barra, text="🖨️ Imprimir / Ver PDF", command=self.imprimir)
        self.btn_pdf.pack(side="left", padx=8)
        tk.Label(barra, text="Doble clic o clic derecho sobre una venta para ver su comprobante.",
                 bg=BG, fg="#9aa5b1", font=("Segoe UI", 8)).pack(side="left", padx=10)

        marco = tk.Frame(self, bg="white")
        marco.pack(fill="both", expand=True, padx=28, pady=8)
        cols = ("id", "comprobante_nro", "fecha", "hora", "vendedor", "comprobante", "subtotal", "igv", "total")
        titulos = ("ID", "N° comprobante", "Fecha", "Hora", "Vendedor", "Tipo", "Subtotal", "IGV", "Total")
        anchos = (50, 125, 95, 80, 170, 100, 100, 90, 105)
        self.tree = ttk.Treeview(marco, columns=cols, show="headings", selectmode="browse")
        for c, t, w in zip(cols, titulos, anchos):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="e" if c in ("subtotal", "igv", "total") else "w")
        sb = ttk.Scrollbar(marco, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=12)
        self.tree.pack(fill="both", expand=True, padx=(12, 0), pady=12)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="🖨️  Imprimir / Ver PDF", command=self.imprimir)
        self.tree.bind("<Double-1>", lambda _e: self.imprimir())
        self.tree.bind("<Button-3>", self._menu_contextual)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._actualizar_botones())
        self._actualizar_botones()

    def cargar(self):
        self.tree.delete(*self.tree.get_children())
        try:
            filas = database.fetch_all(
                """SELECT v.*, CONCAT(u.nombres,' ',u.apellidos) AS vendedor
                   FROM ventas v LEFT JOIN usuarios u ON u.id_usuario = v.id_vendedor
                   ORDER BY v.id_venta DESC""")
        except MySQLError as exc:
            messagebox.showerror("Ventas", mensaje_error_mysql(exc), parent=self.root)
            return
        for r in filas:
            self.tree.insert("", "end", iid=str(r["id_venta"]), values=(
                r["id_venta"], numero_comprobante(r["tipo_comprobante"], r["id_venta"]),
                r["fecha_venta"], _hora_txt(r["hora_venta"]), r["vendedor"] or "—",
                r["tipo_comprobante"], money(r["subtotal"]), money(r["igv"]), money(r["total"])))

    def _actualizar_botones(self):
        self.btn_pdf.configure(state="normal" if self.tree.selection() else "disabled")

    def _menu_contextual(self, evento):
        fila = self.tree.identify_row(evento.y)
        if fila:
            self.tree.selection_set(fila)
            self.menu.tk_popup(evento.x_root, evento.y_root)

    def nueva_venta(self):
        try:
            VentaDialog(self.root, self.user, on_saved=self.cargar)
        except MySQLError as exc:
            messagebox.showerror("Nueva venta", mensaje_error_mysql(exc), parent=self.root)

    def imprimir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Comprobante", "Selecciona una venta de la tabla.", parent=self.root)
            return
        _generar_y_abrir(self.root, int(sel[0]))


# =============================================================
# Ventana "Registrar venta"
# =============================================================
class VentaDialog(tk.Toplevel):
    def __init__(self, parent, user: dict, on_saved=None):
        super().__init__(parent)
        self.root_parent, self.user, self.on_saved = parent, user, on_saved
        self.title("Registrar venta")
        self.geometry("920x700")
        self.transient(parent)

        # Se leen antes de mostrar la ventana: si MySQL falla, el error sube a VentasView.
        productos = database.fetch_all(
            "SELECT id_producto,nombre_producto,precio_venta,stock_actual "
            "FROM productos WHERE stock_actual>0 ORDER BY nombre_producto")
        clientes = database.fetch_all(
            "SELECT id_cliente,nombre_cliente,documento FROM clientes ORDER BY nombre_cliente")

        self.product_map = {f"{r['id_producto']} - {r['nombre_producto']}": r for r in productos}
        self.client_map = {CONSUMIDOR_FINAL: None}
        for c in clientes:
            doc = f" ({c['documento']})" if c["documento"] else ""
            self.client_map[f"{c['id_cliente']} - {c['nombre_cliente']}{doc}"] = c
        self.lineas: list[dict] = []

        self._construir()
        self.grab_set()

    # ---------- interfaz ----------
    def _construir(self):
        cab = tk.Frame(self, padx=20, pady=12)
        cab.pack(fill="x")
        self.tipo_var = tk.StringVar(value="BOLETA")
        tk.Label(cab, text="Tipo de comprobante", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Combobox(cab, textvariable=self.tipo_var, values=["BOLETA", "FACTURA"],
                     state="readonly", width=12).pack(side="left", padx=8)
        tk.Label(cab, text="Cliente", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(20, 0))
        self.cliente_var = tk.StringVar(value=CONSUMIDOR_FINAL)
        ttk.Combobox(cab, textvariable=self.cliente_var, values=list(self.client_map),
                     state="readonly", width=44).pack(side="left", padx=8)

        form = tk.Frame(self, padx=20)
        form.pack(fill="x")
        self.prod_var, self.qty_var = tk.StringVar(), tk.StringVar(value="1")
        ttk.Combobox(form, textvariable=self.prod_var, values=list(self.product_map),
                     width=52, state="readonly").pack(side="left")
        ttk.Entry(form, textvariable=self.qty_var, width=8).pack(side="left", padx=8)
        ttk.Button(form, text="Agregar", command=self._agregar_linea).pack(side="left")
        ttk.Button(form, text="Quitar seleccionado", command=self._quitar_linea).pack(side="left", padx=8)

        marco = tk.Frame(self)
        marco.pack(fill="both", expand=True, padx=20, pady=12)
        cols = ("producto", "cantidad", "precio", "subtotal")
        self.tree = ttk.Treeview(marco, columns=cols, show="headings", height=11, selectmode="browse")
        for c, t in zip(cols, ("Producto", "Cantidad", "Precio", "Subtotal")):
            self.tree.heading(c, text=t)
        self.tree.column("producto", width=470)
        self.tree.column("cantidad", width=100, anchor="center")
        self.tree.column("precio", width=120, anchor="e")
        self.tree.column("subtotal", width=130, anchor="e")
        self.tree.pack(fill="both", expand=True)

        tot = tk.Frame(self, padx=20, pady=8)
        tot.pack(fill="x")
        self.sub_var, self.igv_var, self.tot_var = (tk.StringVar(value="0.00") for _ in range(3))
        for texto, var in (("Subtotal", self.sub_var), ("IGV (18%)", self.igv_var), ("Total", self.tot_var)):
            tk.Label(tot, text=f"{texto}: ", font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(tot, textvariable=var, font=("Segoe UI", 10)).pack(side="left", padx=(0, 25))

        self.btn_guardar = ttk.Button(self, text="Guardar venta", style="Accent.TButton",
                                      command=self._guardar_venta)
        self.btn_guardar.pack(side="right", padx=20, pady=12)
        ttk.Button(self, text="Cancelar", command=self.destroy).pack(side="right", pady=12)

    # ---------- cálculo ----------
    def _calcular(self):
        subtotal = sum((l["subtotal"] for l in self.lineas), Decimal("0")).quantize(CENT, ROUND_HALF_UP)
        igv = (subtotal * IGV_RATE).quantize(CENT, ROUND_HALF_UP)
        return subtotal, igv, subtotal + igv

    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        for i, l in enumerate(self.lineas):
            self.tree.insert("", "end", iid=str(i),
                             values=(l["nombre"], l["cantidad"], f"{l['precio']:.2f}", f"{l['subtotal']:.2f}"))
        sub, igv, total = self._calcular()
        self.sub_var.set(f"{sub:.2f}")
        self.igv_var.set(f"{igv:.2f}")
        self.tot_var.set(f"{total:.2f}")

    # ---------- líneas ----------
    def _agregar_linea(self):
        sel = self.prod_var.get()
        if sel not in self.product_map:
            messagebox.showwarning("Venta", "Selecciona un producto.", parent=self)
            return
        try:
            q = int(self.qty_var.get())
            if q <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Venta", "La cantidad debe ser un número entero mayor que 0.", parent=self)
            return
        r = self.product_map[sel]
        ya = sum(l["cantidad"] for l in self.lineas if l["id_producto"] == r["id_producto"])
        if ya + q > int(r["stock_actual"]):
            messagebox.showwarning("Stock", f"Stock disponible: {r['stock_actual']}", parent=self)
            return
        for l in self.lineas:
            if l["id_producto"] == r["id_producto"]:
                l["cantidad"] += q
                l["subtotal"] = l["precio"] * l["cantidad"]
                break
        else:
            precio = Decimal(str(r["precio_venta"]))
            self.lineas.append({"id_producto": r["id_producto"], "nombre": r["nombre_producto"],
                                "cantidad": q, "precio": precio, "subtotal": precio * q})
        self._refrescar()

    def _quitar_linea(self):
        sel = self.tree.selection()
        if sel:
            del self.lineas[int(sel[0])]
            self._refrescar()

    # ---------- guardar ----------
    def _cliente_elegido(self):
        return self.client_map.get(self.cliente_var.get())

    def _insertar_venta(self, tipo, cliente, subtotal, igv, total) -> int:
        """Inserta cabecera + detalle + descuento de stock en UNA transacción."""
        with database.get_connection() as conn:
            cur = conn.cursor()
            try:
                ahora = datetime.now()
                cur.execute(
                    "INSERT INTO ventas(fecha_venta,hora_venta,id_vendedor,id_cliente,tipo_comprobante,"
                    "subtotal,igv,total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (ahora.date(), ahora.time().replace(microsecond=0), self.user["id_usuario"],
                     cliente["id_cliente"] if cliente else None, tipo, subtotal, igv, total))
                id_venta = cur.lastrowid
                for l in self.lineas:
                    cur.execute("SELECT stock_actual FROM productos WHERE id_producto=%s FOR UPDATE",
                                (l["id_producto"],))
                    if l["cantidad"] > int(cur.fetchone()[0]):
                        raise ValueError(f"Stock insuficiente para {l['nombre']}.")
                    cur.execute(
                        "INSERT INTO detalle_venta(id_venta,id_producto,cantidad,precio_unitario,"
                        "subtotal_detalle) VALUES(%s,%s,%s,%s,%s)",
                        (id_venta, l["id_producto"], l["cantidad"], l["precio"], l["subtotal"]))
                    cur.execute("UPDATE productos SET stock_actual=stock_actual-%s WHERE id_producto=%s",
                                (l["cantidad"], l["id_producto"]))
                cur.execute(
                    "INSERT INTO logs_actividad(id_usuario,accion,tabla_afectada,id_registro,ip_usuario) "
                    "VALUES(%s,'Registró venta','ventas',%s,'127.0.0.1')", (self.user["id_usuario"], id_venta))
                conn.commit()
                return id_venta
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

    def _guardar_venta(self):
        """Manejador del botón «Guardar venta»: valida, guarda en MySQL y genera el PDF."""
        if not self.lineas:
            messagebox.showwarning("Venta", "Agrega al menos un producto.", parent=self)
            return
        tipo = self.tipo_var.get()
        cliente = self._cliente_elegido()
        if tipo == "FACTURA":
            doc = (cliente or {}).get("documento") or ""
            if not cliente or not re.fullmatch(r"[0-9]{11}", doc):
                messagebox.showwarning(
                    "Factura",
                    "Para emitir una FACTURA elige un cliente que tenga RUC (11 dígitos).\n"
                    "Puedes registrarlo o completarlo en el módulo Clientes.", parent=self)
                return

        subtotal, igv, total = self._calcular()
        self.btn_guardar.configure(state="disabled")        # evita doble clic = venta duplicada
        try:
            id_venta = self._insertar_venta(tipo, cliente, subtotal, igv, total)
        except ValueError as exc:
            messagebox.showwarning("No se pudo registrar", str(exc), parent=self)
            self.btn_guardar.configure(state="normal")
            return
        except MySQLError as exc:
            messagebox.showerror("No se pudo registrar", mensaje_error_mysql(exc), parent=self)
            self.btn_guardar.configure(state="normal")
            return

        # La venta ya está guardada. Cerramos el modal y refrescamos la tabla.
        padre = self.root_parent
        self.destroy()
        if self.on_saved:
            self.on_saved()

        # Si el PDF falla, la venta NO se pierde: se puede reimprimir desde la tabla.
        ruta_ok = _generar_y_abrir(padre, id_venta, preguntar=True, titulo="Venta registrada")
        if ruta_ok is None:
            messagebox.showinfo(
                "Venta registrada",
                f"La venta N.° {id_venta} se guardó correctamente.\n"
                "Puedes generar el comprobante luego con «🖨️ Imprimir / Ver PDF».", parent=padre)
