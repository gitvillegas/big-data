import sys, re, unicodedata
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# Arranque estandar de un job en Glue
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

BUCKET = "s3://sd-datalake-sherrerah3"

def normalizar(nombre):
    """'Índice de Vulnerabilidad - media' -> 'indice_de_vulnerabilidad_media'"""
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")

def limpiar_iguala(ruta, sigla):
    # leer (separador "," por defecto)
    df = (spark.read
          .option("header", "true")
          .option("encoding", "UTF-8")
          .csv(ruta))

    # nombres de columna sin tildes ni espacios
    df = df.toDF(*[normalizar(c) for c in df.columns])

    # nombres cortos para las columnas clave
    indice = [c for c in df.columns if c.startswith("indice_de_vulnerabilidad")]
    df = (df
          .withColumnRenamed("codigo_distrito", "cod_distrito")
          .withColumnRenamed("fecha_datos", "anio")
          .withColumnRenamed(indice[0], f"ivt_{sigla}")
          .withColumnRenamed(indice[1], f"ivt_{sigla}_media_ciudad"))
    df = df.toDF(*[c.replace("indicador_", "", 1) for c in df.columns])

    # tipos: enteros para claves, texto para el nombre, decimal para el resto
    for c in df.columns:
        if c in ("cod_distrito", "anio"):
            df = df.withColumn(c, F.col(c).cast("int"))
        elif c == "nombre_distrito":
            df = df.withColumn(c, F.trim(c))
        else:
            df = df.withColumn(c, F.col(c).cast("double"))

    # calidad: un registro por distrito y año
    return (df
            .dropna(subset=["cod_distrito", "anio", f"ivt_{sigla}"])
            .dropDuplicates(["cod_distrito", "anio"]))


datasets = [
    ("iguala-BeI-distritos.csv", "bi", "bienestar_igualdad"),
    ("iguala-EyC-distritos.csv", "ec", "educacion_cultura"),
]

for archivo, sigla, carpeta in datasets:
    df = limpiar_iguala(f"{BUCKET}/raw/archivos/{archivo}", sigla)
    print(f"=== {carpeta}: {df.count()} filas")
    df.printSchema()
    df.select("cod_distrito", "nombre_distrito", "anio",
              f"ivt_{sigla}", f"ivt_{sigla}_media_ciudad").show(3)
    df.write.mode("overwrite").parquet(f"{BUCKET}/trusted/{carpeta}/")

job.commit()
