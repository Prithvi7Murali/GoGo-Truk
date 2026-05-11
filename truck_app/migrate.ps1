param(
    [Parameter(Mandatory=$true)]
    [string]$message
)
python -m alembic revision --autogenerate -m $message
