# Autodiscovery

**Autodiscovery** es una herramienta Python lista para producción que descubre, valida, versiona y registra URLs de fuentes de datos oficiales de Argentina (BCRA, INDEC, REM) con resiliencia y confiabilidad.

## ¿Cómo funciona?

### Arquitectura

El sistema funciona en tres capas principales:

1. **Discovery Layer**: Descubre URLs de fuentes de datos escaneando páginas web oficiales
2. **Validation Layer**: Valida los recursos descubiertos (MIME type, tamaño, integridad)
3. **Registry Layer**: Mantiene un registro versionado de todas las fuentes descubiertas

### Flujo de trabajo

```
┌─────────────────┐
│  Contracts YAML │  Define cómo descubrir cada fuente
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Discoverer    │  Escanea páginas web y encuentra URLs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validator     │  Verifica MIME type, tamaño, etc.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Mirror       │  Descarga y guarda localmente (FS/S3)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Registry      │  Guarda metadatos en JSON atómico
└─────────────────┘
```

### Componentes principales

#### 1. Contracts (`contracts/sources.yml`)

Los contratos definen **cómo** descubrir cada fuente de datos:

```yaml
- key: "bcra_series"
  start_urls:
    - "https://www.bcra.gob.ar/PublicacionesEstadisticas/..."
  match:
    kind: "fixed_filename"
    pattern: "series.xlsm"
  expect:
    mime: "application/vnd.ms-excel.sheet.macroEnabled.12"
    min_size_kb: 100
  mirror: true
  versioning: "date_today"
```

**Tipos de matching:**
- `fixed_filename`: Busca un nombre de archivo exacto
- `date_pattern`: Busca archivos con patrón de fecha (regex)
- `month_pattern`: Busca archivos con patrón de mes/año
- `fuzzy_text_and_ext`: Busca por texto y extensión de archivo

**Tipos de versioning:**
- `date_today`: Versión por fecha de descubrimiento (`v2025-11-04`)
- `date_from_filename`: Extrae fecha del nombre de archivo
- `year_month_from_filename`: Extrae año-mes del nombre

#### 2. Discoverers (`src/autodiscovery/sources/`)

Cada discoverer implementa la lógica específica para encontrar una fuente:

- **BCRASeriesDiscoverer**: Busca `series.xlsm` en páginas de BCRA
- **BCRAInfomodiaDiscoverer**: Busca archivos `infomodia-YYYY-MM-DD.xls`
- **BCRAREMDiscoverer**: Busca PDFs REM con meses en español
- **INDECEMAEDiscoverer**: Busca archivos EMAE por texto fuzzy

Todos heredan de `BaseDiscoverer` y deben implementar:
```python
def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]
```

#### 3. HTTP Client (`src/autodiscovery/http.py`)

Cliente HTTP con:
- **Retry logic**: Reintentos automáticos con backoff exponencial (tenacity)
- **Timeouts**: Configurables por variable de entorno
- **SSL verification**: Opcional (desactivar solo para pruebas)

#### 4. Registry (`src/autodiscovery/registry/`)

Sistema de registro atómico en JSON:

```json
{
  "entries": {
    "bcra_series": {
      "url": "https://www.bcra.gob.ar/.../series.xlsm",
      "version": "v2025-11-04",
      "mime": "application/vnd.ms-excel.sheet.macroEnabled.12",
      "size_kb": 7327.72,
      "sha256": "acdd62bd...",
      "last_checked": "2025-11-04T13:45:27Z",
      "status": "ok",
      "notes": "LELIQ TNA = s/o desde 2024-07-19",
      "stored_path": "mirrors/bcra_series/v2025-11-04/series.xlsm",
      "s3_key": null
    }
  }
}
```

**Escritura atómica**: Usa archivo temporal + rename para evitar corrupción.

#### 5. Mirrors (`src/autodiscovery/mirror/`)

Sistema de espejo dual:

- **Filesystem Mirror**: Guarda en `mirrors/<key>/<version>/<filename>`
- **S3 Mirror** (opcional): Sube a S3 si hay credenciales configuradas

Ambos calculan SHA256 durante la descarga para integridad.

#### 6. Validation Rules (`src/autodiscovery/rules/`)

- **validation.py**: Define MIME types esperados y tamaños mínimos por fuente
- **discontinuities.py**: Documenta discontinuidades conocidas (agregadas como `notes`)

