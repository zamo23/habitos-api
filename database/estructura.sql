-- phpMyAdmin SQL Dump
-- Versión 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Tiempo de generación: 2025-09-01 22:09:03
-- Versión del servidor: 10.11.10-MariaDB
-- Versión de PHP: 8.4.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- Configuración del conjunto de caracteres
SET NAMES utf8mb4;

-- Base de datos: `habitos`
CREATE DATABASE IF NOT EXISTS `habitos` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `habitos`;

-- -------------------------------------
-- Estructura de la tabla `usuarios`
-- Almacena información de los usuarios
-- -------------------------------------
CREATE TABLE `usuarios` (
  `id_clerk` VARCHAR(191) NOT NULL,
  `correo` VARCHAR(191) DEFAULT NULL,
  `nombre_completo` VARCHAR(191) DEFAULT NULL,
  `url_imagen` TEXT DEFAULT NULL,
  `idioma` VARCHAR(10) DEFAULT 'es',
  `zona_horaria` VARCHAR(50) DEFAULT 'UTC',
  `cierre_dia_hora` TINYINT DEFAULT 0,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_clerk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `planes`
-- Almacena detalles de los planes de suscripción
-- -------------------------------------
CREATE TABLE `planes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(50) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `precio_centavos` INT NOT NULL DEFAULT 0,
  `moneda` CHAR(3) NOT NULL DEFAULT 'USD',
  `max_habitos` INT DEFAULT NULL,
  `permite_grupos` TINYINT(1) NOT NULL DEFAULT 0,
  `descripcion` TEXT DEFAULT NULL,
  `activo` TINYINT(1) NOT NULL DEFAULT 1,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `suscripciones`
-- Gestiona las suscripciones de los usuarios
-- -------------------------------------
CREATE TABLE `suscripciones` (
  `id` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `id_plan` INT NOT NULL,
  `estado` ENUM('activa', 'cancelada', 'vencida') NOT NULL DEFAULT 'activa',
  `ciclo` ENUM('gratuito', 'mensual', 'anual') DEFAULT NULL,
  `es_actual` TINYINT(1) NOT NULL DEFAULT 1,
  `periodo_inicio` DATETIME DEFAULT NULL,
  `periodo_fin` DATETIME DEFAULT NULL,
  `cancelar_en` DATETIME DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_sub_actual_por_usuario` (`id_clerk`, `es_actual`),
  KEY `idx_sub_usuario` (`id_clerk`),
  KEY `idx_sub_estado` (`estado`),
  CONSTRAINT `fk_sub_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE,
  CONSTRAINT `fk_sub_plan` FOREIGN KEY (`id_plan`) REFERENCES `planes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Disparador para `usuarios` para asignar suscripción por defecto
-- -------------------------------------
DELIMITER $$
CREATE TRIGGER `trg_usuarios_after_insert` AFTER INSERT ON `usuarios` FOR EACH ROW
BEGIN
  DECLARE v_plan_id INT;
  SELECT id INTO v_plan_id
  FROM planes
  WHERE codigo = 'gratis' AND activo = 1
  LIMIT 1;
  
  UPDATE suscripciones
  SET es_actual = 0
  WHERE id_clerk = NEW.id_clerk;
  
  INSERT INTO suscripciones (
    id, id_clerk, id_plan, estado, ciclo, es_actual,
    periodo_inicio, periodo_fin, cancelar_en
  ) VALUES (
    UUID(), NEW.id_clerk, v_plan_id, 'activa', 'gratuito', 1,
    NULL, NULL, NULL
  );
END $$
DELIMITER ;

-- -------------------------------------
-- Estructura de la tabla `grupos`
-- Almacena información de los grupos
-- -------------------------------------
CREATE TABLE `grupos` (
  `id` CHAR(36) NOT NULL,
  `id_propietario` VARCHAR(191) NOT NULL,
  `nombre` VARCHAR(120) NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_grupo_propietario` (`id_propietario`),
  CONSTRAINT `fk_grupo_propietario` FOREIGN KEY (`id_propietario`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `grupo_miembros`
-- Gestiona los miembros de los grupos
-- -------------------------------------
CREATE TABLE `grupo_miembros` (
  `id_grupo` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `rol` ENUM('propietario', 'administrador', 'miembro') NOT NULL DEFAULT 'miembro',
  `fecha_union` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_grupo`, `id_clerk`),
  KEY `fk_miembro_usuario` (`id_clerk`),
  CONSTRAINT `fk_miembro_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_miembro_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `grupo_invitaciones`
-- Gestiona las invitaciones a grupos
-- -------------------------------------
CREATE TABLE `grupo_invitaciones` (
  `id` CHAR(36) NOT NULL,
  `id_grupo` CHAR(36) NOT NULL,
  `id_invitador` VARCHAR(191) NOT NULL,
  `correo_invitado` VARCHAR(191) NOT NULL,
  `token` CHAR(64) NOT NULL,
  `estado` ENUM('pendiente', 'aceptada', 'expirada', 'revocada') NOT NULL DEFAULT 'pendiente',
  `expira_en` DATETIME DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_inv_invitador` (`id_invitador`),
  KEY `idx_inv_grupo_estado` (`id_grupo`, `estado`),
  CONSTRAINT `fk_inv_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_inv_invitador` FOREIGN KEY (`id_invitador`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `habitos`
-- Almacena información de los hábitos
-- -------------------------------------
CREATE TABLE `habitos` (
  `id` CHAR(36) NOT NULL,
  `id_propietario` VARCHAR(191) NOT NULL,
  `id_grupo` CHAR(36) DEFAULT NULL,
  `titulo` VARCHAR(255) NOT NULL,
  `tipo` ENUM('hacer', 'dejar') NOT NULL,
  `frecuencia_diaria` INT NOT NULL DEFAULT 1,
  `archivado` TINYINT(1) NOT NULL DEFAULT 0,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_habito_propietario` (`id_propietario`),
  KEY `idx_habito_grupo` (`id_grupo`),
  CONSTRAINT `fk_habito_propietario` FOREIGN KEY (`id_propietario`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE,
  CONSTRAINT `fk_habito_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `habito_rachas`
-- Registra las rachas de los hábitos
-- -------------------------------------
CREATE TABLE `habito_rachas` (
  `id_habito` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `racha_actual` INT NOT NULL DEFAULT 0,
  `mejor_racha` INT NOT NULL DEFAULT 0,
  `ultima_fecha` DATE DEFAULT NULL,
  `ultima_revision_local` DATE DEFAULT NULL,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_habito`, `id_clerk`),
  KEY `fk_racha_usuario` (`id_clerk`),
  CONSTRAINT `fk_racha_habito` FOREIGN KEY (`id_habito`) REFERENCES `habitos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_racha_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `habito_registros`
-- Registra la finalización de hábitos
-- -------------------------------------
CREATE TABLE `habito_registros` (
  `id` CHAR(36) NOT NULL,
  `id_habito` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `fecha` DATE NOT NULL,
  `fecha_hora_local` DATETIME NOT NULL,
  `estado` ENUM('exito', 'fallo') NOT NULL,
  `comentario` TEXT DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_registro` (`id_habito`, `id_clerk`, `fecha`),
  KEY `idx_reg_fecha` (`fecha`),
  KEY `idx_reg_fecha_hora_local` (`fecha_hora_local`),
  KEY `idx_reg_usuario` (`id_clerk`),
  KEY `idx_reg_habito_fecha` (`id_habito`, `fecha`),
  CONSTRAINT `fk_reg_habito` FOREIGN KEY (`id_habito`) REFERENCES `habitos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reg_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `notificaciones`
-- Almacena notificaciones
-- -------------------------------------
CREATE TABLE `notificaciones` (
  `id` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `tipo` ENUM('recordatorio', 'logro', 'sistema') NOT NULL,
  `datos_json` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (JSON_VALID(`datos_json`)),
  `programada_para` DATETIME DEFAULT NULL,
  `enviada_en` DATETIME DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_notif_usuario` (`id_clerk`),
  CONSTRAINT `fk_notif_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `pagos_inbox`
-- Almacena detalles de pagos entrantes
-- -------------------------------------
CREATE TABLE `pagos_inbox` (
  `id` CHAR(36) NOT NULL,
  `remitente` VARCHAR(191) NOT NULL,
  `monto_texto` VARCHAR(50) NOT NULL,
  `codigo_seguridad` VARCHAR(191) NOT NULL,
  `fecha_hora` DATETIME NOT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_inbox_idem` (`codigo_seguridad`, `fecha_hora`, `monto_texto`),
  KEY `idx_inbox_fecha` (`fecha_hora`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la tabla `pagos_historial`
-- Almacena el historial de pagos
-- -------------------------------------
CREATE TABLE `pagos_historial` (
  `id` CHAR(36) NOT NULL,
  `id_pago_inbox` CHAR(36) NOT NULL,
  `id_clerk` VARCHAR(191) NOT NULL,
  `id_plan` INT NOT NULL,
  `monto_centavos` INT NOT NULL,
  `moneda` CHAR(3) NOT NULL,
  `estado` ENUM('confirmado', 'rechazado') NOT NULL DEFAULT 'confirmado',
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `fecha_aplicacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_hist_por_inbox` (`id_pago_inbox`),
  KEY `idx_hist_usuario` (`id_clerk`),
  KEY `idx_hist_plan` (`id_plan`),
  KEY `idx_hist_estado` (`estado`),
  CONSTRAINT `fk_hist_inbox` FOREIGN KEY (`id_pago_inbox`) REFERENCES `pagos_inbox` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_plan` FOREIGN KEY (`id_plan`) REFERENCES `planes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- -------------------------------------
-- Estructura de la vista `vista_suscripcion_actual`
-- Muestra los detalles de la suscripción actual
-- -------------------------------------
CREATE OR REPLACE VIEW `vista_suscripcion_actual` AS
SELECT 
  s.id AS id_suscripcion,
  s.id_clerk,
  p.codigo AS plan_codigo,
  p.nombre AS plan_nombre,
  p.precio_centavos,
  p.moneda,
  p.max_habitos,
  p.permite_grupos,
  s.estado,
  s.ciclo,
  s.periodo_inicio,
  s.periodo_fin,
  s.es_actual,
  s.fecha_creacion,
  s.fecha_actualizacion
FROM suscripciones s
JOIN planes p ON p.id = s.id_plan
WHERE s.es_actual = 1;

COMMIT;