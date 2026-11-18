import argparse
import json
import sys
from pathlib import Path

from .audit import audit_file, finding_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local static accessibility checks on HTML.")
    parser.add_argument("html", type=Path, help="HTML file to audit")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning", "none"), default="error",
                        help="Return 1 when findings at or above this threshold exist.")
    args = parser.parse_args(argv)
    try:
        findings = audit_file(args.html)
    except (OSError, UnicodeError) as exc:
        print(f"accessibility-pr-gate: {exc}", file=sys.stderr)
        return 2
    records = [finding_dict(item) for item in findings]
    if args.format == "json":
        print(json.dumps({"file": str(args.html), "findings": records, "count": len(records)}, indent=2))
    elif findings:
        for finding in findings:
            print(f"{args.html}:{finding.line}: {finding.severity.upper()} "
                  f"{finding.rule} (WCAG {finding.criterion}): {finding.message}")
        print(f"{len(findings)} finding(s)")
    else:
        print(f"No findings: {args.html}")
    levels = {"warning": 1, "error": 2, "none": 3}
    return int(any(levels[item.severity] >= levels[args.fail_on] for item in findings))


if __name__ == "__main__":
    raise SystemExit(main())
