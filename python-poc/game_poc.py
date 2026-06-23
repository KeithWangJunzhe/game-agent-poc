from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


DIRECTIONS = {
    "north": (0, -1),
    "south": (0, 1),
    "west": (-1, 0),
    "east": (1, 0),
}

GOLD_TO_WIN = 10


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def step(self, direction: str) -> "Point":
        dx, dy = DIRECTIONS[direction]
        return Point(self.x + dx, self.y + dy)

    def distance_to(self, other: "Point") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


def _swap_player_id(player_id: str) -> str:
    if player_id == "p1":
        return "p2"
    if player_id == "p2":
        return "p1"
    return player_id


def _mirror_point(point: Point, width: int, height: int) -> Point:
    return Point(width - 1 - point.x, height - 1 - point.y)


@dataclass
class PlayerState:
    player_id: str
    name: str
    resources: int = 0


@dataclass
class Unit:
    unit_id: str
    owner_id: str
    kind: str
    position: Point
    hp: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "owner_id": self.owner_id,
            "kind": self.kind,
            "position": {"x": self.position.x, "y": self.position.y},
            "hp": self.hp,
        }


@dataclass
class ResourceNode:
    node_id: str
    position: Point
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "position": {"x": self.position.x, "y": self.position.y},
            "amount": self.amount,
        }


