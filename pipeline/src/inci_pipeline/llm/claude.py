"""Anthropic client wrapper. Generates structured editorial summaries.

Models are referenced via the package's constants (see plan §2.3):
  * Sonnet 4.6  - editorial synthesis
  * Haiku 4.5   - cheap synonym extraction (not used here yet)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import orjson
from anthropic import Anthropic

from ..config import settings

EDITORIAL_MODEL = "claude-sonnet-4-6"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

_PROMPT_PATH = Path(__file__).parent / "prompts" / "editorial_summary.md"


@dataclass(frozen=True)
class Editorial:
    summary_short: str
    summary_long: str
    quick_facts: list[str]
    what_it_does: str


def _client() -> Anthropic:
    s = settings()
    if not s.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=s.anthropic_api_key)


def build_editorial_prompt(
    *,
    inci_name: str,
    function_tags: list[str],
    is_restricted_eu: bool,
    is_restricted_us: bool,
    abstracts: list[dict],
) -> str:
    """Assemble the editorial prompt. Used both by the API call path
    and by the manual-paste export workflow."""
    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    abstracts_text = "\n\n".join(
        f"PMID: {a.get('raw_payload', {}).get('pmid', 'unknown')}\n"
        f"Title: {a.get('title') or ''}\n"
        f"Year: {a.get('raw_payload', {}).get('year', '')}\n"
        f"Abstract: {a.get('raw_payload', {}).get('abstract', '')}"
        for a in abstracts
    )
    return prompt_template.format(
        inci_name=inci_name,
        function_tags=", ".join(function_tags) or "(unspecified)",
        restricted_eu="yes" if is_restricted_eu else "no",
        restricted_us="yes" if is_restricted_us else "no",
        abstracts=abstracts_text,
    )


def generate_editorial(
    *,
    inci_name: str,
    function_tags: list[str],
    is_restricted_eu: bool,
    is_restricted_us: bool,
    abstracts: list[dict],
) -> Editorial:
    """Single Claude call. Returns structured fields ready for
    ingredient_writeups insert."""
    user_msg = build_editorial_prompt(
        inci_name=inci_name,
        function_tags=function_tags,
        is_restricted_eu=is_restricted_eu,
        is_restricted_us=is_restricted_us,
        abstracts=abstracts,
    )
    resp = _client().messages.create(
        model=EDITORIAL_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = resp.content[0].text  # type: ignore[union-attr]
    return parse_editorial_response(raw)


def parse_editorial_response(raw: str) -> Editorial:
    """Parse a JSON editorial response. Tolerates code-fence wrapping
    from either Claude.ai or ChatGPT."""
    payload = orjson.loads(_extract_json(raw))
    return Editorial(
        summary_short=payload["summary_short"],
        summary_long=payload["summary_long"],
        quick_facts=payload.get("quick_facts", []),
        what_it_does=payload["what_it_does"],
    )


def _extract_json(text: str) -> str:
    """Strip Markdown fences around JSON responses."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()
