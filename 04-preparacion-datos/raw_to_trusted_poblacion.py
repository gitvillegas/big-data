import sys
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

# leer el separador ; y todo como texto
df = (spark.read 
      .option("header", True)
      .option("sep",";")
      .option("encoding", "UTF-8")
      .csv(f"{BUCKET}/raw/url/poblacion.csv"))
    
# limpiar nombres de columnas (y espacios)
df = df.toDF(*[c.replace("\ufeff","").strip() for c in df.columns])

# transformar cada columnas
df_limpio = (df
    .withColumn("anio", F.regexp_extract("fecha", r"(\d{4})$", 1).cast("int"))
    .withColumn("cod_distrito", F.col("cod_distrito").cast("int"))
    .withColumn("distrito", F.trim("distrito"))
    .withColumn("cod_barrio", F.col("cod_barrio").cast("int"))
    .withColumn("barrio", F.trim("barrio"))
    .withColumn("num_personas", F.regexp_replace("num_personas", r"\.", "").cast("int"))
    .withColumn("num_hombres", F.regexp_replace("num_personas_hombres", r"\.", "").cast("int"))
    .withColumn("num_mujeres", F.regexp_replace("num_personas_mujeres", r"\.", "").cast("int"))
    .select("anio", "cod_distrito", "distrito", "cod_barrio", "barrio",
            "num_personas", "num_hombres", "num_mujeres"))
            
# quitar filas incompletas y duplicadas
df_limpio = (df_limpio
    .dropna(subset=["anio", "cod_distrito", "cod_barrio", "num_personas"])
    .dropDuplicates(["anio", "cod_barrio"]))
    
# verificar
df_limpio.printSchema()
df_limpio.show(5)
print("Filas leídas:", df.count(), "| Filas limpias:", df_limpio.count())
print("Filas donde hombres + mujeres != total:",
      df_limpio.filter("num_hombres + num_mujeres != num_personas").count())


# escribir en trusted como parquet
(df_limpio.write
    .mode("overwrite")
    .parquet(f"{BUCKET}/trusted/poblacion/"))
    
job.commit()
