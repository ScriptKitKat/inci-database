"""CLI for product-derived ingredient cleanup."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from time import sleep
from uuid import UUID

import typer

from .config import settings

app = typer.Typer(help="Ingredient cleanup ETL for product-derived ingredient rows.")


def _parse_datetime_input(raw: str, *, end_of_day: bool = False) -> datetime:
    raw = raw.strip()
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        try:
            parsed_date = date.fromisoformat(raw)
        except ValueError as exc:
            raise typer.BadParameter(
                f"{raw!r} is not a valid date/datetime. Use YYYY-MM-DD or ISO-8601."
            ) from exc
        if end_of_day:
            return datetime.combine(parsed_date + timedelta(days=1), time.min)
        return datetime.combine(parsed_date, time.min)
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{raw!r} is not a valid date/datetime. Use YYYY-MM-DD or ISO-8601."
        ) from exc


def _configure_logging() -> None:
    logging.basicConfig(
        level=settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command("queue")
def queue(
    since: str = typer.Option(..., "--since", help="Inclusive lower bound."),
    until: str | None = typer.Option(None, "--until", help="Exclusive upper bound."),
) -> None:
    """Backfill existing ingredients into the cleanup queue."""
    from .stages.curate_ingredient_names import queue_window

    _configure_logging()
    since_dt = _parse_datetime_input(since)
    until_dt = _parse_datetime_input(until, end_of_day=True) if until else _parse_datetime_input(since, end_of_day=True)
    count = queue_window(since_dt, until_dt)
    typer.echo(f"queued {count} ingredient(s)")


@app.command("curate")
def curate(
    limit: int = typer.Option(500, "--limit", help="Maximum pending queue rows to claim."),
) -> None:
    """Run deterministic normalized-name curation over queued ingredients."""
    from .stages.curate_ingredient_names import run as curate_run

    _configure_logging()
    run_id = curate_run(limit=limit)
    typer.echo(f"curation run {run_id}")


@app.command("submit-judge-batch")
def submit_judge_batch(
    run_id: UUID = typer.Option(..., "--run-id", help="Curation run id."),
    model: str | None = typer.Option(None, "--model", help="Override judge model."),
    temperature: float | None = typer.Option(None, "--temperature", help="Override judge temperature."),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Override judge max_tokens."),
) -> None:
    """Submit ambiguous candidates to Anthropic Message Batches."""
    from .curation.llm_batch import submit_batch

    _configure_logging()
    batch_id = submit_batch(
        run_id,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    typer.echo(f"submitted Anthropic batch {batch_id}" if batch_id else "no pending LLM items")


@app.command("retrieve-judge-batch")
def retrieve_judge_batch(
    batch_id: str = typer.Option(..., "--batch-id", help="Anthropic Message Batch id."),
) -> None:
    """Retrieve an Anthropic batch and import validated decisions."""
    from .curation.llm_batch import retrieve_batch

    _configure_logging()
    result = retrieve_batch(batch_id)
    typer.echo(
        f"batch {result['status']}; imported {result.get('processed', 0)} LLM decision(s)"
    )


@app.command("apply")
def apply(
    run_id: UUID = typer.Option(..., "--run-id", help="Curation run id."),
) -> None:
    """Apply eligible cleanup decisions transactionally."""
    from .stages.curate_ingredient_names import apply as apply_run

    _configure_logging()
    messages = apply_run(run_id)
    for message in messages:
        typer.echo(message)
    if not messages:
        typer.echo("no eligible decisions to apply")


@app.command("auto")
def auto(
    since: str = typer.Option(..., "--since", help="Inclusive lower bound."),
    until: str | None = typer.Option(None, "--until", help="Exclusive upper bound."),
    limit: int = typer.Option(500, "--limit", help="Rows to claim in deterministic pass."),
    model: str | None = typer.Option(None, "--model", help="Override judge model."),
    temperature: float | None = typer.Option(None, "--temperature", help="Override judge temperature."),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Override judge max_tokens."),
    wait_for_batch: bool = typer.Option(
        True,
        "--wait-for-batch/--no-wait-for-batch",
        help="Poll Anthropic batch completion and continue automatically.",
    ),
    poll_interval_seconds: int | None = typer.Option(None, "--poll-interval-seconds"),
    poll_timeout_seconds: int | None = typer.Option(None, "--poll-timeout-seconds"),
) -> None:
    """Queue, curate, judge, and apply ingredient cleanup in one command."""
    from .curation.llm_batch import retrieve_batch, submit_batch
    from .stages.curate_ingredient_names import queue_window, run as curate_run

    _configure_logging()
    s = settings()
    since_dt = _parse_datetime_input(since)
    until_dt = _parse_datetime_input(until, end_of_day=True) if until else _parse_datetime_input(since, end_of_day=True)

    queued = queue_window(since_dt, until_dt)
    typer.echo(f"queued {queued} ingredient(s)")

    run_id = curate_run(limit=limit)
    typer.echo(f"curation run {run_id}")

    batch_id = submit_batch(
        UUID(run_id),
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if batch_id is None:
        typer.echo("no pending LLM items; applying deterministic decisions")
        _echo_apply_messages(UUID(run_id))
        return

    typer.echo(f"submitted Anthropic batch {batch_id}")
    if not wait_for_batch:
        return

    poll_interval = poll_interval_seconds or s.ingredient_judge_poll_interval_seconds
    poll_timeout = poll_timeout_seconds or s.ingredient_judge_poll_timeout_seconds
    deadline = datetime.now() + timedelta(seconds=poll_timeout)
    while True:
        result = retrieve_batch(batch_id)
        typer.echo(
            f"batch {result['status']}; imported {result.get('processed', 0)} LLM decision(s)"
        )
        if result["status"] != "processing":
            break
        if datetime.now() >= deadline:
            typer.echo(
                f"Anthropic batch {batch_id} did not finish within {poll_timeout} seconds"
            )
            raise typer.Exit(code=2)
        sleep(poll_interval)

    _echo_apply_messages(UUID(run_id))


def _echo_apply_messages(run_id: UUID) -> None:
    from .stages.curate_ingredient_names import apply as apply_run

    messages = apply_run(run_id)
    for message in messages:
        typer.echo(message)
    if not messages:
        typer.echo("no eligible decisions to apply")


if __name__ == "__main__":
    app()
