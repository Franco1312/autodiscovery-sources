# ¿Cómo busca los links de series?

Este documento explica paso a paso cómo el sistema busca y encuentra los links de `series.xlsm` en las páginas de BCRA.

## Proceso completo

### 1. Configuración inicial (contracts/sources.yml)

El contrato define dónde buscar:

```yaml
- key: "bcra_series"
  start_urls:
    - "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp"
    - "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
  match:
    kind: "fixed_filename"
    pattern: "series.xlsm"
```

### 2. Flujo de búsqueda en BCRASeriesDiscoverer

```python
# Paso 1: Para cada URL de inicio
for url in start_urls:
    # Paso 2: Descargar y parsear HTML
    soup = fetch_html(url, self.client)
    
    # Paso 3: Extraer todos los links de la página
    links = find_links(soup, url)
    
    # Paso 4: Buscar series.xlsm
    for link_url, link_text in links:
        filename = Path(link_url).name
        if filename.lower() == "series.xlsm":
            # ¡Encontrado!
```

## Función `fetch_html()` - Descarga y parsing

```python
def fetch_html(url: str, client: HTTPClient) -> BeautifulSoup:
    """Descarga HTML y lo parsea con BeautifulSoup."""
    response = client.get(url)  # GET request
    soup = BeautifulSoup(response.content, "lxml")  # Parse con lxml
    return soup
```

**Qué hace:**
1. Hace un `GET` request a la URL (ej: `https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp`)
2. Obtiene el contenido HTML
3. Parsea el HTML con BeautifulSoup usando el parser `lxml`
4. Retorna un objeto `BeautifulSoup` que permite navegar el DOM

**Ejemplo de HTML que recibe:**
```html
<html>
<body>
    <a href="/Pdfs/PublicacionesEstadisticas/series.xlsm">Series</a>
    <a href="/Pdfs/PublicacionesEstadisticas/otro.xls">Otro archivo</a>
    <a href="https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm">Series completo</a>
</body>
</html>
```

## Función `find_links()` - Extracción de links

```python
def find_links(
    soup: BeautifulSoup,
    base_url: str,
    pattern: Optional[str] = None,
    text_contains: Optional[List[str]] = None,
    ext: Optional[List[str]] = None,
) -> List[tuple[str, str]]:
    """Extrae todos los links de la página."""
    links = []
    for anchor in soup.find_all("a", href=True):  # Busca todos los <a> con href
        href = anchor.get("href", "")  # Obtiene el href
        text = anchor.get_text(strip=True)  # Obtiene el texto del link
        
        # Convierte URL relativa a absoluta
        absolute_url = urljoin(base_url, href)
        
        # Filtros opcionales (no se usan en bcra_series)
        # ...
        
        links.append((absolute_url, text))
    
    return links
```

**Qué hace:**
1. Busca todos los elementos `<a>` que tengan atributo `href` en el HTML
2. Para cada link:
   - Extrae el `href` (puede ser relativo o absoluto)
   - Extrae el texto del link
   - Convierte URLs relativas a absolutas usando `urljoin()`
   - Retorna una tupla `(url_absoluta, texto_del_link)`

**Ejemplo de transformación:**

```python
# HTML:
<a href="/Pdfs/PublicacionesEstadisticas/series.xlsm">Series</a>

# base_url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp"

# Resultado:
# absolute_url = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm"
# text = "Series"
# links.append(("https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm", "Series"))
```

## Búsqueda específica de series.xlsm

En `BCRASeriesDiscoverer.discover()`:

```python
target_filename = "series.xlsm"

# Extrae todos los links
links = find_links(soup, url)
# Ejemplo: [
#   ("https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm", "Series"),
#   ("https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/otro.xls", "Otro"),
#   ...
# ]

# Paso 1: Buscar links preferidos (Pdfs/PublicacionesEstadisticas)
for link_url, link_text in links:
    parsed = urlparse(link_url)  # Parse la URL
    filename = Path(parsed.path).name  # Extrae solo el nombre del archivo
    
    # Ejemplo: "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm"
    # parsed.path = "/Pdfs/PublicacionesEstadisticas/series.xlsm"
    # filename = "series.xlsm"
    
    if filename.lower() == target_filename.lower():  # "series.xlsm" == "series.xlsm"
        # Prefiere links con esta ruta específica
        if "Pdfs/PublicacionesEstadisticas" in link_url:
            discovered = self._validate_and_create(link_url)
            if discovered:
                return discovered  # ¡Encontrado y validado!

# Paso 2: Si no encontró el preferido, buscar cualquier series.xlsm
for link_url, link_text in links:
    parsed = urlparse(link_url)
    filename = Path(parsed.path).name
    
    if filename.lower() == target_filename.lower():
        discovered = self._validate_and_create(link_url)
        if discovered:
            return discovered  # ¡Encontrado!
```