@dataclass
class GameState:
    width: int = 10
    height: int = 10
    turn: int = 1
    current_player_id: str = "p1"
    winner_id: Optional[str] = None
    players: Dict[str, PlayerState] = field(default_factory=dict)
    units: Dict[str, Unit] = field(default_factory=dict)
    resources: Dict[str, ResourceNode] = field(default_factory=dict)
    event_log: List[str] = field(default_factory=list)

    def clone(self) -> "GameState":
        return GameState(
            width=self.width,
            height=self.height,
            turn=self.turn,
            current_player_id=self.current_player_id,
            winner_id=self.winner_id,
            players={player_id: PlayerState(**vars(player)) for player_id, player in self.players.items()},
            units={
                unit_id: Unit(
                    unit_id=unit.unit_id,
                    owner_id=unit.owner_id,
                    kind=unit.kind,
                    position=Point(unit.position.x, unit.position.y),
                    hp=unit.hp,
                )
                for unit_id, unit in self.units.items()
            },
            resources={
                node_id: ResourceNode(
                    node_id=node.node_id,
                    position=Point(node.position.x, node.position.y),
                    amount=node.amount,
                )
                for node_id, node in self.resources.items()
            },
            event_log=list(self.event_log),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        board = data.get("board", {})
        players = {
            player_id: PlayerState(
                player_id=player_data["player_id"],
                name=player_data["name"],
                resources=player_data.get("resources", 0),
            )
            for player_id, player_data in data.get("players", {}).items()
        }
        units = {}
        for unit_data in data.get("units", []):
            position = unit_data["position"]
            units[unit_data["unit_id"]] = Unit(
                unit_id=unit_data["unit_id"],
                owner_id=unit_data["owner_id"],
                kind=unit_data["kind"],
                position=Point(position["x"], position["y"]),
                hp=unit_data["hp"],
            )
        resources = {}
        for node_data in data.get("resources", []):
            position = node_data["position"]
            resources[node_data["node_id"]] = ResourceNode(
                node_id=node_data["node_id"],
                position=Point(position["x"], position["y"]),
                amount=node_data["amount"],
            )
        return cls(
            width=board.get("width", 10),
            height=board.get("height", 10),
            turn=data.get("turn", 1),
            current_player_id=data.get("current_player_id", "p1"),
            winner_id=data.get("winner_id"),
            players=players,
            units=units,
            resources=resources,
            event_log=list(data.get("event_log", [])),
        )

    def in_bounds(self, position: Point) -> bool:
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def unit_at(self, position: Point) -> Optional[Unit]:
        for unit in self.units.values():
            if unit.position == position:
                return unit
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board": {"width": self.width, "height": self.height},
            "turn": self.turn,
            "current_player_id": self.current_player_id,
            "winner_id": self.winner_id,
            "players": {
                player_id: {
                    "player_id": player.player_id,
                    "name": player.name,
                    "resources": player.resources,
                }
                for player_id, player in self.players.items()
            },
            "units": [unit.to_dict() for unit in self.units.values()],
            "resources": [node.to_dict() for node in self.resources.values()],
            "event_log": list(self.event_log),
        }

    def legal_actions_for_player(self, player_id: str) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        for unit in self.units.values():
            if unit.owner_id != player_id:
                continue
            if unit.kind == "worker":
                for node in self.resources.values():
                    if node.position == unit.position and node.amount > 0:
                        actions.append({"type": "gather", "unit_id": unit.unit_id})
            if unit.kind != "base":
                for enemy in self.units.values():
                    if enemy.owner_id == player_id:
                        continue
                    if unit.position.distance_to(enemy.position) == 1:
                        actions.append(
                            {
                                "type": "attack",
                                "attacker_id": unit.unit_id,
                                "target_id": enemy.unit_id,
                            }
                        )
            for direction in self.legal_move_directions(unit.unit_id):
                actions.append(
                    {
                        "type": "move_unit",
                        "unit_id": unit.unit_id,
                        "direction": direction,
                    }
                )
        actions.append({"type": "end_turn"})
        return actions

    def player_resource_snapshot(self) -> Dict[str, int]:
        return {
            player_id: player.resources
            for player_id, player in self.players.items()
        }

    def to_agent_observation(self, perspective_player_id: Optional[str] = None) -> Dict[str, Any]:
        perspective = perspective_player_id or self.current_player_id
        friendly_units = [
            unit.to_dict()
            for unit in self.units.values()
            if unit.owner_id == perspective
        ]
        enemy_units = [
            unit.to_dict()
            for unit in self.units.values()
            if unit.owner_id != perspective
        ]
        current_player_actions = self.legal_actions_for_player(self.current_player_id)
        player_progress = {
            player_id: {
                "resources": player.resources,
                "resources_to_win": max(GOLD_TO_WIN - player.resources, 0),
            }
            for player_id, player in self.players.items()
        }
        threatened_units = []
        for unit in self.units.values():
            for enemy in self.units.values():
                if unit.owner_id == enemy.owner_id:
                    continue
                if unit.position.distance_to(enemy.position) == 1:
                    threatened_units.append(
                        {
                            "unit_id": unit.unit_id,
                            "owner_id": unit.owner_id,
                            "threatening_unit_id": enemy.unit_id,
                            "threatening_owner_id": enemy.owner_id,
                        }
                    )
                    break
        return {
            "type": "game_observation",
            "board": {"width": self.width, "height": self.height},
            "turn": self.turn,
            "current_player_id": self.current_player_id,
            "perspective_player_id": perspective,
            "winner_id": self.winner_id,
            "win_conditions": {
                "gold_to_win": GOLD_TO_WIN,
                "base_destroyed": True,
            },
            "players": {
                player_id: {
                    "player_id": player.player_id,
                    "name": player.name,
                    "resources": player.resources,
                    "resources_to_win": max(GOLD_TO_WIN - player.resources, 0),
                }
                for player_id, player in self.players.items()
            },
            "player_progress": player_progress,
            "friendly_units": friendly_units,
            "enemy_units": enemy_units,
            "all_units": [unit.to_dict() for unit in self.units.values()],
            "resources": [node.to_dict() for node in self.resources.values()],
            "recent_events": list(self.event_log[-5:]),
            "current_player_legal_actions": current_player_actions,
            "threatened_units": threatened_units,
        }

    def to_human_status_lines(self) -> List[str]:
        state = self.to_dict()
        lines = [
            f"Turn {state['turn']} | current_player={state['current_player_id']} | winner={state['winner_id']}",
            f"Board: {self.width}x{self.height}",
            "Status:",
            "  Win condition: first to 10 gold or destroy enemy base",
        ]
        lines.extend(self._render_board())
        lines.append("Players:")
        for player in state["players"].values():
            lines.append(
                f"  {player['player_id']} ({player['name']}): resources={player['resources']} "
                f"remaining_to_win={max(GOLD_TO_WIN - player['resources'], 0)}"
            )
        lines.append("Units:")
        for unit in state["units"]:
            pos = unit["position"]
            legal_directions = self.legal_move_directions(unit["unit_id"])
            lines.append(
                f"  {unit['unit_id']} [{unit['kind']}] owner={unit['owner_id']} "
                f"hp={unit['hp']} pos=({pos['x']}, {pos['y']}) "
                f"move_dirs={','.join(legal_directions) if legal_directions else 'none'}"
            )
        lines.append("Resources:")
        for node in state["resources"]:
            pos = node["position"]
            lines.append(
                f"  {node['node_id']} amount={node['amount']} pos=({pos['x']}, {pos['y']})"
            )
        if state["event_log"]:
            lines.append("Recent events:")
            lines.extend(f"- {event}" for event in state["event_log"][-5:])
        return lines

    def to_jsonable_lines(self) -> List[str]:
        return self.to_human_status_lines()

    def _render_board(self) -> List[str]:
        legend = {
            ("p1", "base"): "1B",
            ("p1", "worker"): "1W",
            ("p1", "warrior"): "1R",
            ("p2", "base"): "2B",
            ("p2", "worker"): "2W",
            ("p2", "warrior"): "2R",
        }
        occupied = {
            (unit.position.x, unit.position.y): legend.get((unit.owner_id, unit.kind), "??")
            for unit in self.units.values()
        }
        rows = ["Battlefield:"]
        header = "   " + " ".join(f"{x:>2}" for x in range(self.width))
        rows.append(header)
        for y in range(self.height):
            cells = []
            for x in range(self.width):
                cell = occupied.get((x, y))
                if cell is None:
                    resource = next(
                        (node for node in self.resources.values() if node.position == Point(x, y)),
                        None,
                    )
                    cell = "G " if resource is not None else ".."
                cells.append(f"{cell:>2}")
            rows.append(f"{y:>2} " + " ".join(cells))
        rows.append("Legend: 1B/2B base, 1W/2W worker, 1R/2R warrior, G resource")
        return rows

    def legal_move_directions(self, unit_id: str) -> List[str]:
        unit = self.units.get(unit_id)
        if unit is None:
            return []
        directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            next_position = Point(unit.position.x + dx, unit.position.y + dy)
            if not self.in_bounds(next_position):
                continue
            blocker = self.unit_at(next_position)
            if blocker is not None:
                continue
            directions.append(direction)
        return directions

    def describe_unit(self, unit_id: str) -> str:
        unit = self.units.get(unit_id)
        if unit is None:
            return f"{unit_id}: not found"
        legal_directions = self.legal_move_directions(unit_id)
        return (
            f"{unit.unit_id} [{unit.kind}] owner={unit.owner_id} hp={unit.hp} "
            f"pos={unit.position} move_dirs={','.join(legal_directions) if legal_directions else 'none'}"
        )

    def mirrored(self) -> "GameState":
        mirrored_players = {
            _swap_player_id(player_id): PlayerState(
                player_id=_swap_player_id(player_id),
                name=player.name,
                resources=player.resources,
            )
            for player_id, player in self.players.items()
        }
        mirrored_units = {}
        for unit_id, unit in self.units.items():
            mirrored_unit_id = unit_id.replace("p1_", "__tmp__").replace("p2_", "p1_").replace("__tmp__", "p2_")
            mirrored_units[mirrored_unit_id] = Unit(
                unit_id=mirrored_unit_id,
                owner_id=_swap_player_id(unit.owner_id),
                kind=unit.kind,
                position=_mirror_point(unit.position, self.width, self.height),
                hp=unit.hp,
            )
        mirrored_resources = {
            node_id: ResourceNode(
                node_id=node.node_id,
                position=_mirror_point(node.position, self.width, self.height),
                amount=node.amount,
            )
            for node_id, node in self.resources.items()
        }
        return GameState(
            width=self.width,
            height=self.height,
            turn=self.turn,
            current_player_id=_swap_player_id(self.current_player_id),
            winner_id=_swap_player_id(self.winner_id) if self.winner_id is not None else None,
            players=mirrored_players,
            units=mirrored_units,
            resources=mirrored_resources,
            event_log=list(self.event_log),
        )


