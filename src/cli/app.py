"""CLI application using Typer."""

from typing import List, Optional

import typer
from dotenv import load_dotenv

from ..infrastructure.bs4_adapter import Bs4Adapter
from ..infrastructure.clock_adapter import ClockAdapter
from ..infrastructure.contracts_yaml_adapter import ContractsYamlAdapter
from ..infrastructure.httpx_adapter import HttpxAdapter
from ..infrastructure.logger_structlog_adapter import LoggerStructlogAdapter
from ..infrastructure.metrics_memory_adapter import MetricsMemoryAdapter
from ..infrastructure.mirror_fs_adapter import MirrorFsAdapter
from ..infrastructure.mirror_s3_adapter import MirrorS3Adapter
from ..infrastructure.registry_fs_adapter import RegistryFsAdapter
from ..interfaces.mirror_port import MirrorPort
from ..usecases.discover_source import DiscoverSourceUseCase
from ..usecases.show_registry import ShowRegistryUseCase
from ..usecases.sync_all import SyncAllUseCase

# Load environment variables
load_dotenv()

app = typer.Typer(help="Autodiscovery Sources CLI")


def _get_adapters() -> dict:
    """Get all adapters (dependency injection)."""
    logger = LoggerStructlogAdapter()
    http = HttpxAdapter()
    html = Bs4Adapter()
    contracts = ContractsYamlAdapter()
    registry = RegistryFsAdapter()
    mirror_fs = MirrorFsAdapter()
    mirror_s3 = MirrorS3Adapter()
    
    # Combine mirror adapters (try S3 first, fallback to FS)
    class CompositeMirror(MirrorPort):
        def __init__(self, s3, fs):
            self.s3 = s3
            self.fs = fs
        
        def write(self, key: str, version: str, filename: str, content: bytes) -> Optional[str]:
            s3_key = self.s3.write(key, version, filename, content)
            if s3_key:
                return s3_key
            return self.fs.write(key, version, filename, content)
    
    mirror = CompositeMirror(mirror_s3, mirror_fs)
    clock = ClockAdapter()
    metrics = MetricsMemoryAdapter()
    
    return {
        "logger": logger,
        "http": http,
        "html": html,
        "contracts": contracts,
        "registry": registry,
        "mirror": mirror,
        "clock": clock,
        "metrics": metrics,
    }


