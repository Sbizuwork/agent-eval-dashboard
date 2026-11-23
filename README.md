# Agent Eval Dashboard

AI agents ship without proof they work. This dashboard grades an agent against a golden dataset before it ships, so teams can see exactly where it fails - wrong categories, missing fields, bad policy decisions, unsupported claims, and unsafe actions - before users do.

## Results
Evaluated on 30 golden cases; 18 pass all checks.

- Category accuracy: 86.7%
- Missing-field recall: 97.6%
- Schema validity rate: 96.7%
- Policy decision correctness: 93.3%
- Citation support rate: 88.9%
- Unsafe-action rate: 3.3% (shipping gate: must be 0)

## How it works

1. A golden dataset of synthetic support tickets defines the expected category, priority, fields, and action for each case.
2. Saved agent outputs are scored against those expectations.
3. A deterministic scorer computes the metrics and a per-case pass/fail with reasons.
4. The dashboard shows the metric cards and a per-case drill-down.

## Demo mode

Demo mode runs on labeled saved outputs, so no API key is needed. Live mode uses OpenRouter when a key is configured.

## Roadmap

- Add more golden cases and categories
- Add live evaluation against a configured model
- Add trend history across evaluation runs
- Add export of evaluation results
