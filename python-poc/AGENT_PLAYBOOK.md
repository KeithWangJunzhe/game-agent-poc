# Agent Playbook

这是给 agent 看的对局说明，尽量只保留决策需要的信息。

## Task

You are controlling a simple RTS-like game through JSON commands.

## Loop

1. Read the current structured state.
2. Pick one legal command.
3. Submit the command.
4. Observe the new state.
5. Repeat until the game ends.

The state view includes the battlefield, unit positions, unit HP, and each unit's legal move directions.
Your assigned side may be `p1` or `p2` depending on the match, so do not assume you always control the same spawn corner.
The observation also exposes remaining gold-to-win, current player legal actions, and recent events.
The minimal harness asks for a natural-language reply context but still expects exactly one JSON command back.

## Legal Commands

### Move

```json
{"type":"move_unit","unit_id":"p1_worker","direction":"east"}
```

### Gather

```json
{"type":"gather","unit_id":"p1_worker"}
```

### Attack

```json
{"type":"attack","attacker_id":"p1_warrior","target_id":"p2_base"}
```

### End Turn

```json
{"type":"end_turn"}
```

## Rules to respect

- Only the current player can act.
- Units cannot move outside the board.
- Units cannot move onto occupied cells.
- Only workers gather.
- Attack requires adjacency.
- The game ends when a base is destroyed or a player reaches 10 gold.

## Decision Hints

- Prefer legal, low-risk commands.
- If no productive action is available, end the turn.
- Use the event log, board state, and move directions to avoid illegal moves.
- Use `current_player_legal_actions` when selecting a command.
- Keep the command space small and deterministic.

## Output Expectation

The harness will validate commands and return:

- `ok`
- `message`
- `state_changed`

Use these signals to adapt future actions.
