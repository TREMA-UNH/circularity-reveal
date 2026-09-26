"""Aligned per-topic score matrices for the reveal tests."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ScoreMatrix:
    """Per-topic evaluation scores of several systems on one leaderboard.

    ``values[i, j]`` is the score of ``systems[i]`` on ``topics[j]``.
    """

    systems: tuple[str, ...]
    topics: tuple[str, ...]
    values: np.ndarray

    @classmethod
    def from_scores(cls, scores: dict[str, dict[str, float]]) -> "ScoreMatrix":
        """Build from ``{system: {topic: score}}`` over the union of topics. A
        topic missing for a system is filled with ``0.0``, the customary score
        for an empty response, so no system or topic is dropped."""
        topics = sorted({t for tv in scores.values() for t in tv})
        systems = sorted(scores)
        values = np.array([[scores[s].get(t, 0.0) for t in topics]
                           for s in systems], dtype=float)
        return cls(tuple(systems), tuple(topics), values)

    def means(self) -> dict[str, float]:
        """Mean score per system over topics."""
        return {s: float(v)
                for s, v in zip(self.systems, self.values.mean(axis=1))}


def align(tested: dict[str, dict[str, float]],
          reference: dict[str, dict[str, float]],
          ) -> tuple[ScoreMatrix, ScoreMatrix]:
    """Restrict two leaderboards to their shared systems and to the topics
    graded on both boards, so the two critical differences rest on one common
    complete block. A topic missing for an individual system is filled with
    ``0.0``, the customary score for an empty response, rather than dropped.
    Returns ``(tested, reference)`` matrices with identical ``systems`` and
    ``topics``."""
    systems = sorted(set(tested) & set(reference))
    if not systems:
        raise ValueError("no systems shared between the two leaderboards")
    tested_topics = {t for tv in tested.values() for t in tv}
    reference_topics = {t for tv in reference.values() for t in tv}
    topics = sorted(tested_topics & reference_topics)
    if not topics:
        raise ValueError("no topics graded on both leaderboards")

    def matrix(scores: dict[str, dict[str, float]]) -> ScoreMatrix:
        values = np.array([[scores[s].get(t, 0.0) for t in topics]
                           for s in systems], dtype=float)
        return ScoreMatrix(tuple(systems), tuple(topics), values)

    return matrix(tested), matrix(reference)