@dataclass
class CommandResult:
    ok: bool
    message: str
    state_changed: bool


class GameEngine:
    def __init__(self, state: Optional[GameState] = None) -> None:
        self.state = state or create_default_state()

    def apply(self, command: Dict[str, Any]) -> CommandResult:
        if self.state.winner_id is not None:
            return CommandResult(False, "game already finished", False)

        command_type = command.get("type")
        if not command_type:
            return CommandResult(False, "missing command type", False)

        handler = {
            "move_unit": self._move_unit,
            "gather": self._gather,
            "attack": self._attack,
            "end_turn": self._end_turn,
        }.get(command_type)

        if handler is None:
            return CommandResult(False, f"unknown command type: {command_type}", False)

        return handler(command)

    def _move_unit(self, command: Dict[str, Any]) -> CommandResult:
        unit = self._get_current_player_unit(command.get("unit_id"))
        if unit is None:
            return CommandResult(False, "unit not found or not owned by current player", False)

        direction = command.get("direction")
        if direction not in DIRECTIONS:
            return CommandResult(False, f"invalid direction: {direction}", False)

        next_position = unit.position.step(direction)
        if not self._in_bounds(next_position):
            legal_directions = self.state.legal_move_directions(unit.unit_id)
            legal_text = ",".join(legal_directions) if legal_directions else "none"
            return CommandResult(
                False,
                f"move blocked by map boundary; {unit.unit_id} at {unit.position} can move: {legal_text}",
                False,
            )

        blocker = self._unit_at(next_position)
        if blocker is not None:
            return CommandResult(
                False,
                f"move blocked by {blocker.unit_id} at {next_position}",
                False,
            )

        before = unit.position
        unit.position = next_position
        self._log(
            f"{unit.unit_id} moved {direction} to ({next_position.x}, {next_position.y})"
        )
        self._advance_turn()
        return CommandResult(
            True,
            f"{unit.unit_id} moved {direction} from {before} to {next_position}",
            True,
        )

    def _gather(self, command: Dict[str, Any]) -> CommandResult:
        unit = self._get_current_player_unit(command.get("unit_id"))
        if unit is None:
            return CommandResult(False, "unit not found or not owned by current player", False)

        if unit.kind != "worker":
            return CommandResult(False, "only worker can gather", False)

        node = self._resource_at(unit.position)
        if node is None:
            return CommandResult(False, "no resource node at worker position", False)

        if node.amount <= 0:
            return CommandResult(False, "resource node already exhausted", False)

        player = self.state.players[unit.owner_id]
        player.resources += 1
        node.amount -= 1
        self._log(
            f"{unit.unit_id} gathered 1 resource from {node.node_id}; "
            f"{player.player_id} now has {player.resources}"
        )
        if player.resources >= 10 and self.state.winner_id is None:
            self.state.winner_id = player.player_id
            self._log(f"{player.player_id} wins by reaching 10 gold")
        self._advance_turn()
        return CommandResult(
            True,
            f"{unit.unit_id} gathered 1 from {node.node_id}; "
            f"{player.player_id} resources={player.resources}, {node.node_id} remaining={node.amount}",
            True,
        )

    def _attack(self, command: Dict[str, Any]) -> CommandResult:
        attacker = self._get_current_player_unit(command.get("attacker_id"))
        if attacker is None:
            return CommandResult(False, "attacker not found or not owned by current player", False)

        if attacker.kind == "base":
            return CommandResult(False, "base cannot attack", False)

        target = self.state.units.get(command.get("target_id", ""))
        if target is None:
            return CommandResult(False, "target unit not found", False)

        if target.owner_id == attacker.owner_id:
            return CommandResult(False, "cannot attack own unit", False)

        if attacker.position.distance_to(target.position) != 1:
            return CommandResult(False, "target not adjacent", False)

        damage = 2 if attacker.kind == "warrior" else 1
        target.hp -= damage
        self._log(
            f"{attacker.unit_id} attacked {target.unit_id} for {damage} damage"
        )
        if target.hp <= 0:
            self._log(f"{target.unit_id} was destroyed")
            del self.state.units[target.unit_id]
            if target.kind == "base":
                self.state.winner_id = attacker.owner_id
                self._log(f"{attacker.owner_id} wins by destroying the enemy base")
            target_status = "destroyed"
        else:
            target_status = f"hp now {target.hp}"

        self._advance_turn()
        return CommandResult(
            True,
            f"{attacker.unit_id} attacked {target.unit_id} for {damage} damage; {target.unit_id} {target_status}",
            True,
        )

    def _end_turn(self, command: Dict[str, Any]) -> CommandResult:
        self._log(f"{self.state.current_player_id} ended turn")
        self._advance_turn()
        return CommandResult(
            True,
            f"turn ended; next player={self.state.current_player_id}",
            True,
        )

    def _get_current_player_unit(self, unit_id: Any) -> Optional[Unit]:
        if not unit_id:
            return None
        unit = self.state.units.get(str(unit_id))
        if unit is None or unit.owner_id != self.state.current_player_id:
            return None
        return unit

    def _unit_at(self, position: Point) -> Optional[Unit]:
        for unit in self.state.units.values():
            if unit.position == position:
                return unit
        return None

    def _resource_at(self, position: Point) -> Optional[ResourceNode]:
        for node in self.state.resources.values():
            if node.position == position:
                return node
        return None

    def _in_bounds(self, position: Point) -> bool:
        return 0 <= position.x < self.state.width and 0 <= position.y < self.state.height

    def _advance_turn(self) -> None:
        self.state.turn += 1
        self.state.current_player_id = "p2" if self.state.current_player_id == "p1" else "p1"

    def _log(self, message: str) -> None:
        self.state.event_log.append(message)


