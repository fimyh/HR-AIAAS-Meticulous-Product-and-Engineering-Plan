# HR-AIAAS FastAPI route bundle

This bundle defines the complete REST route contract for the planned backend.

## Important

- System/status/readiness endpoints are functional.
- Domain endpoints deliberately return HTTP 501 until repositories, authorization, audit, and services are implemented.
- Do not remove the 501 behavior merely to make endpoints appear successful.
- Authentication and authorization must be implemented before candidate or document data is exposed.
- File uploads require `python-multipart`: `uv add python-multipart`.

## Install

Copy `src/hr_aiaas/api/` into the project, then add to `main.py`:

```python
from hr_aiaas.api.v1 import api_v1_router
application.include_router(api_v1_router)
```

## Verify

```powershell
uv add python-multipart email-validator
uv run python -m compileall "src\hr_aiaas\api"
uv run python -c "from hr_aiaas.main import app; print('\n'.join(sorted(route.path for route in app.routes)))"
uv run uvicorn hr_aiaas.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`.
