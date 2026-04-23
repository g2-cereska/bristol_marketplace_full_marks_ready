from fastapi.testclient import TestClient

from ai_service.main import app

client = TestClient(app)


def test_recommend():
    response = client.get('/recommend/1')
    assert response.status_code == 200
    body = response.json()
    assert 'recommendations' in body
    assert body['model_version']


def test_quality_grade_returns_explainability():
    response = client.post('/quality-grade', json={'color': 70, 'size': 85, 'ripeness': 75})
    assert response.status_code == 200
    body = response.json()
    assert body['grade'] in {'A', 'B', 'C'}
    assert 'feature_importance' in body
    assert 'top_risk_factors' in body


def test_quality_metrics_endpoint():
    response = client.get('/quality-metrics')
    assert response.status_code == 200
    body = response.json()

    # Accept both cases:
    # 1. Metrics exist
    # 2. Metrics not generated yet (CI environment)

    if 'models' in body:
        # Full metrics available
        assert 'best_model' in body
    else:
        # No metrics yet
        assert 'detail' in body


def test_model_registry_list():
    response = client.get('/models/list')
    assert response.status_code == 200
    assert 'active_models' in response.json()
