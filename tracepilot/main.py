"""TracePilot CLI — main entry point."""

import asyncio
import click
import os

# Load .env file
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


@click.group()
def cli():
    """TracePilot — Learning operational decisions from observability data."""
    pass


@cli.command()
@click.argument("query")
@click.option("--db", default="tracepilot_memory.db", help="Path to Economic Memory database")
def query(query: str, db: str):
    """Run a query through the TracePilot orchestrator."""
    from tracepilot.tracing import init_tracing
    init_tracing()
    
    from tracepilot.orchestrator import run_query
    asyncio.run(run_query(query, db))


@cli.command()
@click.option("--db", default="tracepilot_memory.db", help="Path to Economic Memory database")
def audit(db: str):
    """Run the Auditor to update Economic Memory from Phoenix traces."""
    from tracepilot.auditor import run_audit
    run_audit(db)


@cli.command()
@click.option("--db", default="tracepilot_memory.db", help="Path to Economic Memory database")
def status(db: str):
    """Show current Economic Memory confidence table."""
    from tracepilot.memory import init_db, get_confidence_table
    from tracepilot.display import print_confidence_table
    
    init_db(db)
    rows = get_confidence_table(db)
    print_confidence_table(rows)


@cli.command()
@click.option("--db", default="tracepilot_memory.db", help="Path to Economic Memory database")
def reset(db: str):
    """Reset the Economic Memory database (for demo reruns)."""
    from tracepilot.memory import reset_db
    reset_db(db)
    click.echo("Economic Memory reset. Ready for a fresh demo.")


if __name__ == "__main__":
    cli()
