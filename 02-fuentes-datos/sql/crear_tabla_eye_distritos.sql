CREATE DATABASE IF NOT EXISTS indicevuln;
USE indicevuln;

CREATE TABLE IF NOT EXISTS eye_distritos (
  cod_distrito TINYINT NOT NULL,
  nombre_distrito VARCHAR(50) NOT NULL,
  anio SMALLINT NOT NULL,
  ivt_ee DECIMAL(4,2),
  ivt_ee_media_ciudad DECIMAL(4,2),
  paro_larga_duracion DECIMAL(4,2),
  paro_larga_duracion_media_ciudad DECIMAL(4,2),
  poblacion_ingresos_bajos DECIMAL(4,2),
  poblacion_ingresos_bajos_media_ciudad DECIMAL(4,2),
  PRIMARY KEY (cod_distrito, anio)
);