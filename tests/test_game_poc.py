import sys
import unittest
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POC_DIR = PROJECT_ROOT / "python-poc"
if str(POC_DIR) not in sys.path:
    sys.path.insert(0, str(POC_DIR))

from game_poc import GameEngine, Point, create_default_state
from baseline_bot import choose_baseline_command
from match_report import MatchRecorder
from harness import extract_json_object, parse_and_validate_command
from analysis.report_tools import aggregate_summaries, summarize_report


class GamePocTest(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(create_default_state())

    def test_move_updates_position_and_turn(self):
        result = self.engine.apply(
            {"type": "move_unit", "unit_id": "p1_worker", "direction": "east"}
        )

        self.assertTrue(result.ok)
        self.assertIn("moved east from (1, 0) to (2, 0)", result.message)
        self.assertEqual(self.engine.state.units["p1_worker"].position, Point(2, 0))
        self.assertEqual(self.engine.state.turn, 2)
        self.assertEqual(self.engine.state.current_player_id, "p2")

    def test_move_boundary_failure_shows_legal_directions(self):
        self.engine.state.units["p1_worker"].position = Point(0, 1)

        result = self.engine.apply(
            {"type": "move_unit", "unit_id": "p1_worker", "direction": "west"}
        )

        self.assertFalse(result.ok)
        self.assertIn("move blocked by map boundary", result.message)
        self.assertIn("can move:", result.message)

    def test_gather_increments_resources(self):
        self.engine.state.units["p1_worker"].position = Point(4, 4)

        result = self.engine.apply({"type": "gather", "unit_id": "p1_worker"})

        self.assertTrue(result.ok)
        self.assertIn("resources=1", result.message)
        self.assertEqual(self.engine.state.players["p1"].resources, 1)
        self.assertEqual(self.engine.state.resources["gold_1"].amount, 19)

    def test_default_gold_mine_amount_is_twenty(self):
        state = create_default_state()

        self.assertEqual(state.resources["gold_1"].amount, 20)

    def test_gather_to_ten_gold_wins(self):
        self.engine.state.units["p1_worker"].position = Point(4, 4)
        self.engine.state.players["p1"].resources = 9

        result = self.engine.apply({"type": "gather", "unit_id": "p1_worker"})

        self.assertTrue(result.ok)
        self.assertEqual(self.engine.state.players["p1"].resources, 10)
        self.assertEqual(self.engine.state.winner_id, "p1")
        self.assertIn("resources=10", result.message)

    def test_attack_can_destroy_base(self):
        self.engine.state.units["p1_warrior"].position = Point(8, 9)
        self.engine.state.units["p2_base"].hp = 2

        result = self.engine.apply(
            {
                "type": "attack",
                "attacker_id": "p1_warrior",
                "target_id": "p2_base",
            }
        )

        self.assertTrue(result.ok)
        self.assertTrue("hp now" in result.message or "destroyed" in result.message)
        self.assertNotIn("p2_base", self.engine.state.units)
        self.assertEqual(self.engine.state.winner_id, "p1")

    def test_state_serializes(self):
        data = self.engine.state.to_dict()

        self.assertEqual(data["board"]["width"], 10)
        self.assertEqual(data["board"]["height"], 10)
        self.assertIn("p1", data["players"])
        self.assertGreaterEqual(len(data["units"]), 6)

    def test_state_lines_include_battlefield_and_move_dirs(self):
        lines = self.engine.state.to_jsonable_lines()

        self.assertTrue(any(line.startswith("Battlefield:") for line in lines))
        self.assertTrue(any(line.startswith("Status:") for line in lines))
        self.assertTrue(any("remaining_to_win=" in line for line in lines))
        self.assertTrue(any("move_dirs=" in line for line in lines))

    def test_agent_observation_has_legal_actions(self):
        observation = self.engine.state.to_agent_observation("p1")

        self.assertEqual(observation["type"], "game_observation")
        self.assertEqual(observation["perspective_player_id"], "p1")
        self.assertIn("current_player_legal_actions", observation)
        self.assertTrue(observation["current_player_legal_actions"])
        self.assertIn("friendly_units", observation)
        self.assertIn("enemy_units", observation)

    def test_match_report_writes_json(self):
        recorder = MatchRecorder(mode="demo", initial_state=create_default_state())
        recorder.record_step(
            {"type": "end_turn"},
            {"ok": True, "message": "turn ended", "state_changed": True},
            self.engine.state,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = recorder.write_report(self.engine.state, Path(tmpdir))

            self.assertTrue(path.exists())
            self.assertTrue(path.name.startswith("match-"))
            report = path.read_text(encoding="utf-8")
            self.assertIn('"mode": "demo"', report)
            self.assertIn('"total_commands": 1', report)

    def test_match_report_includes_trajectory_and_winner_reason(self):
        state = create_default_state()
        state.winner_id = "p1"
        state.event_log.append("p1 wins by reaching 10 gold")
        recorder = MatchRecorder(mode="demo", initial_state=create_default_state())
        recorder.record_step(
            {"type": "end_turn"},
            {"ok": True, "message": "turn ended", "state_changed": True},
            self.engine.state,
        )

        report = recorder.build_report(state)

        self.assertIn("trajectory", report)
        self.assertEqual(report["stats"]["winner_reason"], "gold")

    def test_analysis_helpers_summarize_match(self):
        recorder = MatchRecorder(mode="demo", initial_state=create_default_state())
        recorder.record_step(
            {"type": "end_turn"},
            {"ok": True, "message": "turn ended", "state_changed": True, "source": "baseline"},
            self.engine.state,
        )
        report = recorder.build_report(self.engine.state)
        summary = summarize_report(report)
        aggregate = aggregate_summaries([summary, summary])

        self.assertEqual(summary["total_commands"], 1)
        self.assertEqual(aggregate["matches"], 2)
        self.assertEqual(aggregate["total_commands"], 2)

    def test_baseline_prefers_gather_on_resource(self):
        self.engine.state.units["p1_worker"].position = Point(4, 4)

        command = choose_baseline_command(self.engine, "p1")

        self.assertEqual(command["type"], "gather")
        self.assertEqual(command["unit_id"], "p1_worker")

    def test_harness_extracts_json_from_text(self):
        parsed = extract_json_object("thinking...\n{\"type\":\"end_turn\"}\n")

        self.assertEqual(parsed, {"type": "end_turn"})

    def test_harness_validates_against_legal_actions(self):
        legal_actions = self.engine.state.legal_actions_for_player("p1")
        command, note = parse_and_validate_command(
            "{\"type\":\"move_unit\",\"unit_id\":\"p1_worker\",\"direction\":\"east\"}",
            legal_actions,
        )

        self.assertEqual(note, "ok")
        self.assertIsNotNone(command)


if __name__ == "__main__":
    unittest.main()
