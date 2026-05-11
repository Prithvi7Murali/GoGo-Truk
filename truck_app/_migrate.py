"""
Auto-migration helper. Called by the FastAPI lifespan on every uvicorn reload.
  1. Runs alembic autogenerate — creates a migration file if models changed.
  2. Deletes the file if it contains no actual changes (no op. calls).
  3. Runs alembic upgrade head — applies any pending migrations.
"""
import glob
import os
import subprocess
import sys
from datetime import datetime


def main():
    versions_dir = os.path.join("alembic", "versions")
    before = set(glob.glob(os.path.join(versions_dir, "*.py")))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    subprocess.run(
        [sys.executable, "-m", "alembic", "revision",
         "--autogenerate", "-m", f"auto_{ts}"],
    )

    after = set(glob.glob(os.path.join(versions_dir, "*.py")))
    new_files = after - before

    if new_files:
        new_file = new_files.pop()
        with open(new_file) as f:
            content = f.read()
        if "op." not in content:
            os.remove(new_file)
        else:
            print(f"[migrate] New migration: {os.path.basename(new_file)}")

    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])


if __name__ == "__main__":
    main()
