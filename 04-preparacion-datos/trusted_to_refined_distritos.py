import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Arranque estandar de un job en Glue
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

BUCKET = "s3://sd-datalake-sherrerah3"
ANIO = 2024

# Poblacion: filtrar el año y sumar los barrios de cada distrito
poblacion = (spark.read.parquet(f"{BUCKET}/trusted/poblacion/")
    .filter(F.col("anio") == ANIO)
    .groupBy("cod_distrito")
    .agg(F.first("distrito").alias("distrito"),
         F.sum("num_personas").alias("poblacion"),
         F.count("cod_barrio").alias("num_barrios")))

# Indices: filtrar el año y quedarnos solo con el indice y su media
economia = (spark.read.parquet(f"{BUCKET}/trusted/economia_empleo/")
    .filter(F.col("anio") == ANIO)
    .select("cod_distrito", "ivt_ee", "ivt_ee_media_ciudad"))

bienestar = (spark.read.parquet(f"{BUCKET}/trusted/bienestar_igualdad/")
    .filter(F.col("anio") == ANIO)
    .select("cod_distrito", "ivt_bi", "ivt_bi_media_ciudad"))

educacion = (spark.read.parquet(f"{BUCKET}/trusted/educacion_cultura/")
    .filter(F.col("anio") == ANIO)
    .select("cod_distrito", "ivt_ec", "ivt_ec_media_ciudad"))

# Unir las cuatro tablas por codigo de distrito
df = (poblacion
      .join(economia, "cod_distrito", "inner")
      .join(bienestar, "cod_distrito", "inner")
      .join(educacion, "cod_distrito", "inner"))

# Rankings: 1 = mayor valor
def ranking(columna):
    return F.rank().over(Window.orderBy(F.desc(columna)))

df = (df
      .withColumn("anio", F.lit(ANIO))
      .withColumn("rank_poblacion", ranking("poblacion"))
      .withColumn("rank_ee", ranking("ivt_ee"))
      .withColumn("rank_bi", ranking("ivt_bi"))
      .withColumn("rank_ec", ranking("ivt_ec"))
      .select("anio", "cod_distrito", "distrito", "num_barrios",
              "poblacion", "rank_poblacion",
              "ivt_ee", "ivt_ee_media_ciudad", "rank_ee",
              "ivt_bi", "ivt_bi_media_ciudad", "rank_bi",
              "ivt_ec", "ivt_ec_media_ciudad", "rank_ec")
      .orderBy("cod_distrito"))

# Verificar
df.printSchema()
df.show(21, truncate=False)
print("Distritos en refined:", df.count())
print("Población total Madrid:", df.agg(F.sum("poblacion")).first()[0])

# Escribir en refined (un solo archivo)
df.coalesce(1).write.mode("overwrite").parquet(f"{BUCKET}/refined/distritos_2024/")

job.commit()
