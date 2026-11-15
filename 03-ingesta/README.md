Instrucciones para ejecutar la ingesta automática de las tres fuentes del punto 2 hacia la zona raw de S3.

## Archivos de la carpeta

- `ingesta.py`: script de ingesta.
- `config.env.example`: plantilla del archivo de configuración.
- `crontab.txt`: línea de cron para la ejecución diaria.
- `evidencias/EvidenciasPunto3.pdf`: capturas de cada paso.

## Requisitos previos

- Las tres fuentes del punto 2 creadas.
- La EC2 con el perfil de IAM LabInstanceProfile.

## Creación del bucket

Creamos el bucket de S3 con esta configuración:

- Tipo: uso general
- Nombre: `sd-datalake-<sufijo-propio>` (debe ser único en AWS, usar uno propio)
- Región: us-east-1
- ACL deshabilitadas
- Bloqueo de todo el acceso público activado
- Control de versiones deshabilitado
- Cifrado SSE-S3

## Preparación de la EC2

Instalamos las dependencias:

```bash
sudo apt update
sudo apt install -y python3-boto3 python3-pymysql
sudo snap install aws-cli --classic
```

Comprobamos el rol de la instancia (el ARN debe incluir `assumed-role/LabRole`):

```bash
aws sts get-caller-identity
```

Creamos la carpeta de trabajo y enviamos los archivos desde el equipo local:

```bash
ssh -i <clave>.pem ubuntu@<ip-publica-ec2> "mkdir -p ~/ingesta"
scp -i <clave>.pem ingesta.py config.env.example ubuntu@<ip-publica-ec2>:/home/ubuntu/ingesta/
```

Descargamos el certificado de AWS en la carpeta del script:

```bash
cd ~/ingesta
curl -O https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
```

## Configuración

Creamos `config.env` a partir de la plantilla y restringimos sus permisos:

```bash
cd ~/ingesta
cp config.env.example config.env
nano config.env
chmod 600 config.env
```

Variables a completar, sin comillas:

- `S3_BUCKET`: nombre del bucket
- `ARCHIVOS_DIR`: `/home/ubuntu/datos/iguala`
- `DB_HOST`: endpoint de RDS
- `DB_USER`: `admin`
- `DB_PASS`: contraseña de la base de datos
- `DB_NAME`: `indicevuln`
- `URL_POBLACION`: URL de descarga del CSV de población

`config.env` no se sube al repositorio.

## Ejecución manual

```bash
cd ~/ingesta
python3 ingesta.py
```

La salida debe mostrar una línea `OK s3://...` por archivo y terminar con `FIN correcto`.

## Verificación

Listamos la zona raw (deben aparecer cuatro objetos):

```bash
aws s3 ls s3://<bucket>/raw/ --recursive
```

Revisamos el encabezado de cada archivo:

```bash
aws s3 cp s3://<bucket>/raw/rds/eye_distritos.csv - | head -2
aws s3 cp s3://<bucket>/raw/url/poblacion.csv - | head -2
aws s3 cp s3://<bucket>/raw/archivos/iguala-BeI-distritos.csv - | head -2
aws s3 cp s3://<bucket>/raw/archivos/iguala-EyC-distritos.csv - | head -2
```

## Automatización con cron

Abrimos la tabla de tareas y pegamos al final la línea de `crontab.txt` (ejecución diaria a las 02:00 UTC):

```bash
crontab -e
```

Comprobamos que quedó registrada y la zona horaria de la máquina:

```bash
crontab -l
date
```

Revisamos el resultado de las ejecuciones:

```bash
tail -40 ~/ingesta/ingesta.log
aws s3 ls s3://<bucket>/raw/ --recursive
```