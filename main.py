from __future__ import annotations

import os
import subprocess
import sys


def main():
    port = os.environ.get("CASHPILOT_PORT", "5000")
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address=0.0.0.0",
        f"--server.port={port}",
    ]
    subprocess.run(cmd, check=False, env=env)


if __name__ == "__main__":
    main()