@app.command()
def discover(
    key: str = typer.Argument(..., help="Source key to discover"),
    fast: bool = typer.Option(False, "--fast", help="Fast mode (max_depth=1, max_candidates=1)"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
):
    """Discover a single source by key."""
    adapters = _get_adapters()
    logger = adapters["logger"]
    
    if verbose:
        logger = logger.bind(log_level="DEBUG")
    
    discover_uc = DiscoverSourceUseCase(
        contracts_port=adapters["contracts"],
        http_port=adapters["http"],
        html_port=adapters["html"],
        registry_port=adapters["registry"],
        mirror_port=adapters["mirror"],
        clock_port=adapters["clock"],
        metrics_port=adapters["metrics"],
        logger=logger,
    )
    
    try:
        entry = discover_uc.execute(key, fast=fast)
        if entry:
            typer.echo(f"✓ Discovered {key}: {entry.version} - {entry.url.value}")
            typer.echo(f"  Filename: {entry.filename}")
            typer.echo(f"  Status: {entry.status}")
            if entry.mime:
                typer.echo(f"  MIME: {entry.mime.value}")
            if entry.size_kb:
                typer.echo(f"  Size: {entry.size_kb.value:.2f} KB")
        else:
            typer.echo(f"✗ No entry discovered for {key}", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error discovering {key}: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def sync(
    all_sources: bool = typer.Option(False, "--all", help="Sync all sources"),
    only_keys: Optional[str] = typer.Option(None, "--only-keys", help="Comma-separated list of keys"),
    fast: bool = typer.Option(False, "--fast", help="Fast mode (max_depth=1, max_candidates=1)"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
):
    """Sync one or more sources."""
    adapters = _get_adapters()
    logger = adapters["logger"]
    
    if verbose:
        logger = logger.bind(log_level="DEBUG")
    
    discover_uc = DiscoverSourceUseCase(
        contracts_port=adapters["contracts"],
        http_port=adapters["http"],
        html_port=adapters["html"],
        registry_port=adapters["registry"],
        mirror_port=adapters["mirror"],
        clock_port=adapters["clock"],
        metrics_port=adapters["metrics"],
        logger=logger,
    )
    
    sync_uc = SyncAllUseCase(
        discover_use_case=discover_uc,
        contracts_port=adapters["contracts"],
        metrics_port=adapters["metrics"],
        logger=logger,
    )
    
    if not all_sources:
        typer.echo("Error: --all flag is required for sync command", err=True)
        raise typer.Exit(1)
    
    keys = None
    if only_keys:
        keys = [k.strip() for k in only_keys.split(",")]
    
    try:
        results = sync_uc.execute(only_keys=keys, fast=fast)
        typer.echo(f"Sync completed:")
        typer.echo(f"  Total: {results['total']}")
        typer.echo(f"  Success: {results['success']}")
        typer.echo(f"  Failed: {results['failed']}")
        
        if results["errors"]:
            typer.echo("\nErrors:")
            for error in results["errors"]:
                typer.echo(f"  - {error['key']}: {error['error']}")
        
        if results["failed"] > 0:
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error syncing: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show(
    key: Optional[str] = typer.Argument(None, help="Source key to show (optional)"),
):
    """Show registry entries."""
    adapters = _get_adapters()
    logger = adapters["logger"]
    
    show_uc = ShowRegistryUseCase(
        registry_port=adapters["registry"],
        clock_port=adapters["clock"],
        logger=logger,
    )
    
    try:
        entries = show_uc.execute(key=key)
        if not entries:
            typer.echo("No entries found")
            return
        
        for entry in entries:
            typer.echo(show_uc.format_entry(entry))
            typer.echo("")
    except Exception as e:
        typer.echo(f"✗ Error showing registry: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def list():
    """List all source keys from contracts."""
    adapters = _get_adapters()
    contracts = adapters["contracts"]
    
    try:
        all_contracts = contracts.load_all()
        typer.echo("Available source keys:")
        for contract in all_contracts:
            key = contract.get("key")
            if key:
                typer.echo(f"  - {key}")
    except Exception as e:
        typer.echo(f"✗ Error listing keys: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def validate(
    key: str = typer.Argument(..., help="Source key to validate"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
):
    """Re-validate a source by redoing HEAD/GET and updating status."""
    adapters = _get_adapters()
    logger = adapters["logger"]
    
    if verbose:
        logger = logger.bind(log_level="DEBUG")
    
    # Get latest entry
    registry = adapters["registry"]
    entry = registry.get_by_key(key)
    
    if not entry:
        typer.echo(f"✗ No entry found for key: {key}", err=True)
        raise typer.Exit(1)
    
    # Re-validate by doing HEAD/GET
    http = adapters["http"]
    logger.info("Re-validating", key=key, url=entry.url.value)
    
    headers, error = http.head(entry.url.value)
    if error:
        # Try GET
        content, headers, error_get = http.get(entry.url.value)
        if error_get:
            # Broken
            entry.status = "broken"
            entry.notes = f"Validation failed: {error_get}"
        else:
            # Suspect
            entry.status = "suspect"
            entry.notes = f"HEAD failed, GET OK: {error}"
    else:
        # OK
        entry.status = "ok"
        entry.notes = "Re-validated OK"
    
    # Update last_checked
    entry.last_checked = adapters["clock"].now()
    
    # Upsert
    registry.upsert(entry)
    
    typer.echo(f"✓ Validated {key}: {entry.status}")
    if entry.notes:
        typer.echo(f"  Notes: {entry.notes}")


if __name__ == "__main__":
    app()

