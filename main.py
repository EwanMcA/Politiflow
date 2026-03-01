import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select
from models import Poll, PollAverage, engine, create_db_and_tables
from scraper import scrape_ballotpedia

app = typer.Typer()
console = Console()

@app.command()
def sync():
    """Fetch latest polling data from Ballotpedia."""
    with console.status("[bold green]Scraping Ballotpedia..."):
        scrape_ballotpedia()
    console.print("[bold green]Success![/bold green] Database updated.")

@app.command()
def show(limit: int = 10):
    """Display latest polling data and averages."""
    create_db_and_tables()
    with Session(engine) as session:
        # Show averages
        averages = session.exec(select(PollAverage).order_by(PollAverage.date_updated.desc())).all()
        if averages:
            table = Table(title="Polling Averages")
            table.add_column("Type", style="cyan")
            table.add_column("Positive (%)", style="green")
            table.add_column("Negative (%)", style="red")
            
            # Show most recent per type
            seen_types = set()
            for avg in averages:
                if avg.poll_type not in seen_types:
                    table.add_row(avg.poll_type, str(avg.positive_avg), str(avg.negative_avg))
                    seen_types.add(avg.poll_type)
            console.print(table)

        # Show individual polls
        polls = session.exec(select(Poll).order_by(Poll.created_at.desc()).limit(limit)).all()
        if polls:
            table = Table(title=f"Latest {limit} Individual Polls")
            table.add_column("Type", style="cyan")
            table.add_column("Source", style="magenta")
            table.add_column("Date", style="yellow")
            table.add_column("Pos/Neg", style="white")
            table.add_column("MOE", style="dim")
            
            for p in polls:
                table.add_row(
                    p.poll_type, 
                    p.source, 
                    p.date_range, 
                    f"{p.positive_result}/{p.negative_result}", 
                    p.margin_of_error
                )
            console.print(table)
        else:
            console.print("[yellow]No polls found. Run 'sync' first.[/yellow]")

if __name__ == "__main__":
    app()