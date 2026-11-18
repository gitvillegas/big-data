from pyspark.sql import SparkSession, functions as F

BUCKET = "s3://s3-bucket-big-data-af9fgqtgk03b3okqo03"

spark = SparkSession.builder.appName("analisis-distritos-2024").getOrCreate()

df = spark.read.parquet(f"{BUCKET}/refined/distritos_2024/").cache()
print("Distritos leidos:", df.count())


def ranking_indice(rank, ivt, media):
    """Pregunta 1 y 4: distritos de mayor a menor vulnerabilidad."""
    (df.select(F.col(rank).alias("puesto"), "distrito", ivt, media,
               F.round(F.col(ivt) - F.col(media), 2).alias("diferencia_vs_media"))
       .orderBy(F.desc(ivt))
       .show(21, truncate=False))


def detalle(rank_a, ivt_a, rank_b, ivt_b):
    """Detalle de comparacion entre dos esferas (3a y 5a)."""
    (df.select("distrito", rank_a, ivt_a, rank_b, ivt_b,
               F.abs(F.col(rank_a) - F.col(rank_b)).alias("diferencia_puestos"))
       .orderBy(rank_a)
       .show(21, truncate=False))


def resumen(x, y, rank_x, rank_y):
    """Pearson, Spearman (correlacion sobre rankings) y coincidencias en el top 5."""
    (df.agg(
        F.round(F.corr(x, y), 2).alias("pearson"),
        F.round(F.corr(rank_x, rank_y), 2).alias("spearman"),
        F.sum(F.when((F.col(rank_x) <= 5) & (F.col(rank_y) <= 5), 1)
               .otherwise(0)).alias("coinciden_top5"))
       .show())


print("=== PREGUNTA 1: vulnerabilidad en economia y empleo ===")
ranking_indice("rank_ee", "ivt_ee", "ivt_ee_media_ciudad")

print("=== PREGUNTA 2a: poblacion vs economia (detalle) ===")
(df.select("rank_poblacion", "distrito", "poblacion", "rank_ee", "ivt_ee")
   .orderBy(F.desc("poblacion"))
   .show(21, truncate=False))

print("=== PREGUNTA 2b: poblacion vs economia (resumen) ===")
resumen("poblacion", "ivt_ee", "rank_poblacion", "rank_ee")

print("=== PREGUNTA 3a: economia vs bienestar (detalle) ===")
detalle("rank_ee", "ivt_ee", "rank_bi", "ivt_bi")

print("=== PREGUNTA 3b: economia vs bienestar (resumen) ===")
resumen("ivt_ee", "ivt_bi", "rank_ee", "rank_bi")

print("=== PREGUNTA 4: vulnerabilidad en educacion y cultura ===")
ranking_indice("rank_ec", "ivt_ec", "ivt_ec_media_ciudad")

print("=== PREGUNTA 5a: educacion vs bienestar (detalle) ===")
detalle("rank_ec", "ivt_ec", "rank_bi", "ivt_bi")

print("=== PREGUNTA 5b: educacion vs bienestar (resumen) ===")
resumen("ivt_ec", "ivt_bi", "rank_ec", "rank_bi")

spark.stop()