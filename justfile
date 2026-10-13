set shell := ["bash", "-euo", "pipefail", "-c"]

check: test

test:
    python3 -m unittest discover -s tests -v

benchmark:
    python3 scripts/benchmark_budget.py --samples 3 --output docs/benchmark.json
