# Accessibility PR Gate

A dependency-free, local static audit for common HTML accessibility issues. It reports source line, severity, a rule ID, and the related WCAG 2.2 success criterion.

## Install

Requires Python 3.11+.

```sh
python -m venv .venv
python -m pip install -e .
```

## Use

```sh
accessibility-pr-gate fixtures/sample.html
accessibility-pr-gate fixtures/sample.html --format json --fail-on warning
```

Exit codes: `0` means no finding met the selected threshold, `1` means the threshold was met, and `2` means input could not be read. `--fail-on error` is the default; `warning` also gates on warnings; `none` never gates.

Checks include missing `img` alt attributes, detectable names for links, buttons, and form controls, malformed explicit labels, a main landmark, distinguishable names for repeated navigation landmarks, and heading order/text. Empty `alt=""` is valid for decorative images. Findings are heuristics, not an accessibility conformance verdict.

Run tests with `python -m unittest discover -s tests`.
