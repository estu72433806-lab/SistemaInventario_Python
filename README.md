# Sistema de Inventario - Python + Tkinter + MySQL Server

Conversión del sistema PHP original a una **aplicación de escritorio**.
No se abre en Chrome/Edge y no necesita un servidor web.

## Tecnologías
- Python 3
- Tkinter (incluido con Python en Windows)
- MySQL Server
- mysql-connector-python

## 1. Crear la base de datos
1. Abre **MySQL Server** (puedes usar MySQL Workbench).
2. Abre el archivo `sql/inventario_computadoras_mysql.sql`.
3. Ejecuta todo el script.
4. El script crea la base `inventario_computadoras`, tablas y datos de ejemplo.

## 2. Configurar la conexión
Abre `database.py` y revisa:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "inventario_computadoras",
}
```

Si tu usuario `root` tiene contraseña, colócala en `password`.

### 1.b Si ya tenías la base creada (migración)
En vez de recrearla, ejecuta **una sola vez** `sql/migracion_proveedores_ventas.sql`.
Agrega: RUC/contacto/correo/estado en proveedores, DNI/RUC y dirección en clientes,
`id_cliente` en ventas y la tabla `detalle_ingreso`.

## 3. Instalar las librerías
En la terminal de VS Code:

```powershell
python -m pip install -r requirements.txt
```

## 4. Ejecutar
En VS Code abre esta carpeta y ejecuta:

```powershell
python app.py
```

Se abrirá una **ventana de Windows**, no un navegador.

## Usuario de prueba
- Correo: `admin@sistema.com`
- Contraseña: `1234`

Las cuentas del archivo SQL se conservan; para la versión de escritorio las contraseñas iniciales de las cuentas precargadas se establecen en `1234` y se guardan como SHA-256. Puedes crear más usuarios desde el módulo Usuarios.

## Módulos incluidos
- Inicio de sesión
- Dashboard
- Productos: registrar, editar, buscar
- Clientes: registrar, editar, buscar
- Proveedores: ficha completa (RUC/DNI único validado), búsqueda en tiempo real, filtro por estado, editar, eliminación lógica, ver detalles/historial, exportar a Excel y PDF
- Inventario: estado, porcentaje y stock bajo
- Ventas: múltiples productos, cliente, IGV, total, transacción y descuento de stock; **comprobante PDF** automático en `/comprobantes` (reimprimible desde la tabla)
- Reportes: ventas por fecha, productos vendidos y stock bajo
- Usuarios
- Registro de actividad

## Importante
El archivo SQL original provenía de un dump de phpMyAdmin/MariaDB. Se preparó un SQL limpio para **MySQL Server**, eliminando dependencias del servidor web/PHP y dejando las reglas que ahora maneja Python.
