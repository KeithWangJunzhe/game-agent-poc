from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple

from baseline_bot import choose_baseline_command
from agent_io import extract_json_object, parse_agent_response
from game_poc import GameEngine, GameState, create_default_state, format_state
from match_report import MatchRecorder
from ollama_support import format_ollama_diagnostics, run_ollama


MATCH_DIR = Path(__file__).resolve().parent / "matches"
TextResponder = Callable[[str, GameState, str], str]


class AgentExit(Exception):
    pass


class PromptProvider(Protocol):
    def __call__(self, prompt: str) -> str: ...


@dataclass
class HarnessTurnResult:
    command: Dict[str, Any]
    raw_output: str
    parsed: Optional[Dict[str, Any]]
    note: str
    decision_note: str
    fallback_used: bool


def _compact_agent_view(observation: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "turn": observation["turn"],
        "current_player_id": observation["current_player_id"],
        "perspective_player_id": observation["perspective_player_id"],
        "winner_id": observation["winner_id"],
        "win_conditions": observation["win_conditions"],
        "player_progress": observation["player_progress"],
        "friendly_units": observation["friendly_units"],
        "enemy_units": observation["enemy_units"],
        "resources": observation["resources"],
        "recent_events": observation["recent_events"],
        "current_player_legal_actions": observation["current_player_legal_actions"],
        "threatened_units": observation["threatened_units"],
    }


def build_natural_language_prompt(state: GameState, controlled_player_id: str) -> str:
    observation = _compact_agent_view(state.to_agent_observation(controlled_player_id))
    return (
        "You are playing a small turn-based strategy game.\n"
        f"You control player: {controlled_player_id}\n"
        "Reply with exactly one JSON object and nothing else.\n"
        "Return a JSON object with keys `command` and `decision_note`.\n"
        "The `command` value must be one command from current_player_legal_actions.\n"
        "The `decision_note` value should be a short reason for the choice.\n"
        "If no good action exists, use end_turn.\n\n"
        "If you want to stop the interactive session, type quit.\n\n"
        "Compact observation:\n"
        f"{json.dumps(observation, ensure_ascii=False, indent=2)}\n"
    )


def build_repair_prompt(
    state: GameState,
    controlled_player_id: str,
    raw_output: str,
) -> str:
    observation = _compact_agent_view(state.to_agent_observation(controlled_player_id))
    return (
        "Your previous reply was invalid.\n"
        "Reply again with exactly one JSON object and nothing else.\n"
        "Return a JSON object with keys `command` and `decision_note`.\n"
        "The `command` value must be one command from current_player_legal_actions.\n"
        "The `decision_note` value should be a short reason for the choice.\n\n"
        "If you want to stop the interactive session, type quit.\n\n"
        f"Invalid reply:\n{raw_output}\n\n"
        "Compact observation:\n"
        f"{json.dumps(observation, ensure_ascii=False, indent=2)}\n"
    )


def parse_and_validate_command(
    raw_output: str,
    legal_actions: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], str]:
    command, _, note = parse_agent_response(raw_output, legal_actions)
    return command, note


def parse_agent_output(
    raw_output: str,
    legal_actions: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], str, str]:
    return parse_agent_response(raw_output, legal_actions)


def interactive_provider(prompt: str, _: GameState, __: str) -> str:
    print(prompt)
    response = input("agent> ").strip()
    if response in {"quit", "exit"}:
        raise AgentExit()
    return response


def baseline_provider(prompt: str, state: GameState, player_id: str) -> str:
    del prompt
    engine = GameEngine(state.clone())
    command = choose_baseline_command(engine, player_id)
    return json.dumps(command, ensure_ascii=False)


def ollama_provider_factory(model: str) -> TextResponder:
    def _provider(prompt: str, _: GameState, __: str) -> str:
        completed = run_ollama(model, prompt)
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(f"ollama run failed: {stderr} | {format_ollama_diagnostics()}")
        return completed.stdout.strip()

    _provider.__name__ = f"ollama_provider[{model}]"
    return _provider


