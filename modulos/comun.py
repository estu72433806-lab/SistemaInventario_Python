"""Utilidades compartidas por los módulos: errores MySQL, logs, abrir archivos."""

import os
import subprocess
import sys
from decimal import Decimal

from mysql.connector import Error as MySQLError

import database

IGV_RATE = Decimal("0.18")
CENT = Decimal("0.01")

_MSG_CONEXION = ("No se pudo conectar con MySQL Server.\n"
                 "Verifica que el servicio esté iniciado y revisa DB_CONFIG en database.py.")
_MSG_MIGRACION = ("La base de datos aún no tiene las columnas nuevas.\n"
                  "Ejecuta una vez el script sql/migracion_proveedores_ventas.sql en MySQL.")

ERRORES_MYSQL = {
    2002: _MSG_CONEXION,
    2003: _MSG_CONEXION,
    2006: "Se perdió la conexión con MySQL. Intenta de nuevo.",
    1045: "Usuario o contraseña de MySQL incorrectos (revisa database.py).",
    1049: "La base de datos no existe. Ejecuta sql/inventario_computadoras_mysql.sql.",
    1054: _MSG_MIGRACION,
    1146: _MSG_MIGRACION,
    1062: "Ya existe un registro con ese valor único (duplicado).",
    1451: "No se puede eliminar: el registro está relacionado con otros datos.",
    1452: "El dato relacionado indicado no existe.",
    1205: "La base de datos está ocupada. Intenta nuevamente en unos segundos.",
    1406: "Uno de los textos es demasiado largo para el campo.",
}


def mensaje_error_mysql(exc: Exception) -> str:
    """Convierte una excepción de MySQL en un mensaje claro para el usuario."""
    errno = getattr(exc, "errno", None)
    if errno in ERRORES_MYSQL:
        return ERRORES_MYSQL[errno]
    detalle = getattr(exc, "msg", None) or str(exc)
    return f"Error de base de datos ({errno}): {detalle}"


def escape_like(texto: str) -> str:
    """Escapa % _ \\ para usar el texto dentro de un LIKE literal."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def registrar_log(id_usuario, accion, tabla, id_registro):
    """Guarda en logs_actividad. Un fallo del log nunca debe bloquear la operación."""
    try:
        database.execute(
            "INSERT INTO logs_actividad(id_usuario,accion,tabla_afectada,id_registro,ip_usuario) "
            "VALUES(%s,%s,%s,%s,'127.0.0.1')",
            (id_usuario, accion, tabla, id_registro),
        )
    except MySQLError:
        pass


def abrir_archivo(ruta) -> None:
    """Abre un archivo con la aplicación predeterminada del sistema."""
    ruta = str(ruta)
    if hasattr(os, "startfile"):          # Windows
        os.startfile(ruta)                # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])
