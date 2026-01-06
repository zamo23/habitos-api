DROP DATABASE IF EXISTS habitos;
CREATE DATABASE habitos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
USE habitos;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";
START TRANSACTION;

/* ======================================================
   USUARIOS
====================================================== */
CREATE TABLE usuarios (
  id_clerk VARCHAR(191) NOT NULL,
  correo VARCHAR(191),
  nombre_completo VARCHAR(191),
  url_imagen TEXT,
  idioma VARCHAR(10) DEFAULT 'es',
  zona_horaria VARCHAR(50) DEFAULT 'America/Lima',
  cierre_dia_hora TINYINT DEFAULT 0,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_clerk)
) ENGINE=InnoDB;

CREATE INDEX idx_usuario_idioma ON usuarios (idioma);
CREATE INDEX idx_usuario_zona ON usuarios (zona_horaria);

/* ======================================================
   PLANES
====================================================== */
CREATE TABLE planes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(50) NOT NULL UNIQUE,
  nombre VARCHAR(100) NOT NULL,
  precio_centavos INT NOT NULL DEFAULT 0,
  moneda CHAR(3) NOT NULL DEFAULT 'USD',
  max_habitos INT,
  permite_grupos TINYINT(1) DEFAULT 0,
  descripcion TEXT,
  activo TINYINT(1) DEFAULT 1,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO planes (codigo, nombre, permite_grupos, descripcion)
VALUES ('premium','Premium',1,'Plan premium con todas las funcionalidades');

/* ======================================================
   SUSCRIPCIONES
====================================================== */
CREATE TABLE suscripciones (
  id CHAR(36) PRIMARY KEY,
  id_clerk VARCHAR(191) NOT NULL,
  id_plan INT NOT NULL,
  estado ENUM('activa','cancelada','vencida') DEFAULT 'activa',
  ciclo ENUM('gratuito','mensual','anual'),
  es_actual TINYINT(1) DEFAULT 1,
  periodo_inicio DATETIME,
  periodo_fin DATETIME,
  cancelar_en DATETIME,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_sub_actual (id_clerk, es_actual),
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE,
  FOREIGN KEY (id_plan) REFERENCES planes(id)
) ENGINE=InnoDB;

/* ======================================================
   GRUPOS
====================================================== */
CREATE TABLE grupos (
  id CHAR(36) PRIMARY KEY,
  id_propietario VARCHAR(191) NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  descripcion TEXT,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_propietario) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE grupo_miembros (
  id_grupo CHAR(36),
  id_clerk VARCHAR(191),
  rol ENUM('propietario','administrador','miembro') DEFAULT 'miembro',
  fecha_union TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_grupo, id_clerk),
  FOREIGN KEY (id_grupo) REFERENCES grupos(id) ON DELETE CASCADE,
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE grupo_invitaciones (
  id CHAR(36) PRIMARY KEY,
  id_grupo CHAR(36) NOT NULL,
  id_invitador VARCHAR(191) NOT NULL,
  correo_invitado VARCHAR(191) NOT NULL,
  token CHAR(64) NOT NULL,
  rol ENUM('administrador','miembro') DEFAULT 'miembro',
  estado ENUM('pendiente','aceptada','expirada','revocada') DEFAULT 'pendiente',
  expira_en DATETIME,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_grupo) REFERENCES grupos(id) ON DELETE CASCADE,
  FOREIGN KEY (id_invitador) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

/* ======================================================
   HABITOS
====================================================== */
CREATE TABLE habitos (
  id CHAR(36) PRIMARY KEY,
  id_propietario VARCHAR(191) NOT NULL,
  id_grupo CHAR(36),
  titulo VARCHAR(255) NOT NULL,
  tipo ENUM('hacer','dejar') NOT NULL,
  frecuencia_diaria INT DEFAULT 1,
  archivado TINYINT(1) DEFAULT 0,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_propietario) REFERENCES usuarios(id_clerk) ON DELETE CASCADE,
  FOREIGN KEY (id_grupo) REFERENCES grupos(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_habitos_usuario_archivado
ON habitos (id_propietario, archivado);

/* ======================================================
   REGISTROS Y RACHAS
====================================================== */
CREATE TABLE habito_registros (
  id CHAR(36) PRIMARY KEY,
  id_habito CHAR(36),
  id_clerk VARCHAR(191),
  fecha DATE,
  fecha_hora_local DATETIME,
  estado ENUM('exito','fallo'),
  comentario TEXT,
  archivado TINYINT(1) DEFAULT 0,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_registro (id_habito, id_clerk, fecha),
  FOREIGN KEY (id_habito) REFERENCES habitos(id) ON DELETE CASCADE,
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_reg_usuario_archivado
ON habito_registros (id_clerk, archivado);

CREATE TABLE habito_rachas (
  id_habito CHAR(36),
  id_clerk VARCHAR(191),
  racha_actual INT DEFAULT 0,
  mejor_racha INT DEFAULT 0,
  ultima_fecha DATE,
  ultima_revision_local DATE,
  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_habito, id_clerk),
  FOREIGN KEY (id_habito) REFERENCES habitos(id) ON DELETE CASCADE,
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

/* ======================================================
   IA - ANALISIS Y CONSEJOS
====================================================== */
CREATE TABLE ia_analisis_diario (
  id CHAR(36) PRIMARY KEY,
  id_clerk VARCHAR(191),
  fecha_analisis DATE,
  datos_enviados LONGTEXT,
  respuesta_ia LONGTEXT,
  estado_procesamiento ENUM('pendiente','procesado','error') DEFAULT 'pendiente',
  error_mensaje TEXT,
  archivado TINYINT(1) DEFAULT 0,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_analisis (id_clerk, fecha_analisis),
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ia_consejos (
  id CHAR(36) PRIMARY KEY,
  id_analisis CHAR(36),
  id_clerk VARCHAR(191),
  tipo_consejo ENUM('motivacion','mejora_habito','nuevo_habito','ruptura_racha','felicitacion'),
  titulo VARCHAR(200),
  contenido LONGTEXT,
  leido TINYINT(1) DEFAULT 0,
  archivado TINYINT(1) DEFAULT 0,
  generado_en DATETIME,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_analisis) REFERENCES ia_analisis_diario(id) ON DELETE CASCADE,
  FOREIGN KEY (id_clerk) REFERENCES usuarios(id_clerk) ON DELETE CASCADE
) ENGINE=InnoDB;

/* ======================================================
   TRIGGER SUSCRIPCION AUTOMATICA
====================================================== */
DELIMITER $$

CREATE TRIGGER trg_usuario_creado
AFTER INSERT ON usuarios
FOR EACH ROW
BEGIN
  DECLARE v_plan INT;
  SELECT id INTO v_plan FROM planes WHERE codigo='premium' LIMIT 1;

  IF v_plan IS NOT NULL THEN
    INSERT INTO suscripciones
    (id, id_clerk, id_plan, ciclo, es_actual)
    VALUES (UUID(), NEW.id_clerk, v_plan, 'gratuito', 1);
  END IF;
END$$

DELIMITER ;

COMMIT;
