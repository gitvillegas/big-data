Instrucciones para crear las tres fuentes de datos: archivos en una instancia EC2, una tabla en RDS MariaDB y una URL en Internet.

## Archivos de la carpeta del punto 2

- `datos/`: CSV usados en el proyecto.
- `sql/crear_tabla_eye_distritos.sql`: creación de la base de datos y la tabla.
- `cargar_datos.py`: carga del CSV de economía y empleo a RDS.
- `evidencias/EvidenciasPunto2.pdf`: capturas de cada paso.

## Requisitos previos

- Cuenta de AWS en la región us-east-1.
- Par de claves `.pem` para conectarse por SSH a la EC2.

## Fuente 1: archivos en una instancia EC2

Lanzamos una instancia EC2 con esta configuración:

- Ubuntu Server 24.04 LTS, tipo t3.micro, 8 GiB gp3
- IP pública habilitada
- Grupo de seguridad con SSH (puerto 22) desde la IP de quien se conecta
- Perfil de instancia de IAM: LabInstanceProfile

Creamos la carpeta de destino:

```bash
ssh -i <clave>.pem ubuntu@<ip-publica-ec2>
mkdir -p ~/datos/iguala
exit
```

Desde la carpeta `02-fuentes-datos/datos/` del equipo local enviamos los archivos:

```bash
scp -i <clave>.pem datos/iguala-BeI-distritos.csv datos/iguala-EyC-distritos.csv ubuntu@<ip-publica-ec2>:/home/ubuntu/datos/iguala/
```

Verificamos desde la EC2 (cada archivo debe tener 105 líneas):

```bash
cd ~/datos/iguala
wc -l *
```

## Fuente 2: datos en RDS MariaDB

Creamos la base de datos en RDS con esta configuración:

- Motor MariaDB 11.8.9, identificador `database-1`
- Usuario maestro `admin` con contraseña propia
- Misma VPC que la EC2, acceso público: No
- Grupo de seguridad con regla de entrada MYSQL/Aurora (puerto 3306) cuyo origen es el grupo de seguridad de la EC2

Instalamos las dependencias en la EC2 y descargamos el certificado de AWS, ya que la base de datos exige conexión cifrada:

```bash
cd ~
sudo apt update
sudo apt install -y mariadb-client python3-pymysql
curl -O https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
```

Enviamos el script SQL a la EC2 y creamos la base de datos y la tabla:

```bash
scp -i <clave>.pem sql/crear_tabla_eye_distritos.sql ubuntu@<ip-publica-ec2>:/home/ubuntu/
mysql -h <endpoint-rds> -u admin -p < crear_tabla_eye_distritos.sql
```

Verificamos la creación:

```sql
USE indicevuln;
SHOW TABLES;
```

Enviamos a la EC2 el CSV de economía y empleo y el script de carga:

```bash
scp -i <clave>.pem datos/iguala-EyE-distritos.csv cargar_datos.py ubuntu@<ip-publica-ec2>:/home/ubuntu/datos/iguala/
```

Ejecutamos el script con las credenciales como variables de entorno:

```bash
export DB_HOST="<endpoint-rds>"
export DB_USER="admin"
export DB_PASS="<contraseña>"
cd ~/datos/iguala
python3 cargar_datos.py
```

Verificamos la carga (deben ser 105 filas):

```sql
SELECT COUNT(*) FROM eye_distritos;
```

Eliminamos el CSV de la EC2:

```bash
rm ~/datos/iguala/iguala-EyE-distritos.csv
```

## Fuente 3: URL en Internet

La URL de descarga directa del dataset de población es:

```
https://datos.madrid.es/dataset/300557-0-poblacion-distrito-barrio/resource/300557-0-poblacion-distrito-barrio-csv/download/300557-0-poblacion-distrito-barrio-csv.csv
```

Desde la EC2 comprobamos que es accesible (el archivo descargado es solo temporal y se elimina):

```bash
curl -L -o /tmp/poblacion.csv "<url>"
head -1 /tmp/poblacion.csv
wc -l /tmp/poblacion.csv
rm /tmp/poblacion.csv
```

El encabezado debe empezar con `fecha;cod_municipio;municipio;cod_distrito;distrito;...` y el archivo debe tener 1180 líneas. La URL se configura en `03-ingesta/config.env.example` (variable `URL_POBLACION`).