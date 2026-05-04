# Bristol Regional Food Network — Digital Marketplace

A full-stack regional food marketplace connecting local producers with customers within 20 miles of Bristol. Built for the UWE Bristol DESD module (UFCFTR-30-3) using Django REST Framework, FastAPI, and Docker.

---

## What this system does

- Producers list seasonal products with harvest dates, allergen info, organic certification, and surplus discounts
- Customers browse by category, search, filter, and place multi-vendor orders in a single checkout
- Orders are automatically split into per-producer sub-orders, each with its own delivery date and status lifecycle
- A 5% network commission is calculated and deducted automatically on every order
- Food miles are calculated using the Haversine formula across 100+ Bristol-area postcodes
- An AI service provides demand forecasting, personalised recommendations, and quality grading
- Weekly financial settlements show each producer's 95% payout and running tax-year total
- A staff-only admin dashboard shows platform-wide activity, top products, and producer exposure

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | Django 4 + Django REST Framework |
| AI service | FastAPI + scikit-learn + pandas |
| Database | PostgreSQL (Docker) / SQLite (local) |
| Frontend | Django templates + vanilla JS |
| Auth | Django session-based authentication |
| Containerisation | Docker + Docker Compose |
| Testing | pytest + Django test client |

---

## Quick start — Docker (recommended)

From the project root:

```bash
docker-compose up --build
```

This starts three services:
- `db` — PostgreSQL on port 5432
- `backend` — Django on port 8000 (auto-runs migrations + seed data)
- `ai_service` — FastAPI on port 8001

Then open your browser:

| URL | What you will see |
|---|---|
| `http://localhost:8000/market/login/` | Sign in / Register |
| `http://localhost:8000/market/` | Product catalogue |
| `http://localhost:8000/market/cart/` | Cart and checkout |
| `http://localhost:8000/market/orders/` | Customer order history |
| `http://localhost:8000/market/producer/` | Producer hub |
| `http://localhost:8000/market/admin-dash/` | Admin dashboard (staff only) |
| `http://localhost:8001/docs` | AI service Swagger UI |

---

## Quick start — Local (no Docker)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Django backend
cd backend
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

In a second terminal from the project root:

```bash
uvicorn ai_service.main:app --reload --port 8001
```

---

## Demo accounts

All created automatically by `seed_demo_data`:

| Username | Password | Role |
|---|---|---|
| `customer_robert` | `Password123!` | Customer |
| `producer_jane` | `Password123!` | Producer (Bristol Valley Farm) |
| `producer_dairy` | `Password123!` | Producer (Hillside Dairy) |
| `admin_1` | `Password123!` | Admin |

To access the admin dashboard, create a superuser:

```bash
# Docker
docker-compose exec backend python /app/backend/manage.py createsuperuser

# Local
python manage.py createsuperuser
```

---

## Demo flow

The full end-to-end demo takes approximately 5 minutes.

**1. Customer journey**
- Sign in as `customer_robert`
- Browse the shop — filter by Organic, Surplus, or category
- Add products from Bristol Valley Farm to cart
- Checkout — select per-producer delivery dates, use sandbox payment
- View order in My Orders — see transaction reference, food miles, and 5% commission

**2. Producer journey**
- Sign in as `producer_jane`
- Producer Hub > Sub-orders — see the incoming order
- Advance status: Pending > Confirmed > Ready > Delivered
- Settlement tab — request weekly settlement, see 95/5 payout split
- AI Forecast tab — view demand predictions per product with confidence scores

**3. Admin view**
- Sign in as your superuser account
- Admin Dashboard — live stats, activity feed, top products, platform users
- Observe the order and status changes appear in the activity log in real time

---

## API endpoints

### Authentication
| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/login/` | Anyone |
| POST | `/api/auth/logout/` | Authenticated |
| GET | `/api/csrf/` | Anyone — fetches CSRF cookie for JS frontend |

### Registration
| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/producers/register/` | Anyone |
| POST | `/api/customers/register/` | Anyone |

### Products
| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/products/` | Anyone — supports `?search=`, `?category=`, `?organic_only=true`, `?visible_only=true` |
| POST | `/api/products/` | Producers only |
| PATCH | `/api/products/<id>/` | Owning producer only |

### Cart
| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/cart/<customer_id>/` | Owning customer |
| POST | `/api/cart/add/` | Customers only |
| PATCH | `/api/cart/items/<item_id>/` | Owning customer |
| DELETE | `/api/cart/items/<item_id>/` | Owning customer |

