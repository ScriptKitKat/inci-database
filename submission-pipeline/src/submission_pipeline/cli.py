"""Submission pipeline CLI.

`run` executes one full worker tick (the GitHub Actions cron entrypoint);
`submit` creates a submission row for testing or manual entry.
"""

from __future__ import annotations

import logging

import typer

from .config import settings

app = typer.Typer(help="User-submission product verification pipeline.")

STAGE_ORDER = ("poll", "intake", "submit_batch", "apply", "describe", "purge")


def _configure_logging() -> None:
    logging.basicConfig(
        level=settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _stages() -> dict[str, object]:
    from .stages import apply as apply_stage
    from .stages import intake, purge, verify

    return {
        "poll": verify.poll,
        "intake": intake.run,
        "submit_batch": verify.submit,
        "apply": apply_stage.run,
        "describe": apply_stage.describe,
        "purge": purge.run,
    }


@app.command()
def run(
    stage: str = typer.Option(
        None, "--stage", help="Run a single stage: " + " | ".join(STAGE_ORDER)
    ),
) -> None:
    """Run one worker tick: poll -> intake -> submit_batch -> apply -> describe -> purge."""
    _configure_logging()
    stages = _stages()
    if stage is not None:
        if stage not in stages:
            raise typer.BadParameter(f"unknown stage: {stage}")
        selected = [stage]
    else:
        selected = list(STAGE_ORDER)
    for name in selected:
        counters = stages[name]()  # type: ignore[operator]
        typer.echo(f"{name}: {counters}")


@app.command()
def submit(
    brand: str = typer.Option(..., "--brand", help="Brand name as printed on the product."),
    name: str = typer.Option(..., "--name", help="Product name."),
    ingredients: str = typer.Option(
        ..., "--ingredients", help="Raw ingredient list text (pasted from the label)."
    ),
) -> None:
    """Create a submission (status=received); the worker picks it up next tick."""
    from . import db

    _configure_logging()
    row = db.create_submission(brand, name, ingredients)
    typer.echo(row["id"])


if __name__ == "__main__":
    app()
