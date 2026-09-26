"""Load leaderboard scores from auto-judge eval files.

Requires the optional ``[autojudge]`` extra (the ``autojudge-evaluate``
package). Everything else in ``circularity_reveal`` works without it.
"""
from __future__ import annotations

from pathlib import Path

from autojudge_evaluate.eval_results import ALL_TOPIC_ID, load


def measure_key(name: str):
    """``base__bank__scoring[__tN]`` -> ``(base, scoring[, tN])``; ``None`` when
    the name does not follow the bank-keyed convention."""
    parts = name.split("__")
    if len(parts) == 3:
        return (parts[0], parts[2])
    if len(parts) == 4:
        return (parts[0], parts[2], parts[3])
    return None


def _match_measure(measures, wanted: str) -> str:
    if wanted in measures:
        return wanted
    hits = [m for m in measures
            if measure_key(m) and "__".join(measure_key(m)) == wanted]
    if not hits:
        keys = sorted({"__".join(measure_key(m)) for m in measures
                       if measure_key(m)})
        raise ValueError(f"measure {wanted!r} not found; "
                         f"available bank-stripped keys: {', '.join(keys)}")
    if len(hits) > 1:
        raise ValueError(f"measure {wanted!r} is ambiguous across banks: "
                         f"{sorted(hits)}; pass a full measure name")
    return hits[0]


def load_eval_scores(path, measure: str, fmt: str = "ir_measures",
                     ) -> dict[str, dict[str, float]]:
    """Return ``{system: {topic: score}}`` for one measure from an eval file or
    directory. ``measure`` is the bank-stripped key such as
    ``AVG_GRADE__rubric``; a full measure name also works. Aggregate rows are
    dropped and non-numeric cells skipped."""
    # silent: align() handles incomplete coverage, and a library loader must
    # not print run-level warnings (a blind-protocol surfacing risk)
    result = load(Path(path), format=fmt, recompute_aggregates=False,
                  verify=False, on_missing="ignore")
    name = _match_measure(result.measures, measure)
    scores: dict[str, dict[str, float]] = {}
    for e in result.entries_by_measure(name):
        if e.topic_id == ALL_TOPIC_ID:
            continue
        try:
            scores.setdefault(e.run_id, {})[e.topic_id] = float(e.value)
        except (TypeError, ValueError):
            pass
    return scores
