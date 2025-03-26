#!/usr/bin/env python3
from pathlib import Path

import typer
from rich import print
from rich.console import Console
from rich.panel import Panel

from cp_agent.config import settings
from cp_agent.kb.kb_manager import KnowledgeBaseManager

app = typer.Typer(help="Knowledge Base Management CLI")
console = Console()


def get_kb(collection: str) -> KnowledgeBaseManager:
    """Get KB manager instance with given configuration."""
    return KnowledgeBaseManager(collection_name=collection)


@app.command()
def ingest(
    data_dir: Path = typer.Argument(
        ..., help="Directory containing text files to ingest"
    ),
    collection: str = typer.Option(
        "default", "--collection", help="Name of the vector store collection"
    ),
) -> None:
    """Ingest data from the specified directory into the knowledge base."""
    with console.status(f"Processing files from directory: {data_dir}"):
        kb = get_kb(collection)
        kb.process_text_files(data_dir)
        print("\n[green]Data ingestion complete! ✨[/green]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(4, "--top-k", help="Number of results to return"),
    collection: str = typer.Option(
        "default", "--collection", help="Name of the vector store collection"
    ),
) -> None:
    """Search the knowledge base for similar documents."""
    kb = get_kb(collection)
    results = kb.search_similar(query, top_k=top_k)

    print(f"\n[blue]Search results for:[/blue] '{query}'\n")
    for doc, score in results:
        print(
            Panel(
                f"[yellow]Score:[/yellow] {score:.4f}\n"
                f"[yellow]Source:[/yellow] {doc.metadata.get('source', 'Unknown')}\n"
                f"[yellow]Content:[/yellow] {doc.content[:200]}...",
                expand=False,
            )
        )


@app.command()
def nuke(
    collection: str = typer.Option(
        "default", "--collection", help="Name of the vector store collection"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """Delete all data from the knowledge base."""
    if not force:
        should_continue = typer.confirm(
            "⚠️  This will delete all data from the knowledge base. Are you sure?"
        )
        if not should_continue:
            print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit()

    kb = get_kb(collection)
    with console.status("Clearing knowledge base..."):
        kb.nuke()
        print("[green]Knowledge base has been cleared! 🧹[/green]")


@app.command()
def list_collections(
    collection: str = typer.Option(
        "default", "--collection", help="Name of the vector store collection"
    ),
) -> None:
    """List all available collections in the knowledge base."""
    kb = get_kb(collection)
    collections = kb.list_collections()

    if not collections:
        print("[yellow]No collections found[/yellow]")
        return

    print("\n[blue]Available Collections:[/blue]\n")
    for col in collections:
        print(f"📚 {col}")


@app.command()
def info() -> None:
    """Show information about the current knowledge base configuration."""
    print("\n[blue]Knowledge Base Configuration:[/blue]\n")
    print(f"[yellow]Client Type:[/yellow] {settings.KB_CHROMA_CLIENT_TYPE}")

    if settings.KB_CHROMA_CLIENT_TYPE == "persistent":
        print(f"[yellow]Storage Directory:[/yellow] {settings.KB_CHROMA_DIRECTORY}")
    else:  # http
        protocol = "https" if settings.KB_CHROMA_HTTP_SSL else "http"
        print(
            f"[yellow]Server URL:[/yellow] {protocol}://{settings.KB_CHROMA_HTTP_HOST}:{settings.KB_CHROMA_HTTP_PORT}"
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
