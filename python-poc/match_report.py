from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List

from game_poc import GameState


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_units_by_owner(state: GameState) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for unit in state.units.values():
        counts[unit.owner_id] = counts.get(unit.owner_id, 0) + 1
    return counts


def _sum_resources_by_owner(state: GameState) -> Dict[str, int]:
    return {player_id: player.resources for player_id, player in state.players.items()}


def _winner_reason(state: GameState) -> str:
    for event in reversed(state.event_log):
        if "wins by reaching 10 gold" in event:
            return "gold"
        if "wins by destroying the enemy base" in event:
            return "base"
    return "none"


@dataclass
class MatchRecorder:
    mode: str
    initial_state: GameState
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=_utc_now_iso)
    command_log: List[Dict[str, Any]] = field(default_factory=list)

    def record_step(self, command: Dict[str, Any], result: Dict[str, Any], state: GameState) -> None:
        self.command_log.append(
            {
                "turn": state.turn,
                "current_player_id": state.current_player_id,
                "command": command,
                "result": result,
            }
        )

    def build_report(self, final_state: GameState) -> Dict[str, Any]:
        action_counts: Dict[str, int] = {}
        valid_commands = 0
        invalid_commands = 0
        state_changes = 0
        fallback_count = 0
        source_counts: Dict[str, int] = {}

        for entry in self.command_log:
            command_type = str(entry["command"].get("type", "unknown"))
            action_counts[command_type] = action_counts.get(command_type, 0) + 1
            if entry["result"]["ok"]:
                valid_commands += 1
            else:
                invalid_commands += 1
            if entry["result"]["state_changed"]:
                state_changes += 1
            source = str(entry["result"].get("source", "unknown"))
            source_counts[source] = source_counts.get(source, 0) + 1
            if entry["result"].get("fallback_used"):
                fallback_count += 1

        return {
            "mode": self.mode,
            "match_config": dict(self.metadata),
            "started_at": self.started_at,
            "finished_at": _utc_now_iso(),
            "initial_state": self.initial_state.to_dict(),
            "final_state": final_state.to_dict(),
            "commands": list(self.command_log),
            "trajectory": list(self.command_log),
            "stats": {
                "total_commands": len(self.command_log),
                "valid_commands": valid_commands,
                "invalid_commands": invalid_commands,
                "state_changes": state_changes,
                "fallback_count": fallback_count,
                "action_counts": action_counts,
                "source_counts": source_counts,
                "turns_elapsed": max(final_state.turn - self.initial_state.turn, 0),
                "winner_id": final_state.winner_id,
                "winner_reason": _winner_reason(final_state),
                "resources_by_player": _sum_resources_by_owner(final_state),
                "units_by_player": _count_units_by_owner(final_state),
                "events_recorded": len(final_state.event_log),
            },
        }

    def write_report(self, final_state: GameState, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.build_report(final_state)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = output_dir / f"match-{stamp}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
