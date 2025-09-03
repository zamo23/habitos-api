-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 03-09-2025 a las 19:57:36
-- Versión del servidor: 10.4.28-MariaDB
-- Versión de PHP: 8.0.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `habitos`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id_clerk` varchar(191) NOT NULL,
  `correo` varchar(191) DEFAULT NULL,
  `nombre_completo` varchar(191) DEFAULT NULL,
  `url_imagen` text DEFAULT NULL,
  `idioma` varchar(10) DEFAULT 'es',
  `zona_horaria` varchar(50) DEFAULT 'America/Lima',
  `cierre_dia_hora` tinyint(4) DEFAULT 0,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_clerk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `planes`
--

CREATE TABLE `planes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `precio_centavos` int(11) NOT NULL DEFAULT 0,
  `moneda` char(3) NOT NULL DEFAULT 'USD',
  `max_habitos` int(11) DEFAULT NULL,
  `permite_grupos` tinyint(1) NOT NULL DEFAULT 0,
  `descripcion` text DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos_inbox`
--

CREATE TABLE `pagos_inbox` (
  `id` char(36) NOT NULL,
  `remitente` varchar(191) NOT NULL,
  `monto_texto` varchar(50) NOT NULL,
  `codigo_seguridad` varchar(191) NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_inbox_idem` (`codigo_seguridad`,`fecha_hora`,`monto_texto`),
  KEY `idx_inbox_fecha` (`fecha_hora`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cupones`
--

CREATE TABLE `cupones` (
  `id` char(36) NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `tipo_descuento` enum('porcentaje','fijo') NOT NULL,
  `valor` int(11) NOT NULL,
  `max_usos` int(11) NOT NULL DEFAULT 1,
  `usos_actuales` int(11) NOT NULL DEFAULT 0,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_cupon_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `grupos`
--

CREATE TABLE `grupos` (
  `id` char(36) NOT NULL,
  `id_propietario` varchar(191) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_grupo_propietario` (`id_propietario`),
  CONSTRAINT `fk_grupo_propietario` FOREIGN KEY (`id_propietario`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `grupo_invitaciones`
--

CREATE TABLE `grupo_invitaciones` (
  `id` char(36) NOT NULL,
  `id_grupo` char(36) NOT NULL,
  `id_invitador` varchar(191) NOT NULL,
  `correo_invitado` varchar(191) NOT NULL,
  `token` char(64) NOT NULL,
  `estado` enum('pendiente','aceptada','expirada','revocada') NOT NULL DEFAULT 'pendiente',
  `expira_en` datetime DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_inv_invitador` (`id_invitador`),
  KEY `idx_inv_grupo_estado` (`id_grupo`,`estado`),
  CONSTRAINT `fk_inv_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_inv_invitador` FOREIGN KEY (`id_invitador`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `grupo_miembros`
--

CREATE TABLE `grupo_miembros` (
  `id_grupo` char(36) NOT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `rol` enum('propietario','administrador','miembro') NOT NULL DEFAULT 'miembro',
  `fecha_union` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_grupo`,`id_clerk`),
  KEY `fk_miembro_usuario` (`id_clerk`),
  CONSTRAINT `fk_miembro_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_miembro_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `habitos`
--

CREATE TABLE `habitos` (
  `id` char(36) NOT NULL,
  `id_propietario` varchar(191) NOT NULL,
  `id_grupo` char(36) DEFAULT NULL,
  `titulo` varchar(255) NOT NULL,
  `tipo` enum('hacer','dejar') NOT NULL,
  `frecuencia_diaria` int(11) NOT NULL DEFAULT 1,
  `archivado` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_habito_propietario` (`id_propietario`),
  KEY `idx_habito_grupo` (`id_grupo`),
  CONSTRAINT `fk_habito_grupo` FOREIGN KEY (`id_grupo`) REFERENCES `grupos` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_habito_propietario` FOREIGN KEY (`id_propietario`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `habito_rachas`
--

CREATE TABLE `habito_rachas` (
  `id_habito` char(36) NOT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `racha_actual` int(11) NOT NULL DEFAULT 0,
  `mejor_racha` int(11) NOT NULL DEFAULT 0,
  `ultima_fecha` date DEFAULT NULL,
  `ultima_revision_local` date DEFAULT NULL,
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_habito`,`id_clerk`),
  KEY `fk_racha_usuario` (`id_clerk`),
  CONSTRAINT `fk_racha_habito` FOREIGN KEY (`id_habito`) REFERENCES `habitos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_racha_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `habito_registros`
--

CREATE TABLE `habito_registros` (
  `id` char(36) NOT NULL,
  `id_habito` char(36) NOT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_hora_local` datetime NOT NULL,
  `estado` enum('exito','fallo') NOT NULL,
  `comentario` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_registro` (`id_habito`,`id_clerk`,`fecha`),
  KEY `idx_reg_fecha` (`fecha`),
  KEY `idx_reg_fecha_hora_local` (`fecha_hora_local`),
  KEY `idx_reg_usuario` (`id_clerk`),
  KEY `idx_reg_habito_fecha` (`id_habito`,`fecha`),
  CONSTRAINT `fk_reg_habito` FOREIGN KEY (`id_habito`) REFERENCES `habitos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reg_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notificaciones`
--

CREATE TABLE `notificaciones` (
  `id` char(36) NOT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `tipo` enum('recordatorio','logro','sistema') NOT NULL,
  `datos_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`datos_json`)),
  `programada_para` datetime DEFAULT NULL,
  `enviada_en` datetime DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_notif_usuario` (`id_clerk`),
  CONSTRAINT `fk_notif_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos_historial`
--

CREATE TABLE `pagos_historial` (
  `id` char(36) NOT NULL,
  `id_pago_inbox` char(36) DEFAULT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `id_plan` int(11) NOT NULL,
  `monto_centavos` int(11) NOT NULL,
  `moneda` char(3) NOT NULL,
  `estado` enum('confirmado','rechazado') NOT NULL DEFAULT 'confirmado',
  `descripcion` varchar(255) DEFAULT NULL,
  `fecha_aplicacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `id_cupon` char(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_hist_por_inbox` (`id_pago_inbox`),
  KEY `idx_hist_usuario` (`id_clerk`),
  KEY `idx_hist_plan` (`id_plan`),
  KEY `idx_hist_estado` (`estado`),
  KEY `fk_hist_cupon` (`id_cupon`),
  CONSTRAINT `fk_hist_cupon` FOREIGN KEY (`id_cupon`) REFERENCES `cupones` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_hist_inbox` FOREIGN KEY (`id_pago_inbox`) REFERENCES `pagos_inbox` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_plan` FOREIGN KEY (`id_plan`) REFERENCES `planes` (`id`),
  CONSTRAINT `fk_hist_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `suscripciones`
--

CREATE TABLE `suscripciones` (
  `id` char(36) NOT NULL,
  `id_clerk` varchar(191) NOT NULL,
  `id_plan` int(11) NOT NULL,
  `estado` enum('activa','cancelada','vencida') NOT NULL DEFAULT 'activa',
  `ciclo` enum('gratuito','mensual','anual') DEFAULT NULL,
  `es_actual` tinyint(1) NOT NULL DEFAULT 1,
  `periodo_inicio` datetime DEFAULT NULL,
  `periodo_fin` datetime DEFAULT NULL,
  `cancelar_en` datetime DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_sub_actual_por_usuario` (`id_clerk`,`es_actual`),
  KEY `fk_sub_plan` (`id_plan`),
  KEY `idx_sub_usuario` (`id_clerk`),
  KEY `idx_sub_estado` (`estado`),
  CONSTRAINT `fk_sub_plan` FOREIGN KEY (`id_plan`) REFERENCES `planes` (`id`),
  CONSTRAINT `fk_sub_usuario` FOREIGN KEY (`id_clerk`) REFERENCES `usuarios` (`id_clerk`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Disparadores `usuarios`
--
DELIMITER $$
CREATE TRIGGER `trg_usuarios_after_insert` AFTER INSERT ON `usuarios` FOR EACH ROW BEGIN
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
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_suscripcion_actual`
--
DROP TABLE IF EXISTS `vista_suscripcion_actual`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_suscripcion_actual`  AS SELECT `s`.`id` AS `id_suscripcion`, `s`.`id_clerk` AS `id_clerk`, `p`.`codigo` AS `plan_codigo`, `p`.`nombre` AS `plan_nombre`, `p`.`precio_centavos` AS `precio_centavos`, `p`.`moneda` AS `moneda`, `p`.`max_habitos` AS `max_habitos`, `p`.`permite_grupos` AS `permite_grupos`, `s`.`estado` AS `estado`, `s`.`ciclo` AS `ciclo`, `s`.`periodo_inicio` AS `periodo_inicio`, `s`.`periodo_fin` AS `periodo_fin`, `s`.`es_actual` AS `es_actual`, `s`.`fecha_creacion` AS `fecha_creacion`, `s`.`fecha_actualizacion` AS `fecha_actualizacion` FROM (`suscripciones` `s` join `planes` `p` on(`p`.`id` = `s`.`id_plan`)) WHERE `s`.`es_actual` = 1 ;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;