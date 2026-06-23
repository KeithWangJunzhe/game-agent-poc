from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_tools import load_report


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, str) else 0


def _shorten(value: Any, limit: int = 240) -> str:
    if not isinstance(value, str):
        return ""
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _iter_agent_entries(report: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for index, entry in enumerate(report.get("commands", []), start=1):
        result = entry.get("result", {})
        yield {
            "index": index,
            "turn": entry.get("turn"),
            "current_player_id": entry.get("current_player_id"),
            "source": result.get("source"),
            "command": entry.get("command"),
            "decision_note": result.get("decision_note"),
            "note": result.get("note"),
            "fallback_used": result.get("fallback_used", False),
            "prompt": result.get("prompt"),
            "raw_output": result.get("raw_output"),
            "repair_prompt": result.get("repair_prompt"),
            "repair_output": result.get("repair_output"),
            "parse_note": result.get("parse_note"),
        }


def _classify_intent(entry: Dict[str, Any]) -> str:
    command = entry.get("command") or {}
    decision_note = str(entry.get("decision_note") or "").lower()
    note = str(entry.get("note") or "").lower()
    raw_blob = " ".join(
        [
            decision_note,
            note,
            json.dumps(command, ensure_ascii=False).lower(),
            str(entry.get("raw_output") or "").lower(),
            str(entry.get("repair_output") or "").lower(),
        ]
    )
    if entry.get("fallback_used"):
        return "fallback"
    if "gather" in raw_blob or "resource" in raw_blob or "gold" in raw_blob:
        return "resource"
    if "attack" in raw_blob or "destroy" in raw_blob or "worker" in raw_blob:
        return "attack_worker"
    if "base" in raw_blob or "defend" in raw_blob or "guard" in raw_blob:
        return "defend_base"
    if "move" in raw_blob:
        return "move_other"
    return "other"


def _summarize(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        "fallback": 0,
        "resource": 0,
        "attack_worker": 0,
        "defend_base": 0,
        "move_other": 0,
        "other": 0,
    }
    for entry in entries:
        counts[_classify_intent(entry)] += 1
    return counts


def _print_entry(entry: Dict[str, Any], full: bool) -> None:
    print(
        f"#{entry['index']:02d} turn={entry['turn']} "
        f"player={entry['current_player_id']} source={entry['source']} "
        f"fallback={entry['fallback_used']}"
    )
    print(f"  command={json.dumps(entry['command'], ensure_ascii=False)}")
    print(f"  decision_note={entry.get('decision_note') or ''}")
    print(f"  note={entry.get('note') or ''}")
    print(f"  parse_note={entry.get('parse_note') or ''}")
    print(
        f"  prompt_len={_safe_len(entry.get('prompt'))} "
        f"raw_len={_safe_len(entry.get('raw_output'))} "
        f"repair_prompt_len={_safe_len(entry.get('repair_prompt'))} "
        f"repair_raw_len={_safe_len(entry.get('repair_output'))}"
    )
    if full:
        if entry.get("prompt"):
            print("  prompt:")
            print(entry["prompt"])
        if entry.get("raw_output"):
            print("  raw_output:")
            print(entry["raw_output"])
        if entry.get("repair_prompt"):
            print("  repair_prompt:")
            print(entry["repair_prompt"])
        if entry.get("repair_output"):
            print("  repair_output:")
            print(entry["repair_output"])
    else:
        if entry.get("prompt"):
            print(f"  prompt_preview={_shorten(entry.get('prompt'))}")
        if entry.get("raw_output"):
            print(f"  raw_preview={_shorten(entry.get('raw_output'))}")
        if entry.get("repair_prompt"):
            print(f"  repair_prompt_preview={_shorten(entry.get('repair_prompt'))}")
        if entry.get("repair_output"):
            print(f"  repair_raw_preview={_shorten(entry.get('repair_output'))}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect per-turn debug traces from a match report.")
    parser.add_argument("report", type=Path, help="Path to a match report JSON file.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Print full prompt/output text instead of short previews.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the extracted trace entries as JSON.",
    )
    args = parser.parse_args()

    report = load_report(args.report)
    entries = list(_iter_agent_entries(report))

    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0

    print(f"report: {args.report}")
    print(f"mode: {report.get('mode')}")
    print(f"commands: {len(entries)}")
    print(f"winner: {report.get('stats', {}).get('winner_id')}")
    print(f"intent_summary: {json.dumps(_summarize(entries), ensure_ascii=False)}")
    print()
    for entry in entries:
        _print_entry(entry, args.full)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
