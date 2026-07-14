"""Pipeline CLI. Each stage is a separate subcommand for the cron job."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import typer

from .config import settings

app = typer.Typer(help="INCI database pipeline.")


def _configure_logging() -> None:
    logging.basicConfig(
        level=settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _stage_runner(stage: str) -> Callable[[bool], None]:
    """Import a stage module lazily so a missing dependency in stage X
    doesn't break the entire CLI."""
    import importlib

    module_map = {
        "obf-taxonomy": "inci_pipeline.stages.seed_obf_taxonomy",
        "wikidata": "inci_pipeline.stages.enrich_wikidata",
        "pubchem": "inci_pipeline.stages.enrich_pubchem",
        "obf-aliases": "inci_pipeline.stages.harvest_obf_aliases",
        "pubmed": "inci_pipeline.stages.fetch_pubmed",
        "editorial": "inci_pipeline.stages.generate_editorial",
        "classify": "inci_pipeline.stages.classify_tags",
        "products": "inci_pipeline.stages.seed_products",
    }
    if stage not in module_map:
        raise typer.BadParameter(f"unknown stage: {stage}")
    mod = importlib.import_module(module_map[stage])
    return mod.run  # type: ignore[attr-defined]


@app.command()
def run(
    stage: str = typer.Argument(
        ...,
        help="obf-taxonomy | wikidata | pubchem | obf-aliases | pubmed | editorial | classify | products",
    ),
    force: bool = typer.Option(False, "--force", help="Bypass last-success guard."),
    process_all: bool = typer.Option(
        False,
        "--all",
        help=(
            "For pubmed/editorial only: bypass the curation queue and run "
            "against every ingredient. Editorial costs ~$0.01/ingredient "
            "at Sonnet pricing -- use deliberately."
        ),
    ),
) -> None:
    """Run a single pipeline stage."""
    import inspect

    _configure_logging()
    runner = _stage_runner(stage)
    kwargs: dict[str, object] = {"force": force}
    if "process_all" in inspect.signature(runner).parameters:
        kwargs["process_all"] = process_all
    runner(**kwargs)


@app.command()
def match(token: str) -> None:
    """Resolve a single label token against the ingredient + alias index."""
    from .matching.match import match_token

    _configure_logging()
    result = match_token(token)
    if not result:
        typer.echo("no match")
        raise typer.Exit(code=1)
    typer.echo(f"{result.ingredient_id} {result.match_type} {result.confidence:.3f}")


@app.command("export-editorial-prompts")
def export_editorial_prompts(
    out_dir: Path = typer.Option(
        Path("../data/editorial_inbox"),
        "--out",
        help="Directory to write <slug>.prompt.md files into.",
    ),
) -> None:
    """Write one prompt file per curated ingredient for the manual
    Claude.ai / ChatGPT paste workflow. Save each AI response back as
    <slug>.json in the same folder, then run `import-editorial`."""
    from .stages.export_editorial import run as export_run

    _configure_logging()
    export_run(out_dir)


@app.command("import-editorial")
def import_editorial(
    in_dir: Path = typer.Option(
        Path("../data/editorial_inbox"),
        "--in",
        help="Directory containing <slug>.json response files.",
    ),
    reviewer: str = typer.Option(
        "manual",
        "--reviewer",
        help="Stored in ingredient_writeups.editorial_metadata as `manual:<reviewer>`.",
    ),
) -> None:
    """Import JSON responses written by the manual paste workflow into
    ingredient_writeups. Processed files move to <in>/processed/."""
    from .stages.import_editorial import run as import_run

    _configure_logging()
    import_run(in_dir, reviewer)


if __name__ == "__main__":
    app()
