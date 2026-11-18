import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

# Arranque estandar de un job en Glue
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session 
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

BUCKET = "s3://sd-datalake-sherrerah3"

# leer el csv
df = (spark.read 
      .option("header", True)
      .option("inferSchema",True)
      .csv(f"{BUCKET}/raw/rds/eye_distritos.csv"))
    
# ver lo que se leyo 
df.printSchema()
df.show(5)
print("filas leidas:", df.count())

# escribir en trusted como parquet
(df.write
    .mode("overwrite")
    .parquet(f"{BUCKET}/trusted/economia_empleo/"))
    
job.commit()
