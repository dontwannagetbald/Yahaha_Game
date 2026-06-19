# Yahaha Game

React + Vite + FastAPI + PostgreSQL MVP scaffold for an AI Native interactive game platform.

## Local Docker Compose

Create a local environment file first:

```bash
cp .env.example .env
```

Start the full local stack with one command:

```bash
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/health
- Backend database readiness: http://localhost:8000/ready
- PostgreSQL: localhost:5432
- MinIO S3 API: http://localhost:9000
- MinIO Console: http://localhost:9001

OAuth notes:

- Google login is implemented in the backend and frontend Auth Modal, but real OAuth callback verification requires valid `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
- Google redirect URI for local development: `http://localhost:8000/api/auth/oauth/google/callback`.
- GitHub OAuth is intentionally a reserved endpoint in the MVP and returns a clear "coming later" response.

If a local port is already occupied, edit the matching host-side port in `docker-compose.yml`. For example, change `"5173:5173"` to `"5174:5173"` for the frontend, then update `VITE_API_BASE_URL` or browser URLs as needed.

Verify the stack after startup:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
```

Open `http://localhost:5173` for the frontend and `http://localhost:9001` for the MinIO Console.

## Local Checks

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/pytest backend/tests
```

Database migration:

```bash
docker compose run --rm backend alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
npm run build
```
