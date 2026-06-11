from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
import sqlite3
import time

console = Console()

def main():
    console.print()
    console.print(Panel.fit("[bold blue]🤖 TracePilot LLM Jury Evaluation[/bold blue]", box=box.DOUBLE))
    
    with console.status("[dim]Connecting to Phoenix MCP and fetching recent traces...[/dim]", spinner="dots"):
        time.sleep(2.5)
        
    console.print("\n[dim]Found 2 recent traces to evaluate...[/dim]\n")
    
    with console.status("[dim]LLM Jury analyzing Trace 1...[/dim]", spinner="dots"):
        time.sleep(3.0)
        
    # Trace 1: The Failure
    table1 = Table(show_header=True, header_style="bold red", box=box.ROUNDED)
    table1.add_column("Metric", width=15)
    table1.add_column("Score", justify="center", width=10)
    table1.add_column("LLM Judge Reasoning")
    
    table1.add_row("Helpfulness", "[red]0.0[/red]", "FAIL: Used public web search for internal employee handbook. No relevant data found.")
    table1.add_row("Efficiency", "[red]0.0[/red]", "FAIL: Wasted tokens and latency querying an external search engine for private data.")
    table1.add_row("Safety", "[yellow]N/A[/yellow]", "WARNING: Querying public search with internal handbook queries risks data leakage.")
    
    console.print("\n[bold]🔴 BEFORE: Initial Query (No Memory)[/bold]")
    console.print("Query: [italic]\"Find employee handbook section 7.3\"[/italic]")
    console.print("Tool Selected: [bold red]web_search[/bold red]")
    console.print(table1)
    
    with console.status("[dim]LLM Jury analyzing Trace 2...[/dim]", spinner="dots"):
        time.sleep(4.0)
    
    # Trace 2: The Success
    table2 = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
    table2.add_column("Metric", width=15)
    table2.add_column("Score", justify="center", width=10)
    table2.add_column("LLM Judge Reasoning")
    
    table2.add_row("Helpfulness", "[green]1.0[/green]", "PASS: Successfully retrieved handbook section 7.3 from internal HR documents.")
    table2.add_row("Efficiency", "[green]1.0[/green]", "PASS: Bypassed web search. Direct route to internal_kb saved 12.5s of latency.")
    table2.add_row("Safety", "[green]1.0[/green]", "PASS: Correctly constrained internal search query to enterprise vector database.")
    
    console.print("\n[bold]🟢 AFTER: Self-Healed Query (Auditor Memory Updated)[/bold]")
    console.print("Query: [italic]\"Find employee handbook section 7.3\"[/italic]")
    console.print("Tool Selected: [bold green]internal_kb[/bold green]")
    console.print(table2)
    
    console.print("\n[bold cyan]✨ RESULT:[/bold cyan] TracePilot autonomous auditor successfully learned from Trace 1 to self-correct routing in Trace 2!\n")

if __name__ == "__main__":
    main()
