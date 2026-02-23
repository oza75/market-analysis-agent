from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path


def iso_week_label(reference: date, weeks_ago: int) -> str:
    """
    Return an ISO week label for a date offset from a reference.

    Parameters
    ----------
    reference : date
        The reference date to offset from.
    weeks_ago : int
        Number of weeks before the reference date.

    Returns
    -------
    str
        ISO week label in the format ``YYYY-Www``, e.g. ``"2026-W04"``.
    """
    target = reference - timedelta(weeks=weeks_ago)
    year, week, _ = target.isocalendar()
    return f"{year}-W{week:02d}"


def load_prompt(
    name: str,
    *,
    prompts_dir: Path | None = None,
) -> str:
    """
    Load a prompt from a markdown file in the prompts directory.

    Parameters
    ----------
    name : str
        Prompt name (file stem). The file loaded is ``{name}.md``.
    prompts_dir : Path, optional
        Directory containing prompt markdown files. If ``None``, defaults to
        ``analyst_agent/prompts`` relative to this module.

    Returns
    -------
    str
        Raw text content of the prompt file.

    Raises
    ------
    FileNotFoundError
        When the prompt file ``{name}.md`` does not exist in ``prompts_dir``.
    """
    if prompts_dir is None:
        prompts_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompts_dir / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
