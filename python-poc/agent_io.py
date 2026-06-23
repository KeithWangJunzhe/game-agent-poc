from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    candidates: List[Tuple[int, int, Dict[str, Any]]] = []

    def _add_candidate(start: int, end: int, candidate_text: str) -> None:
        try:
            loaded = json.loads(candidate_text)
        except json.JSONDecodeError:
            return
        if isinstance(loaded, dict):
            score = 0
            if "command" in loaded:
                score += 10
            if "decision_note" in loaded:
                score += 5
            candidates.append((score, start, loaded))

    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        _add_candidate(0, len(stripped), stripped)

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced is not None:
        _add_candidate(fenced.start(1), fenced.end(1), fenced.group(1))

    starts = [index for index, char in enumerate(text) if char == "{"]
    for start in starts:
        depth = 0
        for end in range(start, len(text)):
            char = text[end]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : end + 1]
                    _add_candidate(start, end + 1, candidate)
                    break

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def _split_command_and_note(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    if isinstance(payload.get("command"), dict):
        command = dict(payload["command"])
        decision_note = str(payload.get("decision_note", "")).strip()
        return command, decision_note

    command = dict(payload)
    decision_note = str(command.pop("decision_note", "")).strip()
    return command, decision_note


def parse_agent_response(
    raw_output: str,
    legal_actions: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], str, str]:
    payload = extract_json_object(raw_output)
    if payload is None:
        return None, "", "no_json_found"

    command, decision_note = _split_command_and_note(payload)
    if command not in legal_actions:
        return None, decision_note, "command_not_legal"
    return command, decision_note, "ok"
