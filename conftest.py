# Root conftest: pytest imports this before collecting tests, and its
# presence anchors the project root on sys.path. Together with
# `pythonpath = ["."]` in pyproject.toml this keeps imports working
# when tests are run with the plain `pytest` binary (as CI does),
# not only via `python -m pytest`.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
