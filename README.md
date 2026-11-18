# Proyecto 2 de Big Data: vulnerabilidad territorial en Madrid

SI3007 Sistemas Distribuidos / ST0263 Tópicos Especiales en Telemática, 2026-2, Universidad EAFIT.

**Integrantes:** Juan José Gómez Ramírez, Samuel Herrera Hoyos y Sebastián Villegas Calle.

## Caso de estudio

Analizamos los 21 distritos de Madrid en 2024 cruzando su población con el índice de vulnerabilidad IGUALA del Ayuntamiento, en tres esferas: economía y empleo, bienestar e igualdad, y educación y cultura. Un índice más alto indica mayor vulnerabilidad. Las 5 preguntas de negocio están en [`01-caso-estudio`](01-caso-estudio).

## Arquitectura

```
EC2 (CSV) ─┐
RDS        ├─> ingesta.py + cron ─> S3 raw/ ─> Glue (Spark) ─> trusted/ ─> Glue (Spark) ─> refined/
URL       ─┘                                                                              │
                                              Glue Crawler ─> Glue Data Catalog (proyecto2_db)
                                                                                           │
                                Athena · EMR (Hive, SparkSQL, PySpark) · Lambda + API Gateway + Streamlit
```

## Puntos

| Punto | Carpeta | Tecnologías |
|---|---|---|
| 1. Caso de estudio | [`01-caso-estudio`](01-caso-estudio) | Datos abiertos de Madrid |
| 2. Fuentes de datos | [`02-fuentes-datos`](02-fuentes-datos) | EC2, RDS MariaDB, URL |
| 3. Ingesta automática | [`03-ingesta`](03-ingesta) | Python, cron, S3 |
| 4. Preparación de datos | [`04-preparacion-datos`](04-preparacion-datos) | AWS Glue, PySpark, Parquet |
| 5. Catalogación | [`05-catalogacion`](05-catalogacion) | Glue Crawler, Glue Data Catalog, Hive |
| 6. Consultas SQL | [`06-consultas-sql`](06-consultas-sql) | Athena, Hive, SparkSQL |
| 7. Análisis con PySpark | [`07-analisis-pyspark`](07-analisis-pyspark) | PySpark en EMR |
| 8. Visualización y API | [`08-visualizacion`](08-visualizacion) | Lambda, API Gateway, Streamlit, matplotlib |

## Resultados principales

- Puente de Vallecas es el distrito más vulnerable en las tres esferas.
- La población tiene una relación débil con la vulnerabilidad económica (correlación 0,34).
- Economía y educación coinciden casi por completo (0,95), mientras que bienestar coincide solo en parte con ambas (0,55 y 0,48).

El detalle de cada respuesta está en [`06-consultas-sql/athena`](06-consultas-sql/athena).
