import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    backend = Path(__file__).resolve().parent
    os.chdir(backend)
    subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
    )


if __name__ == "__main__":
    main()
