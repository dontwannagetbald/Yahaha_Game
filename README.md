# Yahaha Game

Minimal React + Vite + FastAPI + PostgreSQL scaffold.

## Local Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/health
- Backend database readiness: http://localhost:8000/ready
- PostgreSQL: localhost:5432

## Local Checks

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/pytest backend/tests/test_health.py
```

Frontend:

```bash
cd frontend
npm install
npm run build
```
