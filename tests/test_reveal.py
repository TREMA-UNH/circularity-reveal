import numpy as np

from circularity_reveal import (
    align,
    critical_difference,
    swap_test,
    theil_sen,
    value_test,
)


def board(means, n_topics=24, spread=0.4, seed=0):
    """Synthetic leaderboard: each system's topic scores scatter around its
    target mean, sharing one difficulty pattern across systems."""
    rng = np.random.default_rng(seed)
    difficulty = rng.normal(0, spread, n_topics)
    return {s: {f"t{k}": float(mu + difficulty[k] + rng.normal(0, 0.05))
                for k in range(n_topics)}
            for s, mu in means.items()}


def test_align_keeps_shared_systems_and_topics():
    a = {"s1": {"t1": 1.0, "t2": 2.0}, "s2": {"t1": 1.0, "t2": 2.0}}
    b = {"s2": {"t2": 1.0, "t3": 2.0}, "s3": {"t2": 1.0, "t3": 2.0}}
    ta, tb = align(a, b)
    assert ta.systems == ("s2",)
    assert ta.topics == ("t2",)  # graded on both boards
    assert ta.systems == tb.systems and ta.topics == tb.topics


def test_align_zero_fills_missing_topics():
    a = {"s1": {"t1": 3.0, "t2": 2.0}, "s2": {"t1": 1.0}}  # s2 omits t2
    b = {"s1": {"t1": 3.0, "t2": 2.0}, "s2": {"t1": 1.0, "t2": 0.5}}
    ta, tb = align(a, b)
    assert ta.systems == ("s1", "s2") and ta.topics == ("t1", "t2")
    i, j = ta.systems.index("s2"), ta.topics.index("t2")
    assert ta.values[i, j] == 0.0  # empty response scored 0, not dropped


def test_critical_difference_positive_and_deterministic():
    tested, _ = align(board({"a": 3, "b": 2, "c": 1}),
                      board({"a": 3, "b": 2, "c": 1}))
    assert critical_difference(tested) == critical_difference(tested) > 0


def test_theil_sen_recovers_a_line():
    x = np.arange(10.0)
    a, b = theil_sen(x, 2.0 + 3.0 * x)
    assert abs(a - 2.0) < 1e-9 and abs(b - 3.0) < 1e-9


def test_swap_reveals_a_contradicted_system():
    means = {"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0}
    reference = board(means, seed=1)
    swapped = dict(means)
    swapped["a"], swapped["d"] = means["d"], means["a"]  # flip top and bottom
    tested, ref = align(board(swapped, seed=1), reference)
    result = swap_test(tested, ref)
    assert "d" in result.revealed  # leads the tested bank, trails the reference
    assert result.contradicted["d"] >= 1


def test_swap_reveals_nothing_when_boards_agree():
    same = board({"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0, "e": 0.5}, seed=2)
    tested, ref = align(same, same)
    assert swap_test(tested, ref).revealed == frozenset()


def test_value_reveals_an_inflated_system():
    means = {f"s{i}": float(i) for i in range(6)}
    reference = board(means, seed=3)
    inflated = board(means, seed=3)
    for topic in inflated["s2"]:
        inflated["s2"][topic] += 3.0  # push s2 far above the affine fit
    tested, ref = align(inflated, reference)
    result = value_test(tested, ref)
    assert "s2" in result.revealed
    assert "s5" not in result.revealed
