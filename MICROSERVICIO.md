# Guía de Extracción como Microservicio

## Estado Actual

✅ **El proyecto está listo para extraerse como microservicio independiente**

### Checklist de Preparación

- [x] **Sin dependencias del proyecto padre**: No hay imports de `ingestor-reader` o `radar_data`
- [x] **Estructura de paquete**: `pyproject.toml` configurado correctamente
- [x] **Clean Architecture**: Separación clara de capas (domain, application, infrastructure)
- [x] **Configuración externa**: Todas las configuraciones vía variables de entorno
- [x] **Paths relativos**: No hay paths absolutos hardcodeados
- [x] **CLI independiente**: Entry point configurado en `pyproject.toml`
- [x] **API Client**: `client.py` para integración externa
- [x] **Documentación**: README y documentación de uso

## Pasos para Extraer

### 1. Crear Nuevo Repositorio

```bash
# Crear nuevo repo
git init autodiscovery-service
cd autodiscovery-service

# Copiar todo el directorio autodiscovery
cp -r /path/to/ingestor-reader/autodiscovery/* .

# Hacer commit inicial
git add .
git commit -m "Initial commit: Autodiscovery microservice"
```

### 2. Configurar Git

```bash
# Agregar .gitignore (ya incluido)
# Configurar remoto
git remote add origin <repo-url>
git push -u origin main
```

### 3. Publicar en PyPI (Opcional)

```bash
# Instalar herramientas
pip install build twine

# Construir paquete
python -m build

# Publicar (requiere cuenta PyPI)
twine upload dist/*
```

### 4. Usar en Otro Proyecto

```bash
# Instalar desde git
pip install git+https://github.com/your-org/autodiscovery-service.git

# O desde PyPI
pip install autodiscovery
```

## Integración con Otros Proyectos

### Opción 1: Como Biblioteca

```python
from autodiscovery.client import AutodiscoveryClient

client = AutodiscoveryClient(registry_path="/path/to/registry.json")
url = client.get_latest_url("bcra_series")
```

### Opción 2: Como CLI

```bash
# En otro proyecto, usar el CLI
autodiscovery discover bcra_series
autodiscovery sync --all
```

### Opción 3: Como API REST (extensión futura)

```python
# Extender con FastAPI
from fastapi import FastAPI
from autodiscovery.application.usecases.discover_source_use_case import DiscoverSourceUseCase

app = FastAPI()

@app.post("/discover/{key}")
async def discover(key: str):
    # Inyectar dependencias
    use_case = DiscoverSourceUseCase(...)
    result = use_case.execute(key)
    return result
```

## Configuración de Producción

### Variables de Entorno Requeridas

```env
REGISTRY_PATH=/data/registry/sources_registry.json
MIRRORS_PATH=/data/mirrors
CONTRACTS_PATH=/app/contracts/sources.yml
```

### Docker Compose

```yaml
version: '3.8'

services:
  autodiscovery:
    build: .
    volumes:
      - ./registry:/data/registry
      - ./mirrors:/data/mirrors
      - ./contracts:/app/contracts
    environment:
      - REGISTRY_PATH=/data/registry/sources_registry.json
      - MIRRORS_PATH=/data/mirrors
      - CONTRACTS_PATH=/app/contracts/sources.yml
      - VERIFY_SSL=true
    command: autodiscovery sync --all
```

## Características del Microservicio

### ✅ Independiente

- No depende de otros proyectos
- Todas las dependencias están en `pyproject.toml`
- Configuración externa vía variables de entorno

### ✅ Portable

- Puede instalarse desde PyPI, Git, o localmente
- Funciona en cualquier entorno Python 3.11+
- No requiere paths específicos del sistema

### ✅ Extensible

- Clean Architecture permite agregar nuevas implementaciones
- Factory pattern permite registrar nuevos discoverers
- Interfaces permiten cambiar implementaciones sin modificar código

### ✅ Testeable

- Capas bien separadas facilitan testing
- Dependencias inyectadas permiten mocks
- Estructura de tests preparada

## Próximos Pasos (Opcional)

1. **Agregar API REST**: FastAPI wrapper para usar vía HTTP
2. **Agregar scheduler**: Cron jobs para descubrimiento automático
3. **Agregar webhooks**: Notificaciones cuando se descubren nuevos archivos
4. **Agregar métricas**: Prometheus metrics para observabilidad
5. **Agregar health checks**: Endpoint `/health` para Kubernetes

## Compatibilidad

- **Python**: 3.11+
- **Sistemas Operativos**: Linux, macOS, Windows
- **Deployment**: Docker, Kubernetes, bare metal