## Instalación

```bash
# Instalar en modo desarrollo
cd autodiscovery
pip install -e .

# O con dependencias de desarrollo
pip install -e ".[dev]"
```

## Configuración

Copia `.env.example` a `.env` y configura:

```bash
# Registry
REGISTRY_PATH=registry/sources_registry.json
MIRRORS_PATH=mirrors

# HTTP
TIMEOUT_SECS=10
RETRIES=3
USER_AGENT=RadarAutodiscovery/1.0
VERIFY_SSL=true  # false solo para pruebas

# S3 (opcional)
MIRRORS_S3_BUCKET=
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Contracts
CONTRACTS_PATH=contracts/sources.yml
```

## Uso

### CLI Commands

#### Descubrir una fuente

```bash
# Con SSL desactivado (solo pruebas)
VERIFY_SSL=false autodiscovery discover bcra_series

# Con JSON output
VERIFY_SSL=false autodiscovery discover bcra_series --json
```

**Qué hace:**
1. Lee el contrato de `bcra_series` desde `contracts/sources.yml`
2. Obtiene las URLs de inicio
3. Ejecuta el discoverer correspondiente
4. Encuentra el archivo `series.xlsm`
5. Valida MIME type y tamaño
6. Descarga y guarda en mirror (si está habilitado)
7. Calcula SHA256
8. Guarda entrada en registry

#### Listar fuentes registradas

```bash
autodiscovery list-keys
autodiscovery list-keys --json
```

#### Mostrar detalles de una fuente

```bash
autodiscovery show bcra_series
autodiscovery show bcra_series --json
```

#### Validar una entrada existente

```bash
VERIFY_SSL=false autodiscovery validate bcra_series
```

**Qué hace:**
1. Lee la entrada del registry
2. Hace HEAD request a la URL
3. Verifica MIME type y tamaño actuales
4. Actualiza `last_checked` y `status`

#### Sincronizar todas las fuentes

```bash
# Sincronizar todas
VERIFY_SSL=false autodiscovery sync --all

# Sincronizar una específica
VERIFY_SSL=false autodiscovery sync --key bcra_infomodia
```

## Integración con `ingestor-reader`

### Usando el cliente Python

```python
from autodiscovery.client import AutodiscoveryClient

client = AutodiscoveryClient()

# Obtener URL más reciente
url = client.get_latest_url("bcra_series")
print(f"URL: {url}")

# Obtener ruta del mirror local
mirror_path = client.get_latest_mirror_path("bcra_series")
print(f"Mirror: {mirror_path}")

# Obtener entrada completa
entry = client.get_entry("bcra_series")
if entry:
    print(f"Version: {entry.version}")
    print(f"Status: {entry.status}")
    print(f"SHA256: {entry.sha256}")
```

### Funciones de conveniencia

```python
from autodiscovery.client import get_latest_url, get_latest_mirror_path

url = get_latest_url("bcra_series")
mirror_path = get_latest_mirror_path("bcra_series")
```

### Leyendo el registry directamente

```python
import json
from pathlib import Path

registry_path = Path("registry/sources_registry.json")
with open(registry_path) as f:
    registry = json.load(f)

entry = registry["entries"]["bcra_series"]
url = entry["url"]
version = entry["version"]
```

## Estructura del proyecto

```
autodiscovery/
├── contracts/
│   └── sources.yml          # Contratos de discovery
├── src/autodiscovery/
│   ├── cli.py                # CLI con Typer
│   ├── config.py             # Configuración desde env
│   ├── http.py               # Cliente HTTP con retries
│   ├── html.py               # Utilidades de parsing HTML
│   ├── hashutil.py           # SHA256 hashing
│   ├── client.py             # API de integración
│   ├── mirror/
│   │   ├── fs.py             # Mirror en filesystem
│   │   └── s3.py             # Mirror en S3 (opcional)
│   ├── registry/
│   │   ├── models.py         # Modelos Pydantic
│   │   └── registry.py       # Manager de registry
│   ├── rules/
│   │   ├── validation.py     # Reglas de validación
│   │   └── discontinuities.py # Discontinuidades conocidas
│   ├── sources/
│   │   ├── base.py           # Base discoverer
│   │   ├── bcra_series.py    # Discoverer BCRA series
│   │   ├── bcra_infomodia.py # Discoverer BCRA infomodia
│   │   ├── bcra_rem.py       # Discoverer BCRA REM
│   │   └── indec_emae.py     # Discoverer INDEC EMAE
│   └── util/
│       ├── date.py           # Utilidades de fecha/versión
│       └── fsx.py            # Utilidades de filesystem
├── tests/
│   └── test_autodiscovery.py # Tests
├── pyproject.toml            # Configuración del paquete
├── README.md                  # Este archivo
└── .env.example               # Ejemplo de configuración
```

