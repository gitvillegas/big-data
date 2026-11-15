import csv, glob, os, sys, tempfile
import urllib.request
from datetime import datetime, timezone
import boto3
import pymysql

BASE = os.path.dirname(os.path.abspath(__file__))

def cargar_config(ruta):
    cfg = {}
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                cfg[clave.strip()] = valor.strip()
    return cfg

cfg = cargar_config(os.path.join(BASE, "config.env"))
BUCKET = cfg["S3_BUCKET"]
s3 = boto3.client("s3")

def log(msg):
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"{ahora} {msg}", flush=True)

def subir(ruta_local, fuente, nombre):
    key = f"raw/{fuente}/{nombre}"
    s3.upload_file(ruta_local, BUCKET, key)
    log(f"OK s3://{BUCKET}/{key}")

def ingesta_archivos():
    rutas = sorted(glob.glob(os.path.join(cfg["ARCHIVOS_DIR"], "*.csv")))
    if not rutas:
        raise RuntimeError(f"No hay CSV en {cfg['ARCHIVOS_DIR']}")
    for ruta in rutas:
        subir(ruta, "archivos", os.path.basename(ruta))

def ingesta_rds():
    tabla = "eye_distritos"
    conn = pymysql.connect(host=cfg["DB_HOST"], user=cfg["DB_USER"], password=cfg["DB_PASS"], database=cfg["DB_NAME"], connect_timeout=15, ssl_ca=os.path.join(BASE, "global-bundle.pem"), ssl_verify_cert=True)
    ruta = None
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {tabla}")
            filas = cur.fetchall()
            columnas = [d[0] for d in cur.description]
        with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", suffix=".csv", delete=False) as tmp:
            escritor = csv.writer(tmp)
            escritor.writerow(columnas)
            escritor.writerows(filas)
            ruta = tmp.name
        log(f"RDS: {len(filas)} filas leídas de {tabla}")
        subir(ruta, "rds", f"{tabla}.csv")
    finally:
        conn.close()
        if ruta and os.path.exists(ruta):
            os.remove(ruta)

def ingesta_url():
    peticion = urllib.request.Request(
        cfg["URL_POBLACION"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(peticion, timeout=60) as resp:
        datos = resp.read()
    if not datos.lstrip(b"\xef\xbb\xbf").startswith(b"fecha;"):
        raise RuntimeError("La descarga no parece el CSV de población")
    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as tmp:
        tmp.write(datos)
        ruta = tmp.name
    try:
        log(f"URL: {len(datos)} bytes descargados")
        subir(ruta, "url", "poblacion.csv")
    finally:
        os.remove(ruta)

def main():
    fallos = 0
    for nombre, funcion in [("archivos", ingesta_archivos), ("rds", ingesta_rds), ("url", ingesta_url)]:
        try:
            log(f"INICIO {nombre}")
            funcion()
        except Exception as e: 
            fallos += 1
            log(f"ERROR {nombre}: {e!r}")
    log("FIN con errores" if fallos else "FIN correcto")
    sys.exit(1 if fallos else 0)

if __name__ == "__main__":
    main()