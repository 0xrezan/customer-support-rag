"""Start the Dramatiq worker locally.

Usage: python scripts/run_worker.py
Or:    python -m dramatiq app.infrastructure.queue.tasks
"""

import subprocess
import sys


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "dramatiq", "app.infrastructure.queue.tasks"],
        check=True,
    )


if __name__ == "__main__":
    main()
