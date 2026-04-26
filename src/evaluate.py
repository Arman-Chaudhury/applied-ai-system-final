"""
CLI entry point for the evaluation harness.

Usage:
    python -m src.evaluate

Exits with code 1 if any case fails so this can be wired into CI later.
"""

import logging
import sys

from src.evaluator import run_eval, format_report


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    report = run_eval()
    print(format_report(report))
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
