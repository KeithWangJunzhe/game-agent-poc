from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from game_poc import GameEngine, GameState, Point, create_default_state, format_state
from match_report import MatchRecorder


MATCH_DIR = Path(__file__).resolve().parent / "matches"


def build_legal_options(engine: GameEngine, player_id: str) -> List[Dict[str, Any]]:
    return list(engine.state.legal_actions_for_player(player_id))


def _attack_priority(state: GameState, command: Dict[str, Any]) -> tuple[int, int]:
    target = state.units.get(command["target_id"])
    if target is None:
        return (0, 0)
    if target.kind == "base":
        return (3, 10 - target.hp)
    if target.kind == "worker":
        return (2, 10 - target.hp)
    return (1, 10 - target.hp)


def _distance_to_nearest_resource(state: GameState, position: Point) -> Optional[int]:
    distances = [
        position.distance_to(node.position)
        for node in state.resources.values()
        if node.amount > 0
    ]
    if not distances:
        return None
    return min(distances)


def _distance_to_enemy_base(state: GameState, player_id: str, position: Point) -> Optional[int]:
    enemy_bases = [
        unit.position
        for unit in state.units.values()
        if unit.owner_id != player_id and unit.kind == "base"
    ]
    if not enemy_bases:
        return None
    return min(position.distance_to(base_pos) for base_pos in enemy_bases)


def choose_baseline_command(engine: GameEngine, player_id: str) -> Dict[str, Any]:
    state = engine.state
    options = build_legal_options(engine, player_id)
    attack_options = [opt for opt in options if opt["type"] == "attack"]
    gather_options = [opt for opt in options if opt["type"] == "gather"]
    move_options = [opt for opt in options if opt["type"] == "move_unit"]
    non_base_moves = [
        opt for opt in move_options if state.units[opt["unit_id"]].kind != "base"
    ]

    if gather_options:
        return gather_options[0]

    if attack_options:
        ranked_attacks = sorted(
            attack_options,
            key=lambda opt: _attack_priority(state, opt),
            reverse=True,
        )
        return ranked_attacks[0]

    candidate_moves = non_base_moves or move_options
    if candidate_moves:
        best_option = candidate_moves[0]
        best_score = None
        for opt in candidate_moves:
            unit = state.units[opt["unit_id"]]
            next_position = unit.position.step(opt["direction"])
            score = 0
            if unit.kind == "worker":
                resource_distance = _distance_to_nearest_resource(state, next_position)
                if resource_distance is not None:
                    score -= resource_distance * 10
                enemy_base_distance = _distance_to_enemy_base(state, player_id, next_position)
                if enemy_base_distance is not None:
                    score -= enemy_base_distance * 2
            elif unit.kind == "warrior":
                enemy_base_distance = _distance_to_enemy_base(state, player_id, next_position)
                if enemy_base_distance is not None:
                    score -= enemy_base_distance * 8
            else:
                enemy_base_distance = _distance_to_enemy_base(state, player_id, next_position)
                if enemy_base_distance is not None:
                    score -= enemy_base_distance * 2

            if best_score is None or score > best_score:
                best_score = score
                best_option = opt
        return best_option

    return {"type": "end_turn"}


def load_state_from_json(text: str) -> GameState:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("state json must be an object")
    return GameState.from_dict(payload)


def run_demo(max_turns: int = 12) -> None:
    engine = GameEngine(create_default_state())
    recorder = MatchRecorder(mode="baseline", initial_state=engine.state.clone())
    print("=== Baseline Demo ===")
    print(format_state(engine.state))
    print()

    for _ in range(max_turns):
        if engine.state.winner_id is not None:
            break
        player_id = engine.state.current_player_id
        command = choose_baseline_command(engine, player_id)
        result = engine.apply(command)
        recorder.record_step(
            command,
            {
                "ok": result.ok,
                "message": result.message,
                "state_changed": result.state_changed,
                "source": "baseline",
            },
            engine.state,
        )
        print(f"> baseline command={json.dumps(command, ensure_ascii=False)}")
        print(f"  result={result.ok} | {result.message}")
        print(format_state(engine.state))
        print()

    report_path = recorder.write_report(engine.state, MATCH_DIR)
    report = recorder.build_report(engine.state)
    print("=== After Match ===")
    print(f"report: {report_path}")
    print("stats: " + json.dumps(report["stats"], ensure_ascii=False, sort_keys=True))


def run_once(state_json: Optional[str]) -> None:
    if state_json is None:
        state = create_default_state()
    else:
        state = load_state_from_json(state_json)
    engine = GameEngine(state)
    command = choose_baseline_command(engine, engine.state.current_player_id)
    print(json.dumps(command, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Baseline bot for the game POC")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run a self-play baseline demo",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=12,
        help="maximum number of turns for demo mode",
    )
    parser.add_argument(
        "--state-json",
        help="optional inline JSON game state; prints one command for that state",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.demo:
        run_demo(args.max_turns)
        return
    run_once(args.state_json)


if __name__ == "__main__":
    main()
