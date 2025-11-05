# autodiscovery-sources

Config-first public sources discovery and versioning engine. Discovers and versions public sources (XLS/XLSX/XLSM/PDF/API) from YAML contracts using a generic engine (no site-specific logic).

## Features

- **Config-first**: All discovery rules defined in YAML contracts
- **Generic engine**: No hardcoded logic per site
- **Clean Architecture**: Separation of concerns with domain, use cases, interfaces, and infrastructure
- **Resilient**: Retries, fallbacks (HEAD→GET), and atomic registry writes
- **Versioning**: Multiple strategies for extracting versions from filenames and headers
- **Mirroring**: Filesystem and S3 (optional) mirroring with atomic operations
- **Registry**: JSON-based registry with atomic writes for tracking discovered sources

## Installation

```bash
# Create virtual environment
make venv
source venv/bin/activate

# Install package
make install
```

Or manually:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` (optional, no critical values required):

```bash
cp .env.example .env
```

Edit `.env` if you want to configure:
- S3 credentials (optional, for S3 mirroring)
- Logging level
- HTTP timeouts

## Usage

### List available sources

```bash
ads list
```

### Discover a single source

```bash
ads discover --key bcra_series
```

### Discover with fast mode (reduced depth and candidates)

```bash
ads discover --key bcra_series --fast
```

### Sync all sources

```bash
ads sync --all
```

### Sync specific sources

```bash
ads sync --all --only-keys bcra_series,bcra_infomodia_xls
```

### Sync with fast mode

```bash
ads sync --all --fast
```

### Show registry entries

```bash
# Show all entries
ads show

# Show specific key
ads show bcra_series
```

### Validate a source

Re-validate a source by redoing HEAD/GET and updating status:

```bash
ads validate --key bcra_series
```

## Project Structure

```
autodiscovery-sources/
├── contracts/
│   └── sources.yml          # Source contracts (YAML)
├── mirrors/                 # Mirrored files (key/version/filename)
├── registry/
│   └── registry.json        # Registry state (atomic writes)
├── src/
│   ├── domain/             # Domain entities, value objects, policies
│   ├── usecases/           # Use cases (discover, sync, show)
│   ├── interfaces/         # Ports (contracts, HTTP, HTML, registry, mirror, etc.)
│   ├── infrastructure/     # Adapters (YAML, httpx, bs4, FS, S3, etc.)
│   ├── engine/             # Generic engine (crawler, ranker, validator, selector, versioning)
│   └── cli/                # CLI commands (Typer)
└── tests/                  # Test suite
```

## Contracts (sources.yml)

Each source is defined with:

- **key**: Unique identifier
- **start_urls**: Starting URLs for crawling
- **scope**: Domain/path restrictions, max depth, max candidates
- **find**: Prefilter criteria (link text, URL tokens)
- **match**: Regex patterns for matching files
- **select**: Selection preferences (extension, newest by method)
- **expect**: Validation criteria (MIME types, minimum size)
- **versioning**: Version extraction strategy
- **mirror**: Whether to mirror the file

### Example Contract

```yaml
- key: "bcra_series"
  start_urls:
    - "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_monetario_diario.asp"
  scope:
    allow_domains: ["bcra.gob.ar"]
    allow_paths_any: ["/PublicacionesEstadisticas"]
    max_depth: 1
    max_candidates: 2
  find:
    link_text_any: ["series", "xlsm"]
    url_tokens_any: ["series", "PublicacionesEstadisticas"]
  match:
    kind: "regex_any"
    patterns:
      - "(?i)series(.*)\\.xlsm$"
  select:
    prefer_ext: [".xlsm", ".xlsx", ".xls"]
    prefer_newest_by: "last_modified"
  expect:
    mime_any: ["application/vnd.ms-excel.sheet.macroEnabled.12"]
    min_size_kb: 100
  versioning: "date_today"
  mirror: true
```

### API Sources

For API sources, use `source_type: "api"`:

```yaml
- key: "indec_emae_api"
  source_type: "api"
  endpoint: "https://apis.datos.gob.ar/series/api/series?ids=173.1_EMAE_2016_M_19"
  headers:
    Accept-Language: "es-AR"
  versioning: "none"
  mirror: false
```

## Versioning Strategies

- **date_today**: Use today's date (for fixed-name files)
- **date_from_filename_or_last_modified**: Try filename regex, fallback to Last-Modified
- **best_effort_date_or_last_modified**: Multiple strategies with fallbacks
- **none**: No versioning (for APIs)

## Output Locations

- **Mirrors**: `mirrors/<key>/<version>/<filename>`
- **Registry**: `registry/registry.json` (atomic writes)

## SLO (Service Level Objectives)

- **Freshness BCRA**: < 36h
- **REM detection**: Within 72h of publication

## Runbooks

### "No candidates found"

- Check `find.link_text_any` and `find.url_tokens_any` - adjust if too restrictive
- Verify `start_urls` are accessible
- Check `scope.allow_domains` and `scope.allow_paths_any`

### "MIME mismatch"

- Relax `expect.mime_any` or accept by filename extension
- Check if server returns incorrect Content-Type

### "Filename without date"

- Use `versioning: "last_modified"` or `"best_effort_date_or_last_modified"`
- Adjust regex patterns in `match.patterns`

### "HEAD failed, GET OK"

- This is expected for some servers - the validator handles this automatically
- Entry will have `notes: "head_failed_get_ok"`

## Testing

```bash
make test
```

Or manually:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Development

### Code Quality

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/
```

### Makefile Targets

- `make venv`: Create virtual environment
- `make install`: Install package and dependencies
- `make test`: Run tests
- `make run-sync`: Run sync all sources (fast mode)
- `make clean`: Clean build artifacts

## Architecture

### Clean Architecture Layers

1. **Domain**: Entities, value objects, policies, errors
2. **Use Cases**: Business logic orchestration
3. **Interfaces (Ports)**: Abstract interfaces for adapters
4. **Infrastructure (Adapters)**: Concrete implementations (YAML, httpx, bs4, FS, S3)
5. **Engine**: Generic discovery logic (crawler, ranker, validator, selector, versioning)
6. **CLI**: Typer commands for user interaction

### Dependency Injection

All adapters are injected via ports, allowing easy testing and swapping implementations.

## Future Extensions

- **Selenium/Playwright**: Interface prepared but not implemented (for JS-heavy sites)
- **More versioning strategies**: Additional date extraction patterns
- **Metrics dashboard**: Expose metrics via HTTP API
- **Scheduled sync**: Cron-like scheduling for automatic discovery

## License

MIT

