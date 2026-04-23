# Architecture Overview

## Services
- Django REST backend for marketplace operations
- FastAPI AI service for recommendation, forecasting, and quality grading
- PostgreSQL for persistent data in Docker mode

## Main DESD coverage
- producer and customer registration
- product catalogue and search
- cart and order creation
- multi-producer suborders
- settlement calculation
- admin dashboard

## Main AI coverage
- interaction-based recommendations
- weekly demand forecasting
- quality grading logic
- model upload endpoint
- explanation fields included in AI responses
