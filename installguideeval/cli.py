"""Command-line entry point for FOSSInstallGuideEval."""

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
    """Run one schema-constrained installation-guide evaluation."""

    # The CLI stays intentionally small: the runner owns all experiment logic.
    console.print(
        f"[bold blue]Starting FOSSInstallGuideEval[/bold blue] for task: "
        f"[bold green]{task_id}[/bold green]"
    )
    try:
        result = EvaluationRunner().run(task_id)
    except Exception as exc:
        console.print(f"[bold red]Could not complete evaluation run:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if result["run"]["status"] == "completed":
        console.print(
            f"[bold green]Evaluation run {result['run']['run_id']} completed.[/bold green]"
        )
        return

    # A failed API call is still recorded as a run, but the command must return
    # a non-zero exit code so batch scripts can detect the failure.
    console.print(
        f"[bold red]Evaluation run {result['run']['run_id']} failed:[/bold red] "
        f"{result['run']['error']['message']}"
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
