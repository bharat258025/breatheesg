# PostgreSQL Setup (VS Code, Windows, PowerShell)

## 1) Start PostgreSQL

From project root:

```powershell
docker compose up -d
```

Verify:

```powershell
docker ps
```

You should see `breatheesg-postgres` running on `0.0.0.0:5432->5432`.

## 2) Activate backend venv

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install django djangorestframework psycopg2-binary
```

## 3) Set DB env vars in current terminal

```powershell
$env:DB_ENGINE="django.db.backends.postgresql"
$env:DB_NAME="breatheesg"
$env:DB_USER="postgres"
$env:DB_PASSWORD="postgres"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
```

Optional:

```powershell
$env:DEBUG="1"
$env:ALLOWED_HOSTS="127.0.0.1,localhost"
```

## 4) Run Django migrations

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 5) If you still get connection refused

Run:

```powershell
docker logs breatheesg-postgres
```

Common causes:
- Docker Desktop not running
- Port `5432` already used by another local PostgreSQL instance
- Wrong env var values in the active terminal session
