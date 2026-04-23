# Bristol Regional Food Network Marketplace

This repository is an upgraded combined **DESD + Advanced AI** project for the Bristol Regional Food Network case study. It now includes stronger ownership controls, better order handling, improved AI service model management, and broader automated test coverage.

## What was fixed in this upgraded version
- customer and producer registration validation improved
- session-based login and logout endpoints added
- producer-only product creation and owner-only product editing enforced
- customer-only cart and order endpoints enforced
- admin dashboard locked to staff users
- cart item update and remove support added
- product availability and stock validation tightened
- multi-vendor orders now support per-producer delivery dates
- sandbox payment failure path supported for demo/testing
- transaction reference exposed in order output
- status progression enforced: pending -> confirmed -> ready -> delivered
- weekly settlement response includes running tax-year total
- AI service now supports model upload, list, activate, and rollback
- admin dashboard includes recent activity and producer exposure snapshot
- repository cleaned for submission use

## Tech stack
- Django + Django REST Framework
- FastAPI
- PostgreSQL in Docker mode
- SQLite in quick local mode
- pandas + scikit-learn
- pytest

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  `.venv\Scripts\activate`
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

In a second terminal:

```bash
uvicorn ai_service.main:app --reload --port 8001
```

## Docker run

```bash
docker compose up --build
```

## Useful endpoints
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/producers/register/`
- `POST /api/customers/register/`
- `GET /api/products/`
- `POST /api/products/`
- `POST /api/cart/add/`
- `PATCH /api/cart/items/<item_id>/`
- `DELETE /api/cart/items/<item_id>/`
- `POST /api/orders/create/`
- `GET /api/orders/`
- `GET /api/producer-orders/<producer_id>/`
- `PATCH /api/producer-suborders/<suborder_id>/status/`
- `POST /api/settlements/<producer_id>/`
- `GET /api/admin-dashboard/`
- `GET /api/ai/recommend/<customer_id>/`
- `GET /api/ai/forecast/<producer_id>/`

## AI service endpoints
- `GET /recommend/{customer_id}`
- `GET /forecast/{producer_id}`
- `POST /quality-grade`
- `POST /models/upload`
- `GET /models/list`
- `POST /models/activate/{task}/{model_name}`
- `POST /models/rollback/{task}`

## Demo flow
1. Register or log in as producer and customer.
2. Producer creates or edits a product.
3. Customer browses visible products and adds items to cart.
4. Customer creates an order with sandbox payment and optional per-producer delivery dates.
5. Producer views only their own sub-orders and updates status.
6. Settlement endpoint shows 95/5 split and running total.
7. AI recommendation and forecast endpoints show explainable output.
8. Admin dashboard shows activity and monitoring snapshot.

## Automated checks
Run from repository root:

```bash
pytest
```

## Honest limitations still left
- no polished frontend UI is included here
- no real email/notification service
- no Stripe integration beyond sandbox-style transaction handling
- food-miles uses a compact postcode mapping for demo purposes
- fairness monitoring is lightweight rather than full production analytics
- no PDF export for settlements yet