## Flujo detallado de discovery

1. **Carga del contrato**: Lee `contracts/sources.yml` y encuentra el contrato para la clave
2. **Selección del discoverer**: Mapea la clave a la clase discoverer correspondiente
3. **Fetch de HTML**: Hace GET request a las URLs de inicio
4. **Parsing**: Usa BeautifulSoup para parsear HTML
5. **Búsqueda de links**: Encuentra links que coinciden con el patrón
6. **Selección**: Elige el archivo más reciente (si hay múltiples)
7. **Validación HEAD**: Hace HEAD request para obtener MIME type y tamaño
8. **Validación de reglas**: Verifica contra `rules/validation.py`
9. **Descarga (mirror)**: Si está habilitado, descarga el archivo
10. **Cálculo SHA256**: Calcula hash durante la descarga
11. **Generación de versión**: Genera versión según política del contrato
12. **Guardado en registry**: Escribe entrada en registry JSON (atómico)

## Versionado

El sistema versiona automáticamente según el tipo definido en el contrato:

- **`date_today`**: `v2025-11-04` (fecha de descubrimiento)
- **`date_from_filename`**: `v2025-11-04` (extraída del nombre)
- **`year_month_from_filename`**: `2025-11` (año-mes)

Los mirrors se guardan en `mirrors/<key>/<version>/<filename>`.

## Resiliencia

- **Retry logic**: Reintentos automáticos con backoff exponencial
- **Timeouts**: Configurables para evitar bloqueos
- **Atomic writes**: Escritura atómica del registry para evitar corrupción
- **Error handling**: Manejo de errores en cada capa
- **Status tracking**: Estado `ok`, `suspect`, o `broken` por entrada

## Observabilidad

- **Logging estructurado**: JSON logs en stdout
- **Métricas**: Contadores en memoria por run
- **JSON output**: Todos los comandos soportan `--json`

## Limitaciones

- **No parsea contenido**: No lee XLS/PDF, solo descubre URLs
- **No valida contenido**: Solo valida MIME type y tamaño
- **No detecta cambios**: Solo detecta cambios en URL, no en contenido

## Tests

```bash
pytest tests/
```

Los tests incluyen:
- Utilidades de fecha/versión
- Registry atómico read/write
- Matchers de discoverers
- Serialización/deserialización de modelos

## Ejemplos de uso

### Descubrir y registrar BCRA series

```bash
VERIFY_SSL=false autodiscovery discover bcra_series --json
```

### Sincronizar todas las fuentes

```bash
VERIFY_SSL=false autodiscovery sync --all --json
```

### Validar una entrada existente

```bash
VERIFY_SSL=false autodiscovery validate bcra_series
```

### Leer desde Python

```python
from autodiscovery.client import get_latest_url

# Obtener URL para ingestor-reader
url = get_latest_url("bcra_series")
# Usar url en ingestor-reader...
```

## Troubleshooting

### Error SSL

```bash
# Desactivar SSL temporalmente (solo pruebas)
VERIFY_SSL=false autodiscovery discover bcra_series
```

### Registry no encontrado

El sistema crea automáticamente el registry si no existe.

### Mirror falla

Verifica permisos de escritura en `MIRRORS_PATH` o configura S3.

### Discoverer no encuentra archivo

1. Verifica que la URL de inicio sea correcta
2. Verifica que el patrón de matching sea correcto
3. Revisa los logs para ver qué links se encontraron

## Contribuir

Para agregar un nuevo discoverer:

1. Crear clase en `src/autodiscovery/sources/<nombre>.py`
2. Heredar de `BaseDiscoverer`
3. Implementar método `discover()`
4. Agregar mapping en `cli.py` (`DISCOVERERS`)
5. Agregar contrato en `contracts/sources.yml`
6. Agregar reglas de validación en `rules/validation.py`

## Licencia

MIT
