"""
Auto-migration helper. Called by the FastAPI lifespan on every uvicorn reload.
  1. Creates all tables directly via SQLAlchemy create_all (safe — skips existing tables)
  2. Stamps alembic to head so it doesn't try to re-run old migrations
  3. Runs alembic autogenerate for any NEW changes going forward
  4. Applies any pending migrations
"""
import glob
import os
import subprocess
import sys
from datetime import datetime


def main():
    # Step 1 — Create all tables directly from SQLAlchemy models
    # This is safe — create_all skips tables that already exist
    try:
        from app.database import engine, Base
        import app.models.kyc
        import app.models.consent
        import app.models.fleet
        import app.models.vehicle_type
        import app.models.availability
        import app.models.booking
        import app.models.rate_card
        import app.models.invoice
        import app.models.cancellation
        import app.models.admin_user
        import app.models.notification_log

        Base.metadata.create_all(bind=engine)
        print("[migrate] Tables created/verified via SQLAlchemy")
    except Exception as e:
        print(f"[migrate] create_all error: {e}")
        return

    # Step 2 — Stamp alembic to head so old migrations don't run
    subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", "head"],
        capture_output=True
    )

    # Step 3 — Autogenerate migration for any NEW model changes
    versions_dir = os.path.join("alembic", "versions")
    before = set(glob.glob(os.path.join(versions_dir, "*.py")))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    subprocess.run(
        [sys.executable, "-m", "alembic", "revision",
         "--autogenerate", "-m", f"auto_{ts}"],
        capture_output=True
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

    # Step 4 — Apply any pending migrations
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])


if __name__ == "__main__":
    main()