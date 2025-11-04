# Instalación y Configuración

## Instalación como Paquete

### Desarrollo Local

```bash
# Clonar el repositorio
git clone <repo-url>
cd autodiscovery

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

### Instalación desde PyPI (cuando esté publicado)

```bash
pip install autodiscovery
```

### Instalación desde Git

```bash
pip install git+https://github.com/your-org/autodiscovery.git
```

## Configuración

### 1. Variables de Entorno

Copia el archivo `.env.example` a `.env` y configura las variables:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones:

```env
REGISTRY_PATH=registry/sources_registry.json
MIRRORS_PATH=mirrors
TIMEOUT_SECS=10
RETRIES=3
USER_AGENT=Autodiscovery/1.0
VERIFY_SSL=true

# S3 (opcional)
MIRRORS_S3_BUCKET=my-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

CONTRACTS_PATH=contracts/sources.yml
```

### 2. Contratos de Fuentes

Crea el archivo `contracts/sources.yml` con la configuración de tus fuentes:

```yaml
- key: "bcra_series"
  start_urls:
    - "https://www.bcra.gob.ar/PublicacionesEstadisticas/..."
  match:
    kind: "filename"
    pattern: "series.xlsm"
  expect:
    mime: "application/vnd.ms-excel.sheet.macroEnabled.12"
    min_size_kb: 100
  mirror: true
  versioning: "date"
```

## Uso

### CLI

```bash
# Descubrir una fuente
autodiscovery discover bcra_series

# Listar fuentes registradas
autodiscovery list-keys

# Ver detalles de una fuente
autodiscovery show bcra_series

# Validar una fuente
autodiscovery validate bcra_series

# Sincronizar todas las fuentes
autodiscovery sync --all

# Descubrir todos los archivos
autodiscovery discover-files --filter-ext .xls,.pdf,.xlsx
```

### API Python

```python
from autodiscovery.client import AutodiscoveryClient

client = AutodiscoveryClient()

# Obtener URL más reciente
url = client.get_latest_url("bcra_series")

# Obtener path del mirror local
path = client.get_latest_mirror_path("bcra_series")

# Obtener entrada completa
entry = client.get_entry("bcra_series")
```

## Despliegue como Microservicio

### Opción 1: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY contracts/ ./contracts/

RUN pip install --no-cache-dir -e .

ENV REGISTRY_PATH=/data/registry/sources_registry.json
ENV MIRRORS_PATH=/data/mirrors
ENV CONTRACTS_PATH=/app/contracts/sources.yml

VOLUME ["/data"]

CMD ["autodiscovery", "sync", "--all"]
```

### Opción 2: API REST (futuro)

El proyecto puede extenderse con una API REST usando FastAPI:

```python
from fastapi import FastAPI
from autodiscovery.client import AutodiscoveryClient

app = FastAPI()
client = AutodiscoveryClient()

@app.get("/sources/{key}")
def get_source(key: str):
    return client.get_entry(key)

@app.post("/sources/{key}/discover")
def discover_source(key: str):
    # Llamar al use case
    pass
```

## Estructura de Directorios

```
autodiscovery/
├── contracts/          # Configuración de fuentes (YAML)
├── registry/           # Registro de fuentes (JSON)
├── mirrors/            # Archivos descargados (FS)
├── src/
│   └── autodiscovery/ # Código fuente
├── tests/             # Tests
├── .env.example       # Ejemplo de configuración
├── pyproject.toml     # Configuración del paquete
└── README.md          # Documentación
```

## Notas

- Todos los paths pueden ser relativos (desde el directorio de trabajo) o absolutos
- El registro y los mirrors se crean automáticamente si no existen
- S3 es opcional; si no se configuran credenciales, solo se usa FS local
- Los contratos pueden estar en cualquier ubicación configurable
