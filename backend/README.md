# SalesLens Backend

Run:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Entrypoint: `app.main:app`
