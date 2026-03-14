# Trend Analysis System Backend

FastAPI backend for collecting RSS/news content, preprocessing Russian-language text, running TF-IDF + Logistic Regression sentiment analysis, LDA topic modeling, and calculating trend metrics.

## Quick start

1. Create PostgreSQL database `trends_db`
2. Copy `.env.example` to `.env`
3. Install requirements
4. Run migrations
5. Start API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`
