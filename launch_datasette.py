"""
Launch an interactive Datasette web app for the NBA database.

Opens http://127.0.0.1:8001 in your browser with:
"""

import subprocess
import datasette
import sys
import os

DB_PATH = "nba.db"
METADATA_PATH = "metadata.json"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Check that the database exists
if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found in {os.getcwd()}")
    sys.exit(1)

# Launch command
cmd = [sys.executable, "-m", "datasette", DB_PATH, "--open"]
if os.path.exists(METADATA_PATH):
    cmd.extend(["--metadata", METADATA_PATH])

subprocess.call(cmd)