def run_episode(
    agent_provider: TextResponder,
    controlled_player_id: Optional[str] = None,
    max_turns: int = 12,
    fallback_to_baseline: bool = True,
    randomize_start: bool = True,
    debug: bool = False,
) -> Path:
    initial_state = create_default_state()
    engine = GameEngine(initial_state.clone())
    if randomize_start:
        engine.state.current_player_id = random.choice(["p1", "p2"])
    controlled_player_id = controlled_player_id or random.choice(["p1", "p2"])

    match_config = {
        "controlled_player_id": controlled_player_id,
        "starting_player_id": engine.state.current_player_id,
        "fallback_to_baseline": fallback_to_baseline,
        "provider": getattr(agent_provider, "__name__", agent_provider.__class__.__name__),
    }
    recorder = MatchRecorder(
        mode="harness",
        initial_state=initial_state.clone(),
        metadata=match_config,
    )

    print("=== Harness Episode ===")
    print("match config: " + json.dumps(match_config, ensure_ascii=False, sort_keys=True))
    if debug:
        print(format_ollama_diagnostics())
    print(format_state(engine.state))
    print()

    for _ in range(max_turns):
        if engine.state.winner_id is not None:
            break

        current_player = engine.state.current_player_id
        trace_prompt = None
        repair_prompt = None
        repair_output = None
        if current_player == controlled_player_id:
            prompt = build_natural_language_prompt(engine.state, controlled_player_id)
            trace_prompt = prompt
            if debug:
                print("=== Agent Prompt ===")
                print(prompt)
            try:
                raw_output = agent_provider(prompt, engine.state, current_player)
            except AgentExit:
                break
            legal_actions = engine.state.legal_actions_for_player(current_player)
            parsed, decision_note, note = parse_agent_output(raw_output, legal_actions)
            fallback_used = False
            if parsed is None:
                repair_prompt = build_repair_prompt(
                    engine.state,
                    controlled_player_id,
                    raw_output,
                )
                if debug:
                    print("=== Repair Prompt ===")
                    print(repair_prompt)
                repaired_output = agent_provider(repair_prompt, engine.state, current_player)
                repair_output = repaired_output
                repaired, repaired_decision_note, repaired_note = parse_agent_output(
                    repaired_output,
                    legal_actions,
                )
                if repaired is not None:
                    parsed = repaired
                    raw_output = repaired_output
                    note = f"repair:{repaired_note}"
                    decision_note = repaired_decision_note
                elif fallback_to_baseline:
                    parsed = choose_baseline_command(engine, current_player)
                    fallback_used = True
                    note = f"{note}; fallback=baseline"
                    decision_note = "fallback=baseline"
                else:
                    parsed = {"type": "end_turn"}
                    fallback_used = True
                    note = f"{note}; fallback=end_turn"
                    decision_note = "fallback=end_turn"
            if parsed is not None and not decision_note:
                decision_note = "no decision_note provided"
            command = parsed
            source = "agent"
        else:
            command = choose_baseline_command(engine, current_player)
            raw_output = json.dumps(command, ensure_ascii=False)
            note = "baseline"
            decision_note = "baseline"
            fallback_used = False
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
                "repair_prompt": repair_prompt,
                "repair_output": repair_output,
                "note": note,
                "fallback_used": fallback_used,
            },
            engine.state,
        )
        print(f"> {source} command={json.dumps(command, ensure_ascii=False)}")
        if current_player == controlled_player_id:
            print(f"  decision_note={decision_note}")
            if debug:
                print(f"  raw_output={raw_output}")
        print(f"  result={result.ok} | {result.message}")
        print(format_state(engine.state))
        print()

    report_path = recorder.write_report(engine.state, MATCH_DIR)
    report = recorder.build_report(engine.state)
    print("=== After Match ===")
    print(f"report: {report_path}")
    print("stats: " + json.dumps(report["stats"], ensure_ascii=False, sort_keys=True))
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal natural-language harness")
    parser.add_argument(
        "--agent",
        choices=["interactive", "baseline", "ollama"],
        default="ollama",
        help="agent responder mode",
    )
    parser.add_argument(
        "--model",
        default="gemma4:e2b",
        help="ollama model name when --agent ollama is used",
    )
    parser.add_argument(
        "--player",
        choices=["p1", "p2", "random"],
        default="random",
        help="controlled side for the agent",
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
        help="print local ollama diagnostics before the match starts",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.agent == "interactive":
        provider = interactive_provider
    elif args.agent == "baseline":
        provider = baseline_provider
    else:
        provider = ollama_provider_factory(args.model)

    controlled_player_id = None if args.player == "random" else args.player
    run_episode(
        provider,
        controlled_player_id=controlled_player_id,
        max_turns=args.max_turns,
        fallback_to_baseline=True,
        randomize_start=True,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
