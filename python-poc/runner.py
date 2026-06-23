from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Sequence

from game_poc import GameEngine, create_default_state, demo_commands, format_state
from match_report import MatchRecorder


MATCH_DIR = Path(__file__).resolve().parent / "matches"


def build_match_state(randomize_first_player: bool = True):
    state = create_default_state()
    if randomize_first_player:
        state.current_player_id = random.choice(["p1", "p2"])
    return state, {
        "starting_player_id": state.current_player_id,
    }


def run_demo() -> None:
    initial_state = create_default_state()
    engine = GameEngine(initial_state.clone())
    recorder = MatchRecorder(mode="demo", initial_state=initial_state.clone())
    print("=== Game Agent POC Demo ===")
    print(format_state(engine.state))
    print()

    for command in demo_commands():
        result = engine.apply(command)
        recorder.record_step(
            command,
            {
                "ok": result.ok,
                "message": result.message,
                "state_changed": result.state_changed,
            },
            engine.state,
        )
        print(f"> command={json.dumps(command, ensure_ascii=False)}")
        print(f"  result={result.ok} | {result.message}")
        print(format_state(engine.state))
        print()

    report_path = recorder.write_report(engine.state, MATCH_DIR)
    report = recorder.build_report(engine.state)
    print("=== After Match ===")
    print(f"report: {report_path}")
    print(
        "stats: "
        + json.dumps(report["stats"], ensure_ascii=False, sort_keys=True)
    )


def run_interactive() -> None:
    run_interactive_limited(30)


def run_interactive_limited(max_turns: int) -> None:
    initial_state, match_config = build_match_state()
    engine = GameEngine(initial_state.clone())
    recorder = MatchRecorder(
        mode="interactive",
        initial_state=initial_state.clone(),
        metadata=match_config,
    )
    print("=== Game Agent POC Interactive ===")
    print(
        "match config: "
        + json.dumps(match_config, ensure_ascii=False, sort_keys=True)
    )
    print(f"turn_limit: {max_turns}")
    print("输入 JSON 命令，或输入 'status' / 'quit'")
    print(format_state(engine.state))

    start_turn = engine.state.turn
    while engine.state.turn - start_turn < max_turns and engine.state.winner_id is None:
        raw = input("\n> ").strip()
        if not raw:
            continue
        if raw in {"quit", "exit"}:
            break
        if raw == "status":
            print(format_state(engine.state))
            continue

        try:
            command = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"invalid json: {exc}")
            recorder.record_step(
                {"raw": raw},
                {"ok": False, "message": f"invalid json: {exc}", "state_changed": False},
                engine.state,
            )
            continue

        result = engine.apply(command)
        recorder.record_step(
            command,
            {
                "ok": result.ok,
                "message": result.message,
                "state_changed": result.state_changed,
            },
            engine.state,
        )
        print(f"{result.ok} | {result.message}")
        print(format_state(engine.state))

    if engine.state.winner_id is None and engine.state.turn - start_turn >= max_turns:
        print(f"turn limit reached: {max_turns}")

    report_path = recorder.write_report(engine.state, MATCH_DIR)
    report = recorder.build_report(engine.state)
    print("=== After Match ===")
    print(f"report: {report_path}")
    print(
        "stats: "
        + json.dumps(report["stats"], ensure_ascii=False, sort_keys=True)
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Game Agent POC runner")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="run an interactive JSON command loop",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run the scripted demo",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="maximum turns for interactive mode",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.interactive:
        run_interactive_limited(args.max_turns)
    else:
        run_demo()


if __name__ == "__main__":
    main()