### Orders
| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/orders/create/` | Customers only |
| GET | `/api/orders/` | Own customer or staff |
| GET | `/api/producer-orders/<producer_id>/` | Owning producer only |
| PATCH | `/api/producer-suborders/<suborder_id>/status/` | Owning producer only |

### Settlements and Admin
| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/settlements/<producer_id>/` | Owning producer only |
| GET | `/api/admin-dashboard/` | Staff and superuser only |

### AI endpoints (proxied through Django)
| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/ai/recommend/<customer_id>/` | Owning customer |
| GET | `/api/ai/forecast/<producer_id>/` | Owning producer |

### AI service direct (port 8001)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/recommend/{customer_id}` | Personalised product recommendations |
| GET | `/forecast/{producer_id}` | Weekly demand forecast per product |
| POST | `/quality-grade` | Quality grading A/B/C from produce attributes |
| POST | `/models/upload` | Upload a new model file |
| GET | `/models/list` | List all registered models |
| POST | `/models/activate/{task}/{name}` | Activate a specific model version |
| POST | `/models/rollback/{task}` | Roll back to default model |

---

## Project structure

```
bristol_marketplace_full_marks_ready/
├── backend/
│   ├── core/                        # Django settings and URL config
│   ├── marketplace/
│   │   ├── models.py                # All database models
│   │   ├── views.py                 # API views
│   │   ├── serializers.py           # Business logic and validation
│   │   ├── permissions.py           # Custom permission classes
│   │   ├── frontend_views.py        # Template views for frontend pages
│   │   ├── urls.py                  # API and frontend URL routing
│   │   ├── services/
│   │   │   ├── food_miles.py        # Haversine distance, 100+ postcodes
│   │   │   └── settlements.py       # Weekly settlement calculation
│   │   ├── templates/marketplace/   # Frontend HTML templates
│   │   │   ├── base.html            # Shared nav, CSS variables, auth helpers
│   │   │   ├── catalogue.html       # Product browsing with filters
│   │   │   ├── cart.html            # Cart and checkout with payment
│   │   │   ├── orders.html          # Customer order history
│   │   │   ├── producer.html        # Producer hub (products, orders, settlement, AI)
│   │   │   ├── admin_dash.html      # Staff-only network dashboard
│   │   │   └── login.html           # Login and registration
│   │   └── management/commands/
│   │       └── seed_demo_data.py    # Populates demo users and products
│   └── manage.py
├── ai_service/
│   ├── main.py                      # FastAPI app
│   ├── recommendations.py           # Collaborative filtering recommender
│   ├── forecasting.py               # Linear regression demand forecaster
│   ├── quality_grading.py           # Rule-based and ML quality grader
│   └── cv_model/                    # Computer vision quality model training
├── data/                            # CSV seed data for AI models
├── tests/                           # pytest test suite
├── docs/                            # Architecture notes and AI evaluation
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.ai
└── requirements.txt
```

---

## Running tests

From the project root:

```bash
# All tests
pytest

# Django backend tests only
cd backend && python manage.py test marketplace

# AI service tests only
pytest tests/test_ai_service.py -v
```

---

## Key design decisions

**Session-based auth** — Django's built-in session authentication is used rather than JWT. The `CSRF_COOKIE_HTTPONLY = False` setting allows the JS frontend to read the `csrftoken` cookie and include it as the `X-CSRFToken` header on every mutating request.

**Multi-vendor order splitting** — A single customer `Order` is split into one `ProducerSubOrder` per producer at checkout. Each sub-order tracks its own status, delivery date, subtotal, and payout independently. The parent order status rolls up automatically when all sub-orders reach the same state.

**AI service as a separate microservice** — The FastAPI AI service runs on port 8001 and is called via HTTP from Django views. This demonstrates a distributed service architecture. A full model registry supports upload, activate, and rollback without restarting the service.

**Food miles** — Calculated using the Haversine great-circle formula across 100+ postcodes covering Bristol (BS1-BS49), Bath, Gloucestershire, Somerset, and Wiltshire. A fuzzy fallback matches partial postcodes by sector then district before defaulting to 10 miles.

**5% commission** — Deducted automatically at order creation. `producer_payout = subtotal * 0.95`. Settlement records include a running tax-year total for producer accounting.

**Permissions layering** — Three custom DRF permission classes (`IsAuthenticatedAndProducer`, `IsAuthenticatedAndCustomer`, `IsAdminUserOrStaff`) act as the first gate. Each view then performs a second ownership check to prevent cross-user data access.

---

## Known limitations

- No real email or notification service — food safety alerts exist as data fields only
- Sandbox payment simulation only — no live Stripe integration
- No PDF export for settlement reports
- Food miles uses straight-line Haversine distance, not actual road distance
- Recommendation exposure data only populates after the AI `/recommend/` endpoint has been called at least once