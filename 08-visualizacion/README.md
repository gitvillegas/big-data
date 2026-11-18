# Punto 8: Visualización de datos y aplicación Streamlit con API Gateway

Aplicación web en Streamlit que responde las cinco preguntas del caso de estudio con gráficas (matplotlib) y tablas. Los datos no se leen directamente del datalake: se obtienen a través de una API expuesta con **Amazon API Gateway**.

## Arquitectura

```
Streamlit (EC2, :8501)  →  API Gateway (GET /distritos)  →  Lambda  →  Athena  →  S3 (refined)
```

| Componente                   | Función                                                           |
| ---------------------------- | ----------------------------------------------------------------- |
| S3 `refined/distritos_2024/` | Tabla final con población, índices IGUALA y rankings por distrito |
| Athena                       | Consulta la tabla `proyecto2_db.distritos_2024`                   |
| Lambda `api-distritos`       | Ejecuta la consulta en Athena y devuelve el resultado en JSON     |
| API Gateway (HTTP API)       | Expone la Lambda en la ruta `GET /distritos`                      |
| Streamlit en EC2             | Consume la API, calcula las métricas y dibuja las gráficas        |

Streamlit llama a la API desde el servidor, no desde el navegador. Así se evita el problema de los WebSockets, que API Gateway no deja pasar si se usa como proxy directo hacia Streamlit.

## Archivos de la carpeta

- `app.py`: aplicación Streamlit.
- `evidencias/`: capturas de cada paso.

Las dependencias (`streamlit`, `matplotlib`, `pandas`, `requests`) están declaradas en el `pyproject.toml` de la raíz del repositorio y se gestionan con `uv`.

## Requisitos previos

- Puntos 4 y 5 terminados: base de datos `proyecto2_db` en el Glue Data Catalog con la tabla `distritos_2024`.
- Carpeta `athena-results/` en el bucket `s3-bucket-big-data-af9fgqtgk03b3okqo03`.
- Ubicación de resultados de Athena configurada con esa carpeta (punto 6).

## 1. Lambda `api-distritos`

En la consola de Lambda: **Create function**, **Author from scratch**.

- **Nombre:** `api-distritos`
- **Runtime:** Python 3.12
- **Rol de ejecución:** en _Change default execution role_ elegimos **Use an existing role** y seleccionamos **LabRole**. El Learner Lab no permite `iam:CreateRole`, así que Lambda no puede crear su propio rol y falla si se deja la opción por defecto.
- **Timeout:** 30 segundos (_Configuration_, _General configuration_).

Código de la función:

```python
import json
import time
import boto3

athena = boto3.client("athena")
OUTPUT = "s3://s3-bucket-big-data-af9fgqtgk03b3okqo03/athena-results/"
QUERY = "SELECT * FROM proyecto2_db.distritos_2024 ORDER BY cod_distrito"


def respuesta(codigo, cuerpo):
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(cuerpo),
    }


def lambda_handler(event, context):
    qid = athena.start_query_execution(
        QueryString=QUERY,
        ResultConfiguration={"OutputLocation": OUTPUT},
    )["QueryExecutionId"]

    while True:
        estado = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if estado["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(0.5)

    if estado["State"] != "SUCCEEDED":
        return respuesta(500, {"error": estado.get("StateChangeReason", estado["State"])})

    filas = athena.get_query_results(QueryExecutionId=qid)["ResultSet"]["Rows"]
    columnas = [c["VarCharValue"] for c in filas[0]["Data"]]
    datos = [
        dict(zip(columnas, [c.get("VarCharValue") for c in fila["Data"]]))
        for fila in filas[1:]
    ]
    return respuesta(200, datos)
```

Pulsamos **Deploy** y probamos con **Test** usando el evento `{}`. La respuesta debe ser `statusCode 200` con los 21 distritos.

![Función Lambda y prueba exitosa](evidencias/01_lambda_prueba.png)

## 2. API Gateway

1. En la consola de API Gateway creamos una **HTTP API** llamada `api-distritos`.
2. Añadimos una integración de tipo **Lambda** apuntando a `api-distritos`.
3. Definimos la ruta **GET** `/distritos`.
4. Dejamos el stage `$default` con auto-deploy.
5. La **Invoke URL** está en _Stages_, `$default`, y tiene la forma `https://XXXX.execute-api.us-east-1.amazonaws.com`.

![API Gateway con la ruta GET /distritos](evidencias/02_api_gateway_ruta.png)

Probamos la API:

```bash
curl https://XXXX.execute-api.us-east-1.amazonaws.com/distritos
```

![Respuesta JSON de la API](evidencias/03_curl_api.png)

## 3. Aplicación Streamlit

`app.py` consulta la API (variable de entorno `API_URL`), convierte la respuesta en un DataFrame y ofrece un selector lateral con las cinco preguntas:

