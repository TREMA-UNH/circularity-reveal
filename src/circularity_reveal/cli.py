"""Command-line interface for the circularity reveal tests."""
from __future__ import annotations

import argparse
import json
import sys

from .reveal import reveal


def _load(path, measure, fmt):
    try:
        from .eval_txt import load_eval_scores
    except ImportError:
        sys.exit("reading eval files needs the autojudge extra: "
                 "pip install circularity-reveal[autojudge]")
    return load_eval_scores(path, measure, fmt)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(
        prog="circularity-reveal",
        description="Reveal circular systems from a tested and a reference "
                    "nugget-bank leaderboard.")
    ap.add_argument("--tested", required=True,
                    help="eval file or directory for the tested nugget bank")
    ap.add_argument("--reference", required=True,
                    help="eval file or directory for the reference nugget bank")
    ap.add_argument("--measure", required=True,
                    help="bank-stripped measure key, e.g. AVG_GRADE__rubric")
    ap.add_argument("--format", default="ir_measures",
                    help="eval file format (default: ir_measures)")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta", type=float, default=0.20,
                    help="swap-test unconfirmed-win threshold as a fraction of "
                         "the systems (default: 0.20)")
    ap.add_argument("--perm", type=int, default=10_000,
                    help="permutations for the critical difference")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--plot", help="write the result plot to this path")
    ap.add_argument("--json", dest="json_out",
                    help="write the full result as JSON to this path")
    args = ap.parse_args(argv)

    try:
        tested = _load(args.tested, args.measure, args.format)
        reference = _load(args.reference, args.measure, args.format)
        result = reveal(tested, reference, alpha=args.alpha,
                        theta_frac=args.theta, n_perm=args.perm, seed=args.seed)
    except ValueError as exc:
        sys.exit(f"error: {exc}")

    both = sorted(result.swap.revealed & result.value.revealed)
    swap_only = sorted(result.swap.revealed - result.value.revealed)
    value_only = sorted(result.value.revealed - result.swap.revealed)
    print(f"systems: {len(result.tested.systems)}  "
          f"topics: {len(result.tested.topics)}")
    print(f"d*_tested={result.swap.d_tested:.3f}  "
          f"d*_reference={result.swap.d_reference:.3f}  "
          f"d*_residual={result.value.d_residual:.3f}")
    print(f"fit: tested = {result.value.intercept:.3f} + "
          f"{result.value.slope:.3f} * reference")
    print(f"revealed by both tests ({len(both)}): {both}")
    print(f"revealed by swap test only ({len(swap_only)}): {swap_only}")
    print(f"revealed by value test only ({len(value_only)}): {value_only}")

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            from .plot import plot_reveal
        except ImportError:
            sys.exit("plotting needs the plot extra: "
                     "pip install circularity-reveal[plot]")
        ax = plot_reveal(result.tested, result.reference, result.swap,
                         result.value)
        ax.figure.savefig(args.plot, bbox_inches="tight", dpi=180)
        print(f"wrote {args.plot}")

    if args.json_out:
        payload = {
            "systems": list(result.tested.systems),
            "topics": list(result.tested.topics),
            "d_tested": result.swap.d_tested,
            "d_reference": result.swap.d_reference,
            "d_residual": result.value.d_residual,
            "slope": result.value.slope,
            "intercept": result.value.intercept,
            "swap_revealed": sorted(result.swap.revealed),
            "value_revealed": sorted(result.value.revealed),
            "unconfirmed": result.swap.unconfirmed,
            "contradicted": result.swap.contradicted,
            "residual": result.value.residual,
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
