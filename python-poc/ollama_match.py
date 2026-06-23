from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from agent_io import parse_agent_response
from game_poc import GameEngine, create_default_state, format_state
from match_report import MatchRecorder
from baseline_bot import choose_baseline_command as baseline_choose_command
from ollama_support import format_ollama_diagnostics, run_ollama


DEFAULT_MODEL = "gemma4:e2b"
MATCH_DIR = Path(__file__).resolve().parent / "matches"


def build_legal_options(engine: GameEngine, player_id: str) -> List[Dict[str, Any]]:
    return list(engine.state.legal_actions_for_player(player_id))


def choose_baseline_command(engine: GameEngine, player_id: str) -> Dict[str, Any]:
    return baseline_choose_command(engine, player_id)


def build_prompt(
    state_text: str,
    controlled_player_id: str,
    current_player_id: str,
    options: List[Dict[str, Any]],
) -> str:
    return (
        "You are controlling a simple turn-based game.\n"
        f"You control player: {controlled_player_id}\n"
        f"Current player: {current_player_id}\n"
        "Return exactly one JSON object and nothing else.\n"
        "Return a JSON object with keys `command` and `decision_note`.\n"
        "The `command` value must be one command from the allowed options.\n"
        "The `decision_note` value should be a short reason for the choice.\n\n"
        "Current state:\n"
        f"{state_text}\n\n"
        "Allowed options:\n"
        f"{json.dumps(options, ensure_ascii=False, indent=2)}\n"
    )


def build_match_state() -> tuple[Any, Dict[str, Any]]:
    model_player_id = random.choice(["p1", "p2"])
    baseline_player_id = "p2" if model_player_id == "p1" else "p1"
    state = create_default_state()
    state.current_player_id = random.choice(["p1", "p2"])
    return state, {
        "model_player_id": model_player_id,
        "baseline_player_id": baseline_player_id,
        "starting_player_id": state.current_player_id,
    }


def query_model(model: str, prompt: str) -> str:
    completed = run_ollama(model, prompt)
    if completed.returncode != 0:
        raise RuntimeError(
            f"ollama failed with exit code {completed.returncode}: {completed.stderr.strip()} | "
            f"{format_ollama_diagnostics()}"
        )
    return completed.stdout.strip()


def run_match(model: str, max_turns: int, debug: bool = False) -> None:
    initial_state, match_config = build_match_state()
    engine = GameEngine(initial_state.clone())
    model_player_id = match_config["model_player_id"]
    baseline_player_id = match_config["baseline_player_id"]
    recorder = MatchRecorder(
        mode=f"ollama:{model}",
        initial_state=initial_state.clone(),
        metadata=match_config,
    )

    print(f"=== Ollama Match: {model} vs baseline ===")
    print(
        "match config: "
        + json.dumps(match_config, ensure_ascii=False, sort_keys=True)
    )
    if debug:
        print(format_ollama_diagnostics())
    print(format_state(engine.state))
    print()

    for _ in range(max_turns):
        if engine.state.winner_id is not None:
            break

        current_player = engine.state.current_player_id
        trace_prompt = None
        if current_player == model_player_id:
            options = build_legal_options(engine, current_player)
            observation = json.dumps(
                engine.state.to_agent_observation(model_player_id),
                ensure_ascii=False,
                indent=2,
            )
            prompt = build_prompt(
                observation,
                model_player_id,
                current_player,
                options,
            )
            trace_prompt = prompt
            if debug:
                print("=== Agent Prompt ===")
                print(prompt)
            try:
                raw_output = query_model(model, prompt)
            except Exception as exc:
                command = {"type": "end_turn"}
                raw_output = ""
                decision_note = f"fallback=end_turn; error={exc}"
                parse_note = "ollama_error"
                print(f"> model error: {exc}")
            else:
                command, decision_note, parse_note = parse_agent_response(raw_output, options)
                if command is None:
                    command = {"type": "end_turn"}
                    decision_note = decision_note or "fallback=end_turn"
                    parse_note = f"fallback:{parse_note}"
                elif not decision_note:
                    decision_note = "no decision_note provided"
            source = "ollama"
        else:
            command = choose_baseline_command(engine, current_player)
            raw_output = json.dumps(command, ensure_ascii=False)
            decision_note = "baseline"
            parse_note = "baseline"
            source = "baseline"

        result = engine.apply(command)
        recorder.record_step(
            command,
            {
                "ok": result.ok,
                "message": result.message,
                "state_changed": result.state_changed,
                "source": source,
                "decision_note": decision_note,
                "prompt": trace_prompt,
                "raw_output": raw_output,
                "parse_note": parse_note,
            },
            engine.state,
        )
        print(f"> {source} command={json.dumps(command, ensure_ascii=False)}")
        if current_player == model_player_id:
            print(f"  decision_note={decision_note}")
            if debug and raw_output:
                print(f"  raw_output={raw_output}")
        print(f"  result={result.ok} | {result.message}")
        print(format_state(engine.state))
        print()

    report_path = recorder.write_report(engine.state, MATCH_DIR)
    report = recorder.build_report(engine.state)
    print("=== After Match ===")
    print(f"report: {report_path}")
    print("stats: " + json.dumps(report["stats"], ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an Ollama vs baseline match")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"ollama model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="maximum number of turns to simulate",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print extra diagnostics before the match starts",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    run_match(args.model, args.max_turns, debug=args.debug)


if __name__ == "__main__":
    main()
