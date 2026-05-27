# Breathe ESG Ingestion & Review Prototype

Production-quality prototype for ESG emissions data ingestion, normalization, analyst review, and audit trail.

## Live Deployments

- Frontend: https://breatheesg-1-ocm8.onrender.com
- Backend API/Admin: https://breatheesg-qqfc.onrender.com

## Core Documentation

- Engineering decisions and tradeoffs: [DECISIONS.md](C:/project/breatheesg/DECISIONS.md)
- Data model and auditability design: [MODEL.md](C:/project/breatheesg/MODEL.md)
- Database schema notes: [01-database-schema.md](C:/project/breatheesg/docs/01-database-schema.md)
- Frontend architecture notes: [02-frontend-architecture.md](C:/project/breatheesg/docs/02-frontend-architecture.md)
- PostgreSQL setup notes: [03-postgres-setup.md](C:/project/breatheesg/docs/03-postgres-setup.md)

## Tech Stack

- Backend: Django, Django REST Framework, PostgreSQL
- Frontend: React, Tailwind, Axios
- Deploy: Render

## Local Run (Quick)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Demo Data

Use sample CSVs from:

- `samples/sap.csv`
- `samples/utility.csv`
- `samples/travel.csv`
