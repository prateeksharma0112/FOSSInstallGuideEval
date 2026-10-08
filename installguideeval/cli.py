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
        f"[bold blue]Starting FOSSInstallGuideEval[/bold blue] for task: "
        f"[bold green]{task_id}[/bold green]"
    )
    try:
        run_record = EvaluationRunner().run(task_id)
    except Exception as exc:
        console.print(f"[bold red]Could not complete evaluation run:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if run_record["run"]["status"] == "completed":
        console.print(
            f"[bold green]Evaluation run {run_record['run']['run_id']} completed.[/bold green]"
        )
        return

    # Return a failure code after saving the failed run.
    console.print(
        f"[bold red]Evaluation run {run_record['run']['run_id']} failed:[/bold red] "
        f"{run_record['run']['error']['message']}"
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
