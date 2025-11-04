"""CLI interface using Typer.

This module contains only CLI commands that delegate to use cases.
No business logic should be here - only orchestration and presentation.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table as RichTable

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.application.usecases.discover_all_links_use_case import (
    DiscoverAllLinksUseCase,
)
from autodiscovery.application.usecases.discover_source_use_case import (
    DiscoverSourceUseCase,
)
from autodiscovery.application.usecases.validate_source_use_case import (
    ValidateSourceUseCase,
)
from autodiscovery.domain.interfaces import IContractRepository, IRegistryRepository
from autodiscovery.http import HTTPClient
from autodiscovery.infrastructure.contract_repository import ContractRepository
from autodiscovery.infrastructure.file_validator import FileValidator
from autodiscovery.infrastructure.html_parser import HTMLParser
from autodiscovery.infrastructure.mirror_service import MirrorService
from autodiscovery.infrastructure.registry_repository import RegistryRepository
from autodiscovery.infrastructure.validation_rules import ValidationRules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Autodiscovery: Data source URL discovery and registration")
console = Console()


# Services (dependency injection)
contract_repository: IContractRepository = ContractRepository()
contract_service = ContractService(contract_repository)
registry_repository: IRegistryRepository = RegistryRepository()


@app.command()
def discover(
    key: str = typer.Argument(..., help="Source key to discover"),
    mirror: bool = typer.Option(True, help="Download mirror copy"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Discover and register a source."""
    with HTTPClient() as client:
        # Initialize services
        file_validator = FileValidator(client)
        mirror_service = MirrorService(client)
        validation_rules = ValidationRules()

        # Create use case
        use_case = DiscoverSourceUseCase(
            contract_service=contract_service,
            registry_repository=registry_repository,
            mirror_service=mirror_service,
            file_validator=file_validator,
            http_client=client,
            validation_rules=validation_rules,
        )

        # Execute use case
        result = use_case.execute(key, mirror=mirror)

        if not result.success:
            console.print(f"[red]{result.error}[/red]")
            sys.exit(1)

        # Format output
        output = {
            "key": result.key,
            "url": result.discovered.url,
            "version": result.discovered.version,
            "mime": result.discovered.mime,
            "size_kb": result.discovered.size_kb,
            "sha256": result.entry.sha256,
            "stored_path": result.entry.stored_path,
            "s3_key": result.entry.s3_key,
            "status": result.entry.status,
        }

        if output_json:
            console.print(json.dumps(output, indent=2))
        else:
            console.print(f"[green]Discovered: {result.key}[/green]")
            console.print(f"  URL: {result.discovered.url}")
            console.print(f"  Version: {result.discovered.version}")
            console.print(f"  MIME: {result.discovered.mime}")
            console.print(f"  Size: {result.discovered.size_kb:.2f} KB")
            if result.entry.sha256:
                console.print(f"  SHA256: {result.entry.sha256}")
            if result.entry.stored_path:
                console.print(f"  Stored: {result.entry.stored_path}")
            if result.entry.s3_key:
                console.print(f"  S3: {result.entry.s3_key}")


