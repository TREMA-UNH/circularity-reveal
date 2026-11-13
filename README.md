# circularity-reveal

Reveal circular systems in LLM-judge evaluation from a pair of nugget-bank
leaderboards.

A judge is circular when a system scores higher under a nugget bank than its
quality warrants, because that bank shares its source with the system. Given the
per-topic scores of every system under a tested nugget bank and under a reference
bank, this package runs two independent tests and plots the outcome.

![The two reveal tests](https://raw.githubusercontent.com/TREMA-UNH/circularity-reveal/master/docs/tests-schematic.png)

## The two tests

**Swap test.** Whenever a system beats another by more than the tested
leaderboard's critical difference, the reference must confirm the win. A system
is revealed when the reference certifies the opposite ordering, or when its
unconfirmed wins pass a threshold, 20 percent of all systems by default. The swap
test makes no assumption about how the two score scales relate, so it needs a diverse
pool of comparison systems.

**Value test.** A robust affine fit by Theil-Sen regression on the system
means predicts each system's tested score from its reference score. A system
is revealed when its mean residual above that fit exceeds a critical
difference calibrated on residuals around Theil-Sen lines fit within each
topic, so the margin reflects topic-to-topic scatter rather than the single
slope's lack of fit. The value test assumes the two banks are affinely
related, and it catches inflation at any rank, including the top.

Both critical differences come from the randomized Tukey HSD permutation test and
rest on the same shared topics, which `align()` enforces.

## Install

```bash
pip install circularity-reveal              # core (numpy)
pip install "circularity-reveal[plot]"      # with the result plot (matplotlib)
pip install "circularity-reveal[autojudge]" # with the CLI's auto-judge eval-file reader
```

The source is at <https://github.com/TREMA-UNH/circularity-reveal>. For a development
install, clone it and run `pip install -e ".[test,plot]"`.

## License

MIT, see `LICENSE`.

## As a library

A dependent package holds its scores in memory as `{system: {topic: score}}` per
bank and runs both tests in one call:

```python
from circularity_reveal import reveal

result = reveal(tested_scores, reference_scores)   # aligns and runs both tests
result.revealed                 # frozenset of systems revealed by either test
result.swap.revealed            # swap test alone; d_tested, d_reference, counts
result.value.revealed           # value test alone; slope, intercept, d_residual
```

The pieces are also available on their own, on aligned `ScoreMatrix` pairs:

```python
from circularity_reveal import align, swap_test, value_test, plot_reveal

tested, reference = align(tested_scores, reference_scores)
swap = swap_test(tested, reference)
value = value_test(tested, reference)
plot_reveal(tested, reference, swap, value,
            planted=known_circular_systems,
            xlabel="tested bank", ylabel="reference bank")
```

`SwapResult` carries the per-system unconfirmed and contradicted counts and the
two critical differences. `ValueResult` carries the fit, the residual critical
difference, and each system's residual.

## Command line

With the `[autojudge]` extra the CLI reads auto-judge ir_measures eval files
directly, selecting one bank-stripped measure key:

```bash
circularity-reveal \
  --tested    ours/judge/both.eval.txt \
  --reference pool/judge/both.eval.txt \
  --measure   AVG_GRADE__rubric \
  --plot reveal.png --json reveal.json
```

It prints the systems revealed by each test and the critical differences.
`--alpha`, `--theta`, `--perm`, and `--seed` tune the tests. `--format` selects a
different eval file format.

## Tests

```bash
pip install -e .[test,plot]
pytest
```
