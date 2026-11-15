import csv, os, pymysql

conn = pymysql.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASS"],
    database="indicevuln"
)

with open("iguala-EyE-distritos.csv", encoding="utf-8") as f:
    filas = csv.reader(f)
    next(filas)  # Salta el encabezado

    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO eye_distritos (
                cod_distrito,
                nombre_distrito,
                anio,
                ivt_ee,
                ivt_ee_media_ciudad,
                paro_larga_duracion,
                paro_larga_duracion_media_ciudad,
                poblacion_ingresos_bajos,
                poblacion_ingresos_bajos_media_ciudad
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            list(filas)
        )

conn.commit()
conn.close()

print("Bien")