@app.command()
def list_keys(
    output_json: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """List all registered source keys."""
    keys = registry_repository.list_keys()

    if output_json:
        result = []
        for key in keys:
            entry = registry_repository.get_entry(key)
            if entry:
                result.append({
                    "key": key,
                    "version": entry.version,
                    "last_checked": entry.last_checked,
                    "status": entry.status,
                })
        console.print(json.dumps(result, indent=2))
    else:
        table = RichTable(title="Registered Sources")
        table.add_column("Key", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Last Checked", style="yellow")
        table.add_column("Status", style="magenta")

        for key in keys:
            entry = registry_repository.get_entry(key)
            if entry:
                table.add_row(
                    key,
                    entry.version,
                    entry.last_checked,
                    entry.status,
                )

        console.print(table)


@app.command()
def show(
    key: str = typer.Argument(..., help="Source key to show"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Show entry for a source key."""
    entry = registry_repository.get_entry(key)

    if not entry:
        console.print(f"[red]Entry not found for key: {key}[/red]")
        sys.exit(1)

    if output_json:
        console.print(json.dumps(entry.model_dump(), indent=2))
    else:
        console.print(f"[green]Entry for {key}:[/green]")
        console.print(f"  URL: {entry.url}")
        console.print(f"  Version: {entry.version}")
        console.print(f"  MIME: {entry.mime}")
        console.print(f"  Size: {entry.size_kb:.2f} KB")
        console.print(f"  SHA256: {entry.sha256}")
        console.print(f"  Last Checked: {entry.last_checked}")
        console.print(f"  Status: {entry.status}")
        if entry.notes:
            console.print(f"  Notes: {entry.notes}")
        if entry.stored_path:
            console.print(f"  Stored: {entry.stored_path}")
        if entry.s3_key:
            console.print(f"  S3: {entry.s3_key}")


@app.command()
def validate(
    key: str = typer.Argument(..., help="Source key to validate"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Re-validate an entry by checking URL."""
    with HTTPClient() as client:
        # Initialize services
        file_validator = FileValidator(client)
        validation_rules = ValidationRules()

        # Create use case
        use_case = ValidateSourceUseCase(
            registry_repository=registry_repository,
            file_validator=file_validator,
            contract_service=contract_service,
            http_client=client,
            validation_rules=validation_rules,
        )

        # Execute use case
        result = use_case.execute(key)

        if not result.success:
            console.print(f"[red]{result.error}[/red]")
            sys.exit(1)

        # Format output
        output = {
            "key": result.key,
            "url": result.entry.url,
            "status": result.status,
            "mime": result.mime,
            "size_kb": result.size_kb,
            "mime_valid": result.mime_valid,
            "size_valid": result.size_valid,
        }

        if output_json:
            console.print(json.dumps(output, indent=2))
        else:
            console.print(f"[green]Validation for {result.key}:[/green]")
            console.print(f"  Status: {result.status}")
            console.print(f"  MIME: {result.mime} ({'✓' if result.mime_valid else '✗'})")
            console.print(f"  Size: {result.size_kb:.2f} KB ({'✓' if result.size_valid else '✗'})")


@app.command()
def sync(
    all: bool = typer.Option(False, "--all", "-a", help="Sync all sources"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Sync specific key"),
    mirror: bool = typer.Option(True, help="Download mirror copy"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Sync sources (discover all or specific)."""
    if not all and not key:
        console.print("[red]Either --all or --key must be specified[/red]")
        sys.exit(1)

    # Get contracts to sync
    contracts = contract_service.load_contracts()
    if not contracts:
        console.print("[red]No contracts found[/red]")
        sys.exit(1)

    if key:
        # Sync specific key
        contract = contract_service.get_contract(key)
        if not contract:
            console.print(f"[red]Contract not found for key: {key}[/red]")
            sys.exit(1)
        contracts = [contract]

    results = []
    with HTTPClient() as client:
        # Initialize services
        file_validator = FileValidator(client)
        mirror_service = MirrorService(client)
        validation_rules = ValidationRules()

        # Create use case
        use_case = DiscoverSourceUseCase(
            contract_service=contract_service,
            registry_repository=registry_repository,
            mirror_service=mirror_service,
            file_validator=file_validator,
            http_client=client,
            validation_rules=validation_rules,
        )

        # Execute for each contract
        for contract in contracts:
            key = contract.get("key")
            if not key:
                logger.warning("Contract missing 'key' field, skipping")
                continue

            try:
                result = use_case.execute(key, mirror=mirror)

                if result.success:
                    results.append({
                        "key": result.key,
                        "status": "ok",
                        "url": result.discovered.url,
                        "version": result.discovered.version,
                    })
                else:
                    results.append({
                        "key": key,
                        "status": "error",
                        "error": result.error,
                    })

            except Exception as e:
                logger.error(f"Failed to sync {key}: {e}")
                results.append({"key": key, "status": "error", "error": str(e)})

    if output_json:
        console.print(json.dumps(results, indent=2))
    else:
        console.print(f"[green]Synced {len([r for r in results if r.get('status') == 'ok'])} sources[/green]")
        for result in results:
            status_icon = "✓" if result.get("status") == "ok" else "✗"
            console.print(f"  {status_icon} {result.get('key')}: {result.get('status')}")


@app.command()
def discover_files(
    output_file: str = typer.Option("discovered_files.json", "--output", "-o", help="Output file path"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON to stdout"),
    filter_ext: Optional[str] = typer.Option(None, "--filter-ext", "-e", help="Filter by file extensions (comma-separated, e.g., .xls,.pdf,.xlsx)"),
):
    """
    Discover all valid files from all sources and save normalized URLs.
    
    This command finds all valid files, normalizes their URLs (encoding spaces and special characters),
    validates them, and saves the results. URLs are automatically normalized during discovery.
    """
    # Parse extensions filter
    extensions = None
    if filter_ext:
        extensions = [ext.strip() for ext in filter_ext.split(",")]
        # Ensure extensions start with dot
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
        logger.info(f"Filtering by extensions: {extensions}")

    with HTTPClient() as client:
        # Initialize services - always validate to ensure we only get valid files
        file_validator = FileValidator(client)
        html_parser = HTMLParser(client)

        # Create use case
        use_case = DiscoverAllLinksUseCase(
            contract_service=contract_service,
            file_validator=file_validator,
            http_client=client,
            html_parser=html_parser,
        )

        # Execute use case (always validate, URLs are normalized automatically)
        result = use_case.execute(
            filter_extensions=extensions,
            validate=True,  # Always validate to get only valid files
        )

    # Convert to JSON-serializable format (URLs are already normalized)
    all_files_data = {}
    for key, source_result in result.sources.items():
        all_files_data[key] = {
            "key": source_result.key,
            "start_urls": source_result.start_urls,
            "files": [
                {
                    "url": link.url,  # Already normalized
                    "text": link.text,
                    "source_page": link.source_page,
                    "mime": link.mime,
                    "size_kb": link.size_kb,
                    "size_bytes": link.size_bytes,
                    "content_disposition": link.content_disposition,
                }
                for link in source_result.links_found
                if link.status == "ok"  # Only include valid files
            ],
            "selected_file": source_result.selected_link,
            "filter_extensions": source_result.filter_extensions,
            "error": source_result.error,
        }

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_files_data, f, indent=2, ensure_ascii=False)

    # Calculate stats
    total_files = sum(len(data["files"]) for data in all_files_data.values())
    selected_count = sum(
        1
        for data in all_files_data.values()
        if data.get("selected_file") and "error" not in data.get("selected_file", {})
    )

    # Format output
    output = {
        "output_file": str(output_path),
        "sources_processed": len(all_files_data),
        "total_files_found": total_files,
        "selected_files": selected_count,
        "sources": list(all_files_data.keys()),
        "urls_normalized": True,
    }

    if output_json:
        console.print(json.dumps(output, indent=2))
    else:
        console.print(f"[green]Discovery complete![/green]")
        console.print(f"  Output file: {output_path}")
        console.print(f"  Sources processed: {len(all_files_data)}")
        console.print(f"  Total valid files found: {total_files}")
        console.print(f"  Selected files: {selected_count}")
        console.print(f"  URLs normalized: ✓")
        if extensions:
            console.print(f"  Filtered by extensions: {', '.join(extensions)}")
        console.print(f"\nFiles saved to: {output_path}")
    
    # Exit successfully
    sys.exit(0)


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()

