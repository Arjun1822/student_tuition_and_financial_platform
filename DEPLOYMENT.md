# Deployment & Infrastructure Guide

This guide describes containerized deployment with Docker Compose, production environment configurations, network topologies, and volume management.

---

## 1. Container Architecture & Docker Compose

The platform is orchestrated via `docker-compose.yml` comprising three production services interconnected on a private bridge network (`app_network`):

```
                                    +-----------------------+
                                    |     Client Browser    |
                                    +-----------+-----------+
                                                |
                                                | Port 80 (HTTP)
                                                v
+-----------------------------------------------------------------------------------+
| Docker Network: app_network                                                       |
|                                                                                   |
|  +---------------------------+                                                    |
|  | student_finance_frontend  |  Nginx Alpine Reverse Proxy                        |
|  | (Port 80)                 |  - Serves static compiled React assets             |
|  +-------------+-------------+  - Proxies /api and /health to backend:8000        |
|                |                                                                  |
|                | HTTP (Internal)                                                  |
|                v                                                                  |
|  +---------------------------+                                                    |
|  | student_finance_backend   |  FastAPI + Uvicorn (Python 3.12-slim)              |
|  | (Port 8000)               |  - Healthcheck: http://localhost:8000/health       |
|  +-------------+-------------+  - Depends on: mysql (service_healthy)             |
|                |                                                                  |
|                | TCP 3306 (Internal)                                              |
|                v                                                                  |
|  +---------------------------+                                                    |
|  | student_finance_db        |  MySQL 8.0 Engine                                  |
|  | (Port 3306)               |  - Healthcheck: mysqladmin ping                   |
|  +-------------+-------------+  - Volume: mysql_data (/var/lib/mysql)             |
|                |                                                                  |
+----------------+------------------------------------------------------------------+
                 |
                 v
        +------------------+
        | Named Volume:    |
        | mysql_data       |
        +------------------+
```

---

## 2. Service Specifications

### 2.1 MySQL Service (`student_finance_db`)
- **Image**: `mysql:8.0`
- **Command**: `--default-authentication-plugin=mysql_native_password`
- **Volume**: `mysql_data:/var/lib/mysql` for persistent database storage across restarts.
- **Healthcheck**: Runs `mysqladmin ping -h localhost -u root -p<PASSWORD>` every 10s.
- **Port**: `3306:3306`

### 2.2 Backend Service (`student_finance_backend`)
- **Build Context**: `./backend/Dockerfile` (Multi-layer `python:3.12-slim`).
- **Dependencies**: Waits for `mysql` container to report `service_healthy`.
- **Healthcheck**: Executes Python urllib probe against `http://localhost:8000/health`.
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 2.3 Frontend Service (`student_finance_frontend`)
- **Build Context**: `./frontend/Dockerfile`
  - *Stage 1*: `node:22-alpine` runs `npm run build` producing optimized production assets in `/app/dist`.
  - *Stage 2*: `nginx:alpine` copies dist assets and custom `nginx.conf`.
- **Nginx Configuration**:
  - Gzip compression enabled.
  - SPA fallback: `try_files $uri $uri/ /index.html;`.
  - Internal reverse proxy: forwards `/api/*`, `/health`, and `/docs` to `http://backend:8000`.

---

## 3. Production Deployment Commands

```powershell
# 1. Validate Docker Compose syntax
docker-compose config

# 2. Build and launch services in background
docker-compose up --build -d

# 3. Verify container statuses
docker-compose ps

# 4. View aggregated real-time container logs
docker-compose logs -f

# 5. Execute database seed inside running container (if unseeded)
docker-compose exec backend python scripts/seed_db.py

# 6. Graceful shutdown
docker-compose down
```

---

## 4. Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MYSQL_HOST` | `mysql` | Hostname of database container. |
| `MYSQL_PORT` | `3306` | MySQL TCP port. |
| `MYSQL_USER` | `root` | Database user account. |
| `MYSQL_PASSWORD` | `<CONFIGURED_SECRET>` | Database authentication password. |
| `MYSQL_DATABASE` | `student_finance_db` | Primary database name. |
| `SECRET_KEY` | `<CONFIGURED_SECRET>` | 32+ character JWT HMAC secret. |
| `ALGORITHM` | `HS256` | JWT signature algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `60` | Token validity duration in minutes. |
| `CORS_ORIGINS` | `["http://localhost:80", ...]` | Allowed HTTP origins array. |
