import requests
from django.conf import settings


def fetch_json(path: str) -> dict:
    response = requests.get(f"{settings.AI_SERVICE_URL}{path}", timeout=15)
    response.raise_for_status()
    return response.json()
