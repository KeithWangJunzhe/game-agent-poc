from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_tools import load_report, summarize_report


def _print_human(summary: dict[str, object]) -> None:
    print(f"report: {summary.get('source_path')}")
    print(f"mode: {summary.get('mode')}")
    match_config = summary.get("match_config") or {}
    if match_config:
        print(f"match_config: {json.dumps(match_config, ensure_ascii=False)}")
    print(
        "result: "
        f"winner={summary.get('winner_id')} "
        f"reason={summary.get('winner_reason')} "
        f"commands={summary.get('total_commands')} "
        f"valid={summary.get('valid_commands')} "
        f"invalid={summary.get('invalid_commands')}"
    )
    print(
        "flow: "
        f"fallbacks={summary.get('fallback_count')} "
        f"state_changes={summary.get('state_changes')} "
        f"turns_elapsed={summary.get('turns_elapsed')} "
        f"trajectory_entries={summary.get('trajectory_entries')}"
    )
    print(f"events_recorded: {summary.get('events_recorded')}")
    print(f"action_counts: {json.dumps(summary.get('action_counts', {}), ensure_ascii=False)}")
    print(f"source_counts: {json.dumps(summary.get('source_counts', {}), ensure_ascii=False)}")
    print(f"resources_by_player: {json.dumps(summary.get('resources_by_player', {}), ensure_ascii=False)}")
    print(f"units_by_player: {json.dumps(summary.get('units_by_player', {}), ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a minimal summary for one match report.")
    parser.add_argument("report", type=Path, help="Path to a match report JSON file.")
    parser.add_argument("--json", action="store_true", help="Print the summary as JSON.")
    args = parser.parse_args()

    try:
        report = load_report(args.report)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    summary = summarize_report(report, args.report)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_human(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