def create_default_state() -> GameState:
    players = {
        "p1": PlayerState(player_id="p1", name="Player 1"),
        "p2": PlayerState(player_id="p2", name="Player 2"),
    }
    units = {
        "p1_base": Unit("p1_base", "p1", "base", Point(0, 0), 5),
        "p1_worker": Unit("p1_worker", "p1", "worker", Point(1, 0), 2),
        "p1_warrior": Unit("p1_warrior", "p1", "warrior", Point(0, 1), 3),
        "p2_base": Unit("p2_base", "p2", "base", Point(9, 9), 5),
        "p2_worker": Unit("p2_worker", "p2", "worker", Point(8, 9), 2),
        "p2_warrior": Unit("p2_warrior", "p2", "warrior", Point(9, 8), 3),
    }
    resources = {
        "gold_1": ResourceNode("gold_1", Point(4, 4), 20),
    }
    return GameState(players=players, units=units, resources=resources)


def create_mirrored_state() -> GameState:
    return create_default_state().mirrored()


def format_state(state: GameState) -> str:
    return "\n".join(state.to_jsonable_lines())


def demo_commands() -> Iterable[Dict[str, Any]]:
    return (
        {"type": "move_unit", "unit_id": "p1_worker", "direction": "east"},
        {"type": "move_unit", "unit_id": "p2_worker", "direction": "west"},
        {"type": "move_unit", "unit_id": "p1_worker", "direction": "east"},
        {"type": "move_unit", "unit_id": "p2_worker", "direction": "west"},
        {"type": "end_turn"},
    )