| Pregunta                   | Visualización                                                                                         |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| 1. Economía y empleo       | Barras horizontales por distrito con la media de la ciudad, más tabla ordenada                        |
| 2. Población vs. economía  | Dispersión población contra índice, métricas Pearson, Spearman y coincidencias en el top 5, más tabla |
| 3. Economía vs. bienestar  | Dispersión entre índices, las mismas métricas y tabla                                                 |
| 4. Educación y cultura     | Barras horizontales con la media de la ciudad, más tabla                                              |
| 5. Educación vs. bienestar | Dispersión entre índices, las mismas métricas y tabla                                                 |

Las métricas son las mismas del punto 6: Pearson sobre los índices, Spearman como correlación sobre los rankings y `coinciden_top5` como el número de distritos que están a la vez en el top 5 de ambas variables.

## 4. Despliegue en EC2 (Ubuntu) con uv

### 4.1 Security group

En **EC2**, **Instances**, seleccionamos la instancia y abrimos la pestaña **Security**. Entramos al security group asociado a la instancia, **Inbound rules**, **Edit inbound rules**, **Add rule**:

- **Type:** Custom TCP
- **Port range:** `8501`
- **Source:** `0.0.0.0/0` (o _My IP_)

Guardamos con **Save rules**. Hay que editar el grupo que realmente está asignado a la instancia.

![Regla de entrada del puerto 8501](evidencias/04_security_group.png)

### 4.2 Conexión e instalación de uv

```bash
ssh -i tu-llave.pem ubuntu@IP-PUBLICA-EC2

sudo apt update && sudo apt install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version
```

### 4.3 Clonar el repositorio e instalar dependencias

```bash
git clone https://github.com/gitvillegas/big-data.git
cd big-data
uv sync --no-dev
```

`uv sync` descarga Python 3.14 automáticamente, porque `pyproject.toml` declara `requires-python = ">=3.14"`.

### 4.4 Configurar la URL de la API y verificarla

```bash
export API_URL="https://XXXX.execute-api.us-east-1.amazonaws.com/distritos"
curl $API_URL
```

### 4.5 Arrancar Streamlit

```bash
nohup uv run streamlit run 08-visualizacion/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true > streamlit.log 2>&1 &
```

La aplicación queda disponible en `http://IP-PUBLICA-EC2:8501`.

![Aplicación corriendo en el navegador](evidencias/05_app_pregunta1.png)

### 4.6 Comandos útiles

```bash
tail -f streamlit.log     # ver los logs
pgrep -af streamlit       # comprobar que está corriendo
pkill -f streamlit        # detenerla
```

### 4.7 Opcional: servicio systemd

Para que la app se reinicie sola si la instancia se reinicia:

```bash
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit big-data
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/big-data
Environment=API_URL=https://XXXX.execute-api.us-east-1.amazonaws.com/distritos
ExecStart=/home/ubuntu/.local/bin/uv run streamlit run 08-visualizacion/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now streamlit
sudo systemctl status streamlit
```

## 5. Prueba en local (opcional)

Desde la raíz del repositorio:

```bash
uv sync
API_URL="https://XXXX.execute-api.us-east-1.amazonaws.com/distritos" uv run streamlit run 08-visualizacion/app.py
```

En PowerShell:

```powershell
$env:API_URL="https://XXXX.execute-api.us-east-1.amazonaws.com/distritos"
uv run streamlit run 08-visualizacion/app.py
```

## Evidencias

- Función Lambda y prueba exitosa.
- API Gateway con la ruta `GET /distritos`.
- `curl` a la API devolviendo el JSON.
- Regla de entrada del puerto 8501 en el security group.
- La aplicación en el navegador, una captura por pregunta:
  - ![Pregunta 1](evidencias/05_app_pregunta1.png)
  - ![Pregunta 2](evidencias/06_app_pregunta2.png)
  - ![Pregunta 3](evidencias/07_app_pregunta3.png)
  - ![Pregunta 4](evidencias/08_app_pregunta4.png)
  - ![Pregunta 5](evidencias/09_app_pregunta5.png)

## Notas y problemas encontrados

- **`iam:CreateRole` no autorizado:** el Learner Lab no deja crear roles. Se resolvió usando el rol existente **LabRole** al crear la Lambda.
- **API Gateway y Streamlit:** la API Gateway expone los datos y Streamlit los consume. No se usa API Gateway como proxy de la página de Streamlit, porque esta depende de WebSockets.
- **IP pública de la EC2:** en el Learner Lab cambia cuando la instancia se detiene y se vuelve a iniciar. Hay que usar la IP nueva para abrir la app.
- **Rol de Lambda y Athena:** la Lambda necesita permisos sobre Athena, Glue y S3. LabRole los tiene.
