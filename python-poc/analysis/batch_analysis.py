from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_tools import aggregate_summaries, collect_report_paths, load_report, summarize_report


def _print_human(summary: dict[str, object]) -> None:
    print(f"matches: {summary.get('matches')}")
    print(f"winner_counts: {json.dumps(summary.get('winner_counts', {}), ensure_ascii=False)}")
    print(f"winner_reason_counts: {json.dumps(summary.get('winner_reason_counts', {}), ensure_ascii=False)}")
    print(f"provider_counts: {json.dumps(summary.get('provider_counts', {}), ensure_ascii=False)}")
    print(
        "totals: "
        f"commands={summary.get('total_commands')} "
        f"valid={summary.get('total_valid_commands')} "
        f"invalid={summary.get('total_invalid_commands')} "
        f"fallbacks={summary.get('total_fallbacks')} "
        f"state_changes={summary.get('total_state_changes')}"
    )
    print(
        "averages: "
        f"commands_per_match={summary.get('average_commands_per_match')} "
        f"events_per_match={summary.get('average_events_per_match')}"
    )
    print(f"action_counts: {json.dumps(summary.get('action_counts', {}), ensure_ascii=False)}")
    print(f"source_counts: {json.dumps(summary.get('source_counts', {}), ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate minimal stats from match report JSON files.")
    parser.add_argument(
        "inputs",
        nargs="+",
        help="One or more report files or directories containing reports.",
    )
    parser.add_argument("--json", action="store_true", help="Print the aggregate summary as JSON.")
    args = parser.parse_args()

    report_paths = collect_report_paths(args.inputs)
    summaries = []
    for path in report_paths:
        try:
            report = load_report(path)
        except (FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))
        summaries.append(summarize_report(report, path))
    aggregate = aggregate_summaries(summaries)
    aggregate["report_count"] = len(report_paths)
    aggregate["reports"] = [str(path) for path in report_paths]

    if args.json:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    else:
        _print_human(aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
