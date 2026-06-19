# Yahaha Game

React + Vite + FastAPI + PostgreSQL MVP scaffold for an AI Native interactive game platform.

## Local Development

Create a local environment file first:

```bash
cp .env.example .env
```

Recommended workflow:

- Run `db` / `minio` / `backend` with Docker Compose
- Run `frontend` locally with Vite hot reload

Start backend-side local services:

```bash
docker compose up --build
```

Services:

- Backend API: http://localhost:8000
- Backend Swagger UI: http://localhost:8000/docs
- Backend ReDoc: http://localhost:8000/redoc
- Backend OpenAPI JSON: http://localhost:8000/openapi.json
- Backend health: http://localhost:8000/health
- Backend database readiness: http://localhost:8000/ready
- PostgreSQL: localhost:5432
- MinIO S3 API: http://localhost:9000
- MinIO Console: http://localhost:9001

Start the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Frontend local URL:

- Frontend: http://localhost:5173

Optional: if you explicitly want the frontend inside Docker, enable the dedicated profile:

```bash
docker compose --profile docker-frontend up --build frontend
```

OAuth notes:

- Google login is implemented in the backend and frontend Auth Modal, but real OAuth callback verification requires valid `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
- Google redirect URI for local development: `http://localhost:8000/api/auth/oauth/google/callback`.
- GitHub OAuth is intentionally a reserved endpoint in the MVP and returns a clear "coming later" response.

If a local port is already occupied, edit the matching host-side port in `docker-compose.yml`. For local Vite dev, you can also run `npm run dev -- --port 5174` and update `FRONTEND_ORIGIN` if needed.

Verify the stack after startup:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
curl -i http://localhost:8000/openapi.json
```

Open `http://localhost:5173` for the frontend and `http://localhost:9001` for the MinIO Console.

If you previously started the old Docker frontend and keep seeing stale pages, stop it once:

```bash
docker compose stop frontend
```

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
