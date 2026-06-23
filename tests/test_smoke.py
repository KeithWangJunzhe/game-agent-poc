import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from main import main


class SmokeTest(unittest.TestCase):
    def test_main_runs_demo(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()

        output = buffer.getvalue()
        self.assertIn("Game Agent POC Demo", output)
        self.assertIn("Turn 1", output)


if __name__ == "__main__":
    unittest.main()
