-- =============================================================
-- SISTEMA DE INVENTARIO Y CONTROL DE ALMACEN
-- VERSION DE ESCRITORIO: PYTHON + TKINTER + MYSQL SERVER
-- =============================================================

CREATE DATABASE IF NOT EXISTS inventario_computadoras
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE inventario_computadoras;

SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS vista_ventas_diarias;
DROP VIEW IF EXISTS vista_productos_estadisticas;
DROP VIEW IF EXISTS vista_productos_completo;

DROP TABLE IF EXISTS detalle_venta;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS inventario;
DROP TABLE IF EXISTS logs_actividad;
DROP TABLE IF EXISTS detalle_ingreso;
DROP TABLE IF EXISTS ingreso_mercaderia;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS proveedores;
DROP TABLE IF EXISTS usuarios;

SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------------
-- USUARIOS
-- La version de escritorio usa SHA-256 desde Python.
-- Las cuentas precargadas usan temporalmente la clave: 1234
-- -------------------------------------------------------------
CREATE TABLE usuarios (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    nombres VARCHAR(60) NOT NULL,
    apellidos VARCHAR(60) NOT NULL,
    correo VARCHAR(80) NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'vendedor',
    estado CHAR(1) NOT NULL DEFAULT 'A',
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuarios_correo (correo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO usuarios (id_usuario,nombres,apellidos,correo,contrasena,rol,estado) VALUES
(1,'CORDOVA','ALBERTO','ccalbert980@gmail.com','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','ADMIN','A'),
(2,'CORDOVA','ALBERTO','estu72433806@institutobolivar.edu.pe','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A'),
(3,'jose','lopez','jose@123','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A'),
(4,'EVER','PEÑA CORDOVA','PENA@123','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','admin','A'),
(8,'CARLOS','CORDOVA CORDOVA','car@123.com','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A'),
(9,'Manuel','gutierres','manuel@124','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A'),
(10,'Demo','Usuario','demo@sistema.com','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A'),
(11,'Admin','Sistema','admin@sistema.com','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','admin','A'),
(15,'Camila','Suares','camila.@123','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','vendedor','A');

-- -------------------------------------------------------------
-- CLIENTES
-- -------------------------------------------------------------
CREATE TABLE clientes (
    id_cliente INT NOT NULL AUTO_INCREMENT,
    nombre_cliente VARCHAR(100) NULL,
    documento VARCHAR(15) NULL,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(80) NULL,
    direccion VARCHAR(150) NULL,
    PRIMARY KEY (id_cliente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO clientes (id_cliente,nombre_cliente,telefono,correo) VALUES
(1,'Diomira Cordova Montalvan','931784972','deo@gmail.com123'),
(2,'Carlos Pérez Rojas','987654321','carlos@email.com'),
(3,'María Gómez Silva','976543210','maria@email.com'),
(4,'Juan Castillo Flores','965432109','juan@email.com'),
(5,'Ana Torres Vargas','954321098','ana@email.com'),
(6,'Pedro Luna Sánchez','943210987','pedro@email.com'),
(7,'Roberto Gómez Torres','932145678','roberto@email.com'),
(8,'Laura Sánchez Díaz','921034567','laura@email.com'),
(9,'Miguel Ángel Ruiz','910923456','miguel@email.com'),
(10,'Carmen Flores Rojas','987612345','carmen@email.com'),
(11,'Jorge Luis Mendoza','965478321','jorge@email.com');

-- Clientes de ejemplo con documento (para probar boletas y facturas)
UPDATE clientes SET documento='20100000017', direccion='Av. Larco 345, Miraflores, Lima' WHERE id_cliente=2;
UPDATE clientes SET documento='45871236',   direccion='Jr. Los Pinos 120, Surco, Lima'    WHERE id_cliente=3;
UPDATE clientes SET documento='20200000022', direccion='Calle Comercio 88, Arequipa'       WHERE id_cliente=4;

-- -------------------------------------------------------------
-- PROVEEDORES
-- -------------------------------------------------------------
CREATE TABLE proveedores (
    id_proveedor INT NOT NULL AUTO_INCREMENT,
    ruc VARCHAR(11) NOT NULL,
    razon_social VARCHAR(100) NOT NULL,
    contacto VARCHAR(100) NULL,
    correo VARCHAR(80) NULL,
    telefono VARCHAR(20) NULL,
    direccion VARCHAR(150) NULL,
    estado CHAR(1) NOT NULL DEFAULT 'A',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_proveedor),
    UNIQUE KEY uq_proveedores_ruc (ruc),
    KEY idx_proveedores_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO proveedores (id_proveedor,ruc,razon_social,contacto,correo,telefono,direccion,estado) VALUES
(1,'20100000017','venta de celulares','Luis Ramos','ventas@celulares.pe','987623456','callao_lima','A'),
(2,'20200000022','Tecnología Total SAC','María Quispe','contacto@tecnototal.pe','942345678','Av. Principal 123, Lima','A'),
(3,'20300000038','Computech EIRL','Jorge Salas','ventas@computech.pe','932456789','Calle Los Andes 456, Arequipa','A'),
(4,'20400000043','Importaciones PC Pro','Ana Villanueva','info@pcpro.pe','921567890','Av. Industrial 789, Trujillo','A'),
(5,'20500000059','Soluciones Digitales','Carlos Huamán','hola@soldigitales.pe','910678901','Calle Central 321, Cusco','A'),
(6,'20600000064','Intel Corporation','Representante Intel','peru@intel.example.com','987654321','Av. Tecnológica 150, Lima','A'),
(7,'20700000070','NVIDIA Latin America','Representante NVIDIA','peru@nvidia.example.com','976543210','Calle Innovación 200, Lima','A'),
(8,'20800000085','Seagate Technology','Representante Seagate','peru@seagate.example.com','965432109','Av. Industrial 300, Lima','I');

-- -------------------------------------------------------------
-- PRODUCTOS
-- -------------------------------------------------------------
CREATE TABLE productos (
    id_producto INT NOT NULL AUTO_INCREMENT,
    nombre_producto VARCHAR(80) NOT NULL,
    categoria VARCHAR(40) NULL,
    marca VARCHAR(40) NULL,
    precio_venta DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_producto),
    KEY idx_productos_categoria (categoria),
    KEY idx_productos_stock (stock_actual, stock_minimo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO productos (id_producto,nombre_producto,categoria,marca,precio_venta,stock_actual,stock_minimo) VALUES
(1,'Windows 11 Pro','Laptops','Lenovo',2400.00,2399,10),
(2,'Laptop HP AI','Laptops','HP',2200.00,1999,2),
(3,'Laptop Dell Inspiron 15','Laptops','Dell',2800.00,15,5),
(4,'PC Gamer Intel i7 12th','Computadoras','Asus',3500.00,8,3),
(5,'Monitor Samsung 24" LED','Computadoras','Samsung',650.00,12,4),
(6,'Mouse Logitech G502 Hero','Periféricos','Logitech',120.00,4,5),
(7,'Teclado Mecánico Redragon','Periféricos','Redragon',85.00,0,2),
(8,'Disco SSD 500GB Kingston','Componentes','Kingston',95.00,3,5),
(9,'Memoria RAM 16GB Corsair','Componentes','Corsair',180.00,1,2),
(10,'Impresora HP LaserJet Pro','Periféricos','HP',450.00,2,3),
(11,'Tablet Samsung Galaxy Tab','Laptops','Samsung',1200.00,7,3),
(12,'Laptop MacBook Air M2','Laptops','Apple',4200.00,4,2),
(13,'Procesador Intel Core i9','Componentes','Intel',1800.00,2,3),
(14,'Tarjeta Gráfica RTX 4060','Componentes','NVIDIA',2500.00,1,2),
(15,'Disco Duro Externo 2TB','Componentes','Seagate',350.00,6,4),
(16,'Auriculares Gamer Astro','Periféricos','Astro',650.00,5,3),
(17,'Cámara Web 4K Logitech','Periféricos','Logitech',280.00,2,2);

-- -------------------------------------------------------------
-- INVENTARIO
-- Se inicializa con el stock actual de productos.
-- -------------------------------------------------------------
CREATE TABLE inventario (
    id_inventario INT NOT NULL AUTO_INCREMENT,
    id_producto INT NOT NULL,
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_inventario),
    UNIQUE KEY uq_inventario_producto (id_producto),
    CONSTRAINT fk_inventario_producto FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO inventario (id_producto,stock_actual,stock_minimo)
SELECT id_producto,stock_actual,stock_minimo FROM productos ORDER BY id_producto;

-- -------------------------------------------------------------
-- INGRESO DE MERCADERIA
-- -------------------------------------------------------------
CREATE TABLE ingreso_mercaderia (
    id_ingreso INT NOT NULL AUTO_INCREMENT,
    fecha_ingreso DATE NULL,
    id_proveedor INT NULL,
    total_ingreso DECIMAL(10,2) NULL,
    PRIMARY KEY (id_ingreso),
    KEY idx_ingreso_proveedor (id_proveedor),
    CONSTRAINT fk_ingreso_proveedor FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- DETALLE DE INGRESO (productos suministrados por proveedor)
-- -------------------------------------------------------------
CREATE TABLE detalle_ingreso (
    id_detalle_ingreso INT NOT NULL AUTO_INCREMENT,
    id_ingreso INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    costo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (id_detalle_ingreso),
    KEY idx_detingreso_ingreso (id_ingreso),
    KEY idx_detingreso_producto (id_producto),
    CONSTRAINT fk_detingreso_ingreso FOREIGN KEY (id_ingreso) REFERENCES ingreso_mercaderia(id_ingreso) ON DELETE CASCADE,
    CONSTRAINT fk_detingreso_producto FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- VENTAS
-- -------------------------------------------------------------
CREATE TABLE ventas (
    id_venta INT NOT NULL AUTO_INCREMENT,
    fecha_venta DATE NULL,
    hora_venta TIME NULL,
    id_vendedor INT NULL,
    id_cliente INT NULL,
    tipo_comprobante VARCHAR(15) NULL,
    subtotal DECIMAL(10,2) NULL,
    igv DECIMAL(10,2) NULL,
    total DECIMAL(10,2) NULL,
    PRIMARY KEY (id_venta),
    KEY idx_ventas_fecha (fecha_venta),
    KEY idx_ventas_vendedor (id_vendedor),
    KEY idx_ventas_cliente (id_cliente),
    CONSTRAINT fk_ventas_vendedor FOREIGN KEY (id_vendedor) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    CONSTRAINT fk_ventas_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ventas (id_venta,fecha_venta,hora_venta,id_vendedor,tipo_comprobante,subtotal,igv,total) VALUES
(1,'2026-06-03','04:19:00',2,'FACTURA',2400.00,432.00,2832.00),
(2,'2026-06-09','23:59:37',3,'BOLETA',2200.00,396.00,2596.00),
(3,'2026-06-10','10:30:00',9,'BOLETA',2800.00,504.00,3304.00),
(4,'2026-06-11','11:45:00',2,'FACTURA',3500.00,630.00,4130.00),
(5,'2026-06-12','14:20:00',9,'BOLETA',650.00,117.00,767.00),
(6,'2026-06-13','09:15:00',3,'FACTURA',1200.00,216.00,1416.00),
(7,'2026-06-14','16:30:00',9,'BOLETA',450.00,81.00,531.00),
(8,'2026-06-15','12:00:00',2,'FACTURA',4200.00,756.00,4956.00),
(9,'2026-06-16','15:10:00',3,'BOLETA',180.00,32.40,212.40),
(10,'2026-06-17','08:45:00',9,'FACTURA',2800.00,504.00,3304.00),
(11,'2026-06-18','13:20:00',2,'BOLETA',95.00,17.10,112.10),
(12,'2026-06-19','10:00:00',3,'FACTURA',120.00,21.60,141.60),
(13,'2026-06-20','09:30:00',9,'BOLETA',1800.00,324.00,2124.00),
(14,'2026-06-20','11:15:00',2,'FACTURA',2500.00,450.00,2950.00),
(15,'2026-06-21','14:45:00',3,'BOLETA',350.00,63.00,413.00),
(16,'2026-06-21','16:20:00',9,'FACTURA',650.00,117.00,767.00),
(17,'2026-06-22','10:00:00',2,'BOLETA',280.00,50.40,330.40),
(18,'2026-06-22','12:30:00',3,'FACTURA',4200.00,756.00,4956.00),
(19,'2026-06-22','15:10:00',9,'BOLETA',1800.00,324.00,2124.00),
(20,'2026-06-23','08:45:00',2,'FACTURA',2500.00,450.00,2950.00),
(21,'2026-06-23','11:00:00',3,'BOLETA',350.00,63.00,413.00),
(22,'2026-06-23','14:30:00',9,'FACTURA',280.00,50.40,330.40);

-- -------------------------------------------------------------
-- DETALLE DE VENTAS
-- -------------------------------------------------------------
CREATE TABLE detalle_venta (
    id_detalle INT NOT NULL AUTO_INCREMENT,
    id_venta INT NULL,
    id_producto INT NULL,
    cantidad INT NULL,
    precio_unitario DECIMAL(10,2) NULL,
    subtotal_detalle DECIMAL(10,2) NULL,
    PRIMARY KEY (id_detalle),
    KEY idx_detalle_venta (id_venta),
    KEY idx_detalle_producto (id_producto),
    CONSTRAINT fk_detalle_venta FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO detalle_venta (id_detalle,id_venta,id_producto,cantidad,precio_unitario,subtotal_detalle) VALUES
(1,1,1,1,2400.00,2400.00),
(2,2,2,1,2200.00,2200.00),
(3,3,3,1,2800.00,2800.00),
(4,4,4,1,3500.00,3500.00),
(5,5,5,1,650.00,650.00),
(6,6,9,1,1200.00,1200.00),
(7,7,8,1,450.00,450.00),
(8,8,10,1,4200.00,4200.00),
(9,9,7,1,180.00,180.00),
(10,10,3,1,2800.00,2800.00),
(11,11,6,1,95.00,95.00),
(12,12,6,1,120.00,120.00),
(13,13,13,1,1800.00,1800.00),
(14,14,14,1,2500.00,2500.00),
(15,15,15,1,350.00,350.00),
(16,16,16,1,650.00,650.00),
(17,17,17,1,280.00,280.00),
(18,18,12,1,4200.00,4200.00),
(19,19,13,1,1800.00,1800.00),
(20,20,14,1,2500.00,2500.00),
(21,21,15,1,350.00,350.00),
(22,22,17,1,280.00,280.00);

-- -------------------------------------------------------------
-- LOGS
-- -------------------------------------------------------------
CREATE TABLE logs_actividad (
    id_log INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NULL,
    accion VARCHAR(100) NULL,
    tabla_afectada VARCHAR(50) NULL,
    id_registro INT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_usuario VARCHAR(45) NULL,
    PRIMARY KEY (id_log),
    KEY idx_logs_usuario (id_usuario),
    CONSTRAINT fk_logs_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO logs_actividad (id_log,id_usuario,accion,tabla_afectada,id_registro,fecha_hora,ip_usuario) VALUES
(1,9,'Inicio de sesión','usuarios',9,'2026-06-23 17:17:52','127.0.0.1'),
(2,9,'Registró venta','ventas',1,'2026-06-23 17:17:52','127.0.0.1'),
(3,2,'Inicio de sesión','usuarios',2,'2026-06-23 17:17:52','127.0.0.1'),
(4,9,'Actualizó producto','productos',2,'2026-06-23 17:17:52','127.0.0.1'),
(5,3,'Registró cliente','clientes',2,'2026-06-23 17:17:52','127.0.0.1'),
(6,1,'Actualizó producto','productos',17,'2026-06-30 22:08:08','127.0.0.1'),
(7,1,'Actualizó producto','productos',17,'2026-06-30 22:15:20','127.0.0.1');

-- -------------------------------------------------------------
-- VISTAS PARA REPORTES
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vista_productos_completo AS
SELECT
    p.id_producto,
    p.nombre_producto,
    p.categoria,
    p.marca,
    p.precio_venta,
    p.stock_actual,
    p.stock_minimo,
    COALESCE(SUM(d.cantidad),0) AS total_vendido,
    COALESCE(SUM(d.subtotal_detalle),0) AS total_ingreso,
    COUNT(d.id_detalle) AS veces_vendido,
    CASE
        WHEN p.stock_actual <= p.stock_minimo THEN 'CRITICO'
        WHEN p.stock_actual <= p.stock_minimo * 1.5 THEN 'BAJO'
        ELSE 'NORMAL'
    END AS estado_stock,
    (p.stock_minimo - p.stock_actual) AS diferencia_stock
FROM productos p
LEFT JOIN detalle_venta d ON d.id_producto = p.id_producto
GROUP BY p.id_producto;

CREATE OR REPLACE VIEW vista_productos_estadisticas AS
SELECT * FROM vista_productos_completo;

CREATE OR REPLACE VIEW vista_ventas_diarias AS
SELECT
    fecha_venta AS fecha,
    COUNT(*) AS total_ventas,
    COALESCE(SUM(total),0) AS ingreso_total,
    COALESCE(SUM(subtotal),0) AS subtotal_total,
    COALESCE(SUM(igv),0) AS igv_total,
    COALESCE(AVG(total),0) AS promedio_venta
FROM ventas
GROUP BY fecha_venta
ORDER BY fecha_venta DESC;

-- Ajustar AUTO_INCREMENT después de restaurar los IDs originales.
ALTER TABLE usuarios AUTO_INCREMENT = 16;
ALTER TABLE clientes AUTO_INCREMENT = 12;
ALTER TABLE proveedores AUTO_INCREMENT = 9;
ALTER TABLE productos AUTO_INCREMENT = 18;
ALTER TABLE inventario AUTO_INCREMENT = 18;
ALTER TABLE ventas AUTO_INCREMENT = 23;
ALTER TABLE detalle_venta AUTO_INCREMENT = 23;
ALTER TABLE logs_actividad AUTO_INCREMENT = 8;

-- =============================================================
-- FIN
-- =============================================================
