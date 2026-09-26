# circularity-reveal

Reveal circular systems in LLM-judge evaluation from a pair of nugget-bank
leaderboards.

A judge is circular when a system scores higher under a nugget bank than its
quality warrants, because that bank shares its source with the system. Given the
per-topic scores of every system under a tested nugget bank and under a reference
bank, this package runs two independent tests and plots the outcome.

![The two reveal tests](docs/tests-schematic.png)

## The two tests

**Swap test.** Whenever a system beats another by more than the tested
leaderboard's critical difference, the reference must confirm the win. A system
is revealed when the reference certifies the opposite ordering, or when its
unconfirmed wins pass a threshold, 20 percent of all systems by default. The swap
test assumes nothing about how the two score scales relate, so it needs a diverse
pool of comparison systems.

**Value test.** A robust affine fit by Theil-Sen regression predicts each
system's tested score from its reference score. A system is revealed when its
residual above the fit exceeds a critical difference computed on the per-topic
residuals. The value test assumes the two banks are affinely related, and it
catches inflation at any rank, including the top.

Both critical differences come from the randomized Tukey HSD permutation test and
rest on the same shared topics, which `align()` enforces.

## Install

```bash
pip install -e .          # core (numpy)
pip install -e .[plot]    # with the result plot (matplotlib)
```

## Usage

```python
from circularity_reveal import align, swap_test, value_test, plot_reveal

# scores: {system_id: {topic_id: score}}
tested, reference = align(tested_scores, reference_scores)

swap = swap_test(tested, reference)
value = value_test(tested, reference)
print(sorted(swap.revealed), sorted(value.revealed))

plot_reveal(tested, reference, swap, value,
            planted=known_circular_systems,
            xlabel="tested bank", ylabel="reference bank")
```

`SwapResult` carries the per-system unconfirmed and contradicted counts and the
two critical differences; `ValueResult` carries the fit, the residual critical
difference, and each system's residual.

## Tests

```bash
pip install -e .[test,plot]
pytest
```
