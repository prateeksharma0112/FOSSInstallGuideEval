"""Run the experiment from the command line."""

import typer
from rich.console import Console

from installguideeval.runner import EvaluationRunner

app = typer.Typer(
    help="FOSSInstallGuideEval - criteria-based LLM evaluation of FOSS installation guides"
)
console = Console()


@app.command(name="run")
def run_task(
    task_id: str = typer.Option(
        ..., "--task-id", "-t", help="The ID of the guide-evaluation task to run"
    ),
) -> None:
    """Run one installation-guide evaluation."""

    console.print(
        f"[bold blue]Starting evaluation for task:[/bold blue] "
        f"[bold green]{task_id}[/bold green]\n"
    )
    try:
        run_record = EvaluationRunner(show_progress=console.print).run(task_id)
    except Exception as exc:
        console.print(f"[bold red]Could not complete evaluation run:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if run_record["run"]["status"] == "completed":
        console.print(
            f"\n[bold green]Evaluation completed:[/bold green] "
            f"{run_record['run']['run_id']}"
        )
        return

    # Return a failure code after saving the failed run.
    console.print(
        f"\n[bold red]Evaluation failed:[/bold red] "
        f"{run_record['run']['run_id']} - "
        f"{run_record['run']['error']['message']}"
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
