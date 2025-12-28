#!/usr/bin/env python3
"""
JLAW ML Model Pre-Download Script
==================================

Downloads and caches all ML models required for JLAW forensic analysis.
This script should be run before first analysis to avoid cold-start delays.

Usage:
    python scripts/download_ml_models.py
    python scripts/download_ml_models.py --force
    python scripts/download_ml_models.py --list
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        DownloadColumn,
        TransferSpeedColumn,
        TimeRemainingColumn
    )
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from src.ml.model_registry import ModelRegistry


async def download_all_models(force: bool = False) -> int:
    """
    Download all registered models.
    
    Args:
        force: Force re-download even if cached
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    console = Console() if RICH_AVAILABLE else None
    registry = ModelRegistry()
    
    if console:
        console.print("[cyan]🤖 JLAW ML Model Downloader[/cyan]\n")
        console.print(f"Cache directory: {registry.get_cache_dir()}\n")
    else:
        print("JLAW ML Model Downloader")
        print(f"Cache directory: {registry.get_cache_dir()}\n")
    
    # Determine which models need downloading
    models_to_download = []
    for model_name, model_info in registry.MODELS.items():
        if force or not registry.is_model_cached(model_name):
            models_to_download.append(model_info)
        else:
            msg = f"✅ {model_name} (already cached)"
            if console:
                console.print(f"[green]{msg}[/green]")
            else:
                print(msg)
    
    if not models_to_download:
        msg = "\n✅ All models are already cached!"
        if console:
            console.print(f"[green]{msg}[/green]")
        else:
            print(msg)
        return 0
    
    # Show download plan
    total_size_mb = sum(m.size_mb for m in models_to_download)
    msg = f"\n📥 Downloading {len(models_to_download)} models (~{total_size_mb} MB total)\n"
    
    if console:
        console.print(f"[yellow]{msg}[/yellow]")
    else:
        print(msg)
    
    # Download each model
    for model_info in models_to_download:
        success = await download_model(model_info, console)
        if not success:
            if console:
                console.print(f"[red]❌ Download failed: {model_info.name}[/red]")
            else:
                print(f"Download failed: {model_info.name}")
            return 1
    
    msg = "\n✅ All models downloaded successfully!"
    if console:
        console.print(f"[green]{msg}[/green]")
    else:
        print(msg)
    
    return 0


async def download_model(model_info, console) -> bool:
    """
    Download a single model.
    
    Args:
        model_info: ModelInfo object
        console: Rich console (or None)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import transformers library
        try:
            from transformers import AutoModel, AutoTokenizer
        except ImportError:
            msg = "transformers library not installed. Run: pip install transformers"
            if console:
                console.print(f"[red]{msg}[/red]")
            else:
                print(msg)
            return False
        
        cache_dir = ModelRegistry.get_cache_dir() / model_info.name
        
        msg = f"⏬ Downloading {model_info.name} (~{model_info.size_mb} MB)..."
        if console:
            console.print(f"[cyan]{msg}[/cyan]")
        else:
            print(msg)
        
        # Download model and tokenizer
        AutoModel.from_pretrained(
            model_info.model_id,
            cache_dir=cache_dir
        )
        AutoTokenizer.from_pretrained(
            model_info.model_id,
            cache_dir=cache_dir
        )
        
        msg = f"✅ Downloaded: {model_info.name}"
        if console:
            console.print(f"[green]{msg}[/green]")
        else:
            print(msg)
        
        return True
        
    except Exception as e:
        msg = f"Error downloading {model_info.name}: {e}"
        if console:
            console.print(f"[red]{msg}[/red]")
        else:
            print(msg)
        return False


def list_models(console):
    """
    List all registered models with their status.
    
    Args:
        console: Rich console (or None)
    """
    registry = ModelRegistry()
    models = registry.list_all_models()
    
    if console:
        table = Table(title="Registered ML Models")
        table.add_column("Name", style="cyan")
        table.add_column("Size (MB)", justify="right")
        table.add_column("Status", style="green")
        table.add_column("Required For")
        
        for model in models:
            status = "✅ Cached" if model['cached'] else "⬇️  Not Cached"
            required_for = ", ".join(model['required_for'])
            table.add_row(
                model['name'],
                str(model['size_mb']),
                status,
                required_for
            )
        
        console.print(table)
        console.print(f"\nTotal size: ~{registry.get_total_size_mb()} MB")
        console.print(f"Cached: ~{registry.get_cached_size_mb()} MB")
    else:
        print("Registered ML Models:")
        print("-" * 80)
        for model in models:
            status = "Cached" if model['cached'] else "Not Cached"
            required_for = ", ".join(model['required_for'])
            print(f"  {model['name']}: {status}")
            print(f"    Size: {model['size_mb']} MB")
            print(f"    Required for: {required_for}")
            print()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download JLAW ML models"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if cached'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all models and their status'
    )
    
    args = parser.parse_args()
    
    console = Console() if RICH_AVAILABLE else None
    
    if args.list:
        list_models(console)
        return 0
    
    return await download_all_models(force=args.force)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
