"""Generación de comprobantes de venta (Boleta / Factura) en PDF con reportlab.

    pip install reportlab

Uso:
    ruta = generar_comprobante_pdf(id_venta)      # -> Path al PDF dentro de /comprobantes
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import database

# ------------------------------------------------------------------
# CONFIGURACIÓN: edita los datos de tu empresa
# ------------------------------------------------------------------
EMPRESA = {
    "nombre": "TIENDA DE COMPUTADORAS",
    "subtitulo": "Sistema de Inventario y Control de Almacén",
    "ruc": "00000000000",                       # <-- coloca el RUC real
    "direccion": "Av. Principal 123, Lima - Perú",
    "telefono": "(01) 000-0000",
}
SERIES = {"BOLETA": "B001", "FACTURA": "F001"}
NOMBRES_DOC = {"BOLETA": "BOLETA DE VENTA", "FACTURA": "FACTURA"}
PREFIJO_ARCHIVO = {"BOLETA": "Boleta", "FACTURA": "Factura"}

BASE_DIR = Path(__file__).resolve().parent.parent
CARPETA_COMPROBANTES = BASE_DIR / "comprobantes"

AZUL = colors.HexColor("#243B53")
GRIS = colors.HexColor("#627D98")
LINEA = colors.HexColor("#BCCCDC")
ZEBRA = colors.HexColor("#F0F4F8")


# ------------------------------------------------------------------
# Utilidades de formato
# ------------------------------------------------------------------
def numero_comprobante(tipo: str | None, id_venta: int) -> str:
    """B001-00000022 / F001-00000022 (el correlativo es el N° de venta)."""
    serie = SERIES.get((tipo or "").upper(), "V001")
    return f"{serie}-{int(id_venta):08d}"


def nombre_archivo(tipo: str | None, id_venta: int) -> str:
    tipo = (tipo or "").upper()
    if tipo in PREFIJO_ARCHIVO:
        return f"{PREFIJO_ARCHIVO[tipo]}_{numero_comprobante(tipo, id_venta)}.pdf"
    return f"Comprobante_Venta_{id_venta}.pdf"


def _fmt_fecha(valor) -> str:
    return valor.strftime("%d/%m/%Y") if isinstance(valor, (date, datetime)) else str(valor or "")


def _fmt_hora(valor) -> str:
    # MySQL devuelve las columnas TIME como timedelta.
    if isinstance(valor, timedelta):
        s = int(valor.total_seconds())
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
    return str(valor or "")


def _soles(valor) -> str:
    return f"S/ {Decimal(str(valor or 0)):,.2f}"


_UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
             "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho",
             "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
             "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_DECENAS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta",
            9: "noventa"}
_CENTENAS = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
             6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _menor_mil(n: int) -> str:
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    partes = [_CENTENAS[c]] if c else []
    if r:
        if r < 30:
            partes.append(_UNIDADES[r])
        else:
            d, u = divmod(r, 10)
            partes.append(_DECENAS[d] + (f" y {_UNIDADES[u]}" if u else ""))
    return " ".join(partes)


def _apocopar(texto: str) -> str:
    if texto.endswith("veintiuno"):
        return texto[:-9] + "veintiún"
    return texto[:-1] if texto.endswith("uno") else texto


def entero_a_letras(n: int) -> str:
    if n == 0:
        return "cero"
    millones, resto = divmod(n, 1_000_000)
    miles, resto = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("un millón" if millones == 1 else f"{_apocopar(_menor_mil(millones))} millones")
    if miles:
        partes.append("mil" if miles == 1 else f"{_apocopar(_menor_mil(miles))} mil")
    if resto:
        partes.append(_menor_mil(resto))
    return " ".join(partes)


def monto_en_letras(total) -> str:
    total = Decimal(str(total or 0)).quantize(Decimal("0.01"))
    enteros, centimos = divmod(int(total * 100), 100)
    return f"SON: {entero_a_letras(enteros).upper()} CON {centimos:02d}/100 SOLES"


# ------------------------------------------------------------------
# Datos desde MySQL
# ------------------------------------------------------------------
def obtener_datos_venta(id_venta: int) -> dict:
    venta = database.fetch_one(
        """SELECT v.id_venta, v.fecha_venta, v.hora_venta, v.tipo_comprobante,
                  v.subtotal, v.igv, v.total,
                  CONCAT(u.nombres,' ',u.apellidos) AS vendedor,
                  c.nombre_cliente, c.documento AS cliente_doc,
                  c.direccion AS cliente_direccion
           FROM ventas v
           LEFT JOIN usuarios u ON u.id_usuario = v.id_vendedor
           LEFT JOIN clientes c ON c.id_cliente = v.id_cliente
           WHERE v.id_venta = %s""", (id_venta,))
    if not venta:
        raise ValueError(f"La venta N.° {id_venta} no existe.")
    venta["items"] = database.fetch_all(
        """SELECT d.cantidad, d.precio_unitario, d.subtotal_detalle,
                  p.nombre_producto, p.marca
           FROM detalle_venta d
           LEFT JOIN productos p ON p.id_producto = d.id_producto
           WHERE d.id_venta = %s ORDER BY d.id_detalle""", (id_venta,))
    return venta


# ------------------------------------------------------------------
# Construcción del PDF
# ------------------------------------------------------------------
def _estilos() -> dict:
    base = getSampleStyleSheet()["Normal"]
    mk = lambda name, **kw: ParagraphStyle(name, parent=base, **kw)  # noqa: E731
    return {
        "empresa": mk("empresa", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=AZUL),
        "sub": mk("sub", fontSize=8.5, leading=11, textColor=GRIS),
        "txt": mk("txt", fontSize=9, leading=12),
        "lbl": mk("lbl", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=GRIS),
        "caja_ruc": mk("caja_ruc", fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=TA_CENTER),
        "caja_tipo": mk("caja_tipo", fontName="Helvetica-Bold", fontSize=12, leading=16,
                        alignment=TA_CENTER, textColor=colors.white),
        "caja_num": mk("caja_num", fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=TA_CENTER),
        "th": mk("th", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.white, alignment=TA_CENTER),
        "td": mk("td", fontSize=9, leading=12),
        "td_c": mk("td_c", fontSize=9, leading=12, alignment=TA_CENTER),
        "td_r": mk("td_r", fontSize=9, leading=12, alignment=TA_RIGHT),
        "tot_l": mk("tot_l", fontSize=9.5, leading=13, alignment=TA_RIGHT),
        "tot_b": mk("tot_b", fontName="Helvetica-Bold", fontSize=11, leading=14, alignment=TA_RIGHT),
        "letras": mk("letras", fontName="Helvetica-Bold", fontSize=8.5, leading=11),
        "gracias": mk("gracias", fontSize=9, textColor=GRIS, alignment=TA_CENTER),
    }


def _construir_story(d: dict) -> list:
    s = _estilos()
    tipo = (d["tipo_comprobante"] or "").upper()
    titulo_doc = NOMBRES_DOC.get(tipo, "COMPROBANTE DE VENTA")
    numero = numero_comprobante(tipo, d["id_venta"])
    ancho = A4[0] - 36 * mm

    # --- Cabecera: empresa (izq) + caja del comprobante (der) ---
    izq = [Paragraph(EMPRESA["nombre"], s["empresa"]),
           Paragraph(EMPRESA["subtitulo"], s["sub"]), Spacer(1, 3),
           Paragraph(EMPRESA["direccion"], s["txt"]),
           Paragraph(f"Tel.: {EMPRESA['telefono']}", s["txt"])]
    caja = Table([[Paragraph(f"R.U.C. {EMPRESA['ruc']}", s["caja_ruc"])],
                  [Paragraph(titulo_doc, s["caja_tipo"])],
                  [Paragraph(f"N° {numero}", s["caja_num"])]], colWidths=[62 * mm])
    caja.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, AZUL),
        ("BACKGROUND", (0, 1), (-1, 1), AZUL),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    cabecera = Table([[izq, caja]], colWidths=[ancho - 62 * mm, 62 * mm])
    cabecera.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (0, 0), 0)]))

    # --- Datos de la venta y del cliente ---
    cliente = d["nombre_cliente"] or "CLIENTE VARIOS"
    doc_cli = d["cliente_doc"] or "—"
    etiqueta_doc = "RUC" if len(str(d["cliente_doc"] or "")) == 11 else "DNI"
    P = lambda t, st="txt": Paragraph(str(t), s[st])  # noqa: E731
    datos = Table([
        [P("FECHA DE EMISIÓN", "lbl"), P(_fmt_fecha(d["fecha_venta"])), P("HORA", "lbl"), P(_fmt_hora(d["hora_venta"]))],
        [P("CLIENTE", "lbl"), P(cliente), P(f"{etiqueta_doc}", "lbl"), P(doc_cli)],
        [P("DIRECCIÓN", "lbl"), P(d["cliente_direccion"] or "—"), P("VENDEDOR", "lbl"), P(d["vendedor"] or "—")],
        [P("N° DE VENTA", "lbl"), P(d["id_venta"]), P("MONEDA", "lbl"), P("SOLES (PEN)")],
    ], colWidths=[36 * mm, ancho / 2 - 36 * mm + 10 * mm, 24 * mm, ancho / 2 - 24 * mm - 10 * mm])
    datos.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, LINEA), ("BACKGROUND", (0, 0), (-1, -1), ZEBRA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    # --- Detalle ---
    filas = [[P("CANT.", "th"), P("DESCRIPCIÓN", "th"), P("P. UNIT.", "th"), P("SUBTOTAL", "th")]]
    for it in d["items"]:
        desc = it["nombre_producto"] or "Producto eliminado"
        if it["marca"]:
            desc += f" — {it['marca']}"
        filas.append([P(it["cantidad"], "td_c"), P(desc, "td"),
                      P(_soles(it["precio_unitario"]), "td_r"), P(_soles(it["subtotal_detalle"]), "td_r")])
    detalle = Table(filas, colWidths=[20 * mm, ancho - 20 * mm - 32 * mm - 34 * mm, 32 * mm, 34 * mm],
                    repeatRows=1)
    detalle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINEA), ("BOX", (0, 0), (-1, -1), 0.6, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    # --- Totales ---
    totales = Table([
        [P("Subtotal (op. gravada)", "tot_l"), P(_soles(d["subtotal"]), "tot_l")],
        [P("IGV (18%)", "tot_l"), P(_soles(d["igv"]), "tot_l")],
        [P("TOTAL A PAGAR", "tot_b"), P(_soles(d["total"]), "tot_b")],
    ], colWidths=[48 * mm, 34 * mm], hAlign="RIGHT")
    totales.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 1, AZUL), ("BACKGROUND", (0, 2), (-1, 2), ZEBRA),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return [cabecera, Spacer(1, 7 * mm), datos, Spacer(1, 6 * mm), detalle, Spacer(1, 4 * mm),
            totales, Spacer(1, 5 * mm), Paragraph(monto_en_letras(d["total"]), s["letras"]),
            Spacer(1, 14 * mm), Paragraph("¡Gracias por su compra!", s["gracias"])]


def _pie_de_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRIS)
    canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
    canvas.drawString(18 * mm, 11.5 * mm,
                      f"Generado por el Sistema de Inventario el {datetime.now():%d/%m/%Y %H:%M}")
    canvas.drawRightString(A4[0] - 18 * mm, 11.5 * mm, f"Página {doc.page}")
    canvas.restoreState()


def generar_comprobante_pdf(id_venta: int, carpeta: Path | str | None = None) -> Path:
    """Crea (o regenera) el PDF de una venta y devuelve su ruta."""
    datos = obtener_datos_venta(id_venta)
    carpeta = Path(carpeta) if carpeta else CARPETA_COMPROBANTES
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre_archivo(datos["tipo_comprobante"], id_venta)

    def construir(destino: Path):
        doc = SimpleDocTemplate(
            str(destino), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=16 * mm, bottomMargin=22 * mm,
            title=f"{NOMBRES_DOC.get((datos['tipo_comprobante'] or '').upper(), 'Comprobante')} "
                  f"{numero_comprobante(datos['tipo_comprobante'], id_venta)}",
            author=EMPRESA["nombre"])
        doc.build(_construir_story(datos), onFirstPage=_pie_de_pagina, onLaterPages=_pie_de_pagina)

    try:
        construir(ruta)
    except PermissionError:
        # El PDF anterior está abierto en un visor: se guarda una copia con hora.
        ruta = ruta.with_name(f"{ruta.stem}_{datetime.now():%H%M%S}.pdf")
        construir(ruta)
    return ruta
