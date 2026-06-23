from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence
import json


def load_report(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"report not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"report is not valid JSON: {path}") from exc


def collect_report_paths(inputs: Sequence[str]) -> List[Path]:
    paths: List[Path] = []
    seen: set[Path] = set()

    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            candidates = sorted(path.rglob("*.json"))
        else:
            candidates = [path]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(candidate)

    return paths


def _stats_for_report(report: Dict[str, Any]) -> Dict[str, Any]:
    stats = dict(report.get("stats", {}))
    commands = list(report.get("commands", []))
    trajectory = list(report.get("trajectory", []))
    stats.setdefault("total_commands", len(commands))
    stats.setdefault("trajectory_entries", len(trajectory))
    return stats


def summarize_report(report: Dict[str, Any], source_path: Path | None = None) -> Dict[str, Any]:
    stats = _stats_for_report(report)
    match_config = dict(report.get("match_config", {}))
    return {
        "source_path": str(source_path) if source_path else None,
        "mode": report.get("mode"),
        "match_config": match_config,
        "started_at": report.get("started_at"),
        "finished_at": report.get("finished_at"),
        "winner_id": stats.get("winner_id"),
        "winner_reason": stats.get("winner_reason"),
        "total_commands": stats.get("total_commands", 0),
        "valid_commands": stats.get("valid_commands", 0),
        "invalid_commands": stats.get("invalid_commands", 0),
        "fallback_count": stats.get("fallback_count", 0),
        "state_changes": stats.get("state_changes", 0),
        "turns_elapsed": stats.get("turns_elapsed", 0),
        "trajectory_entries": stats.get("trajectory_entries", 0),
        "events_recorded": stats.get("events_recorded", 0),
        "action_counts": dict(stats.get("action_counts", {})),
        "source_counts": dict(stats.get("source_counts", {})),
        "resources_by_player": dict(stats.get("resources_by_player", {})),
        "units_by_player": dict(stats.get("units_by_player", {})),
    }


def aggregate_summaries(summaries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    summary_list = list(summaries)
    matches = len(summary_list)
    winner_counts: Counter[str] = Counter()
    winner_reason_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    total_commands = 0
    total_valid = 0
    total_invalid = 0
    total_fallbacks = 0
    total_state_changes = 0
    total_events = 0
    total_turns = 0
    total_trajectory_entries = 0

    for summary in summary_list:
        if summary.get("winner_id"):
            winner_counts[str(summary["winner_id"])] += 1
        if summary.get("winner_reason"):
            winner_reason_counts[str(summary["winner_reason"])] += 1
        if summary.get("mode"):
            mode_counts[str(summary["mode"])] += 1
        match_config = summary.get("match_config") or {}
        provider = match_config.get("provider")
        if provider:
            provider_counts[str(provider)] += 1

        total_commands += int(summary.get("total_commands", 0))
        total_valid += int(summary.get("valid_commands", 0))
        total_invalid += int(summary.get("invalid_commands", 0))
        total_fallbacks += int(summary.get("fallback_count", 0))
        total_state_changes += int(summary.get("state_changes", 0))
        total_events += int(summary.get("events_recorded", 0))
        total_turns += int(summary.get("turns_elapsed", 0))
        total_trajectory_entries += int(summary.get("trajectory_entries", 0))

        for action, count in (summary.get("action_counts") or {}).items():
            action_counts[str(action)] += int(count)
        for source, count in (summary.get("source_counts") or {}).items():
            source_counts[str(source)] += int(count)

    return {
        "matches": matches,
        "winner_counts": dict(winner_counts),
        "winner_reason_counts": dict(winner_reason_counts),
        "mode_counts": dict(mode_counts),
        "provider_counts": dict(provider_counts),
        "total_commands": total_commands,
        "total_valid_commands": total_valid,
        "total_invalid_commands": total_invalid,
        "total_fallbacks": total_fallbacks,
        "total_state_changes": total_state_changes,
        "total_events_recorded": total_events,
        "total_turns_elapsed": total_turns,
        "total_trajectory_entries": total_trajectory_entries,
        "average_commands_per_match": round(total_commands / matches, 2) if matches else 0.0,
        "average_events_per_match": round(total_events / matches, 2) if matches else 0.0,
        "action_counts": dict(action_counts),
        "source_counts": dict(source_counts),
    }