## Validación del link encontrado

Una vez encontrado el link, se valida haciendo un `HEAD` request:

```python
def _validate_and_create(self, url: str) -> Optional[DiscoveredFile]:
    """Valida el link haciendo HEAD request."""
    response = self.client.head(url)  # HEAD request (solo headers, no descarga)
    
    # Extrae metadatos
    mime = response.headers.get("content-type", "").split(";")[0].strip()
    # Ejemplo: "application/vnd.ms-excel.sheet.macroEnabled.12"
    
    size_bytes = int(response.headers.get("content-length", 0))
    size_kb = size_bytes / 1024.0
    # Ejemplo: 7327.72 KB
    
    version = version_from_date_today()  # "v2025-11-04"
    
    return DiscoveredFile(
        url=url,
        version=version,
        filename="series.xlsm",
        mime=mime,
        size_kb=size_kb,
    )
```

**Qué hace el HEAD request:**
- No descarga el archivo completo
- Solo obtiene los headers HTTP
- Permite verificar que el archivo existe y obtener su tamaño y MIME type
- Es mucho más rápido que descargar el archivo completo

## Ejemplo completo paso a paso

### Entrada:
```yaml
start_urls:
  - "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp"
```

### Paso 1: GET request
```python
GET https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp
→ HTML response (200 OK)
```

### Paso 2: Parse HTML
```python
soup = BeautifulSoup(html_content, "lxml")
→ BeautifulSoup object con DOM parseado
```

### Paso 3: Extraer links
```python
find_links(soup, base_url)
→ [
    ("https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm", "Series"),
    ("https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/otro.xls", "Otro"),
    ...
  ]
```

### Paso 4: Buscar series.xlsm
```python
for link_url, link_text in links:
    filename = Path(link_url).name
    # filename = "series.xlsm"  ← ¡Coincide!
    
    if filename.lower() == "series.xlsm":
        if "Pdfs/PublicacionesEstadisticas" in link_url:
            # ¡Encontrado el preferido!
            discovered = self._validate_and_create(link_url)
```

### Paso 5: Validar con HEAD
```python
HEAD https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm
→ Headers:
   Content-Type: application/vnd.ms-excel.sheet.macroEnabled.12
   Content-Length: 7500000
```

### Paso 6: Crear DiscoveredFile
```python
DiscoveredFile(
    url="https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/series.xlsm",
    version="v2025-11-04",
    filename="series.xlsm",
    mime="application/vnd.ms-excel.sheet.macroEnabled.12",
    size_kb=7327.72,
)
```

## Ventajas de este enfoque

1. **No depende de estructura HTML específica**: Busca cualquier link con el nombre de archivo
2. **Resuelve URLs relativas**: Convierte automáticamente `/Pdfs/...` a URL absoluta
3. **Prioriza rutas conocidas**: Prefiere links de `Pdfs/PublicacionesEstadisticas`
4. **Validación rápida**: Usa HEAD request en lugar de descargar
5. **Resiliente**: Si una URL falla, prueba la siguiente

## Diferencias con otros discoverers

### BCRA Infomodia (patrón de fecha)
```python
# Busca por regex: infomodia-YYYY-MM-DD.xls
pattern = r"infomodia-(\d{4}-\d{2}-\d{2})\.xls"
match = re.search(pattern, filename)
if match:
    date_str = match.group(1)  # "2025-11-04"
    # Selecciona el más reciente
```

### BCRA REM (mes en español)
```python
# Busca: relevamiento-expectativas-mercado-<mes>-<año>.pdf
pattern = r"relevamiento-expectativas-mercado-(\w+)-(\d{4})\.pdf"
match = re.search(pattern, filename)
if match:
    month_str, year_str = match.groups()  # ("noviembre", "2025")
    # Normaliza mes español a número
```

### INDEC EMAE (fuzzy text)
```python
# Busca por texto del link y extensión
keywords = ["EMAE", "Estimador mensual de actividad económica"]
extensions = [".xlsx", ".xls", ".csv", ".pdf"]

# Filtra links que contengan keywords Y tengan extensión válida
if keyword in link_text and ext in link_url:
    # Prioriza .xlsx sobre .pdf
```

## Resumen

El proceso de búsqueda de `series.xlsm`:

1. **Descarga HTML** de las URLs de inicio
2. **Parsea HTML** con BeautifulSoup
3. **Extrae todos los links** `<a href="...">`
4. **Convierte URLs relativas** a absolutas
5. **Filtra por nombre de archivo** (`series.xlsm`)
6. **Prioriza rutas conocidas** (`Pdfs/PublicacionesEstadisticas`)
7. **Valida con HEAD request** (MIME type, tamaño)
8. **Retorna DiscoveredFile** con metadatos

Este enfoque es robusto porque no depende de la estructura exacta del HTML, solo busca cualquier link que apunte a un archivo con el nombre correcto.

