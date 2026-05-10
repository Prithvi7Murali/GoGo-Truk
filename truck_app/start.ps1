python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit 1 }
uvicorn app.main:app --reload
