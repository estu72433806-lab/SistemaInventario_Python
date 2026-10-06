-- =============================================================
-- MIGRACION para bases YA CREADAS (ejecutar UNA sola vez)
--   * Proveedores: RUC/DNI, contacto, correo, estado
--   * Clientes: DNI/RUC y direccion (necesarios para facturas)
--   * Ventas: id_cliente (cliente del comprobante)
--   * detalle_ingreso: productos suministrados por proveedor
-- Si instalas desde cero usa inventario_computadoras_mysql.sql (ya lo incluye).
-- =============================================================
USE inventario_computadoras;

-- ---------- PROVEEDORES ----------
ALTER TABLE proveedores
  ADD COLUMN ruc            VARCHAR(11)  NULL AFTER id_proveedor,
  ADD COLUMN contacto       VARCHAR(100) NULL AFTER razon_social,
  ADD COLUMN correo         VARCHAR(80)  NULL AFTER contacto,
  ADD COLUMN estado         CHAR(1)      NOT NULL DEFAULT 'A' AFTER direccion,
  ADD COLUMN fecha_registro DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD UNIQUE KEY uq_proveedores_ruc (ruc),
  ADD KEY idx_proveedores_estado (estado);

-- Los proveedores antiguos quedan con RUC vacio (NULL): la app mostrara
-- "pendiente" y exigira el RUC/DNI la proxima vez que se editen.
-- Cuando todos tengan RUC puedes volverlo obligatorio tambien en MySQL:
-- ALTER TABLE proveedores MODIFY ruc VARCHAR(11) NOT NULL;

-- ---------- CLIENTES ----------
ALTER TABLE clientes
  ADD COLUMN documento VARCHAR(15)  NULL AFTER nombre_cliente,
  ADD COLUMN direccion VARCHAR(150) NULL AFTER correo;

-- ---------- VENTAS ----------
ALTER TABLE ventas
  ADD COLUMN id_cliente INT NULL AFTER id_vendedor,
  ADD KEY idx_ventas_cliente (id_cliente),
  ADD CONSTRAINT fk_ventas_cliente FOREIGN KEY (id_cliente)
      REFERENCES clientes(id_cliente) ON DELETE SET NULL;

-- ---------- DETALLE DE INGRESO (productos por proveedor) ----------
CREATE TABLE IF NOT EXISTS detalle_ingreso (
    id_detalle_ingreso INT NOT NULL AUTO_INCREMENT,
    id_ingreso INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    costo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (id_detalle_ingreso),
    KEY idx_detingreso_ingreso (id_ingreso),
    KEY idx_detingreso_producto (id_producto),
    CONSTRAINT fk_detingreso_ingreso FOREIGN KEY (id_ingreso)
        REFERENCES ingreso_mercaderia(id_ingreso) ON DELETE CASCADE,
    CONSTRAINT fk_detingreso_producto FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
