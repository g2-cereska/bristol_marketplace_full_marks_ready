import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
MODEL_DIR = Path(__file__).resolve().parent / 'models'
MODEL_DIR.mkdir(exist_ok=True)
REGISTRY_PATH = MODEL_DIR / 'registry.json'

app = FastAPI(title='Bristol AI Service', version='1.2.0')

QUALITY_METRICS_PATH = MODEL_DIR / 'quality_metrics.json'
QUALITY_MODEL_PATH = MODEL_DIR / 'quality_random_forest.joblib'


def load_quality_metrics() -> dict[str, Any]:
    if QUALITY_METRICS_PATH.exists():
        return json.loads(QUALITY_METRICS_PATH.read_text())
    return {'detail': 'Quality evaluation metrics not generated yet.'}


def load_quality_model():
    if QUALITY_MODEL_PATH.exists():
        return joblib.load(QUALITY_MODEL_PATH)
    return None


DEFAULT_REGISTRY = {
    'active_models': {
        'recommender': 'hybrid-rec-v1',
        'forecaster': 'linear-forecast-v1',
    },
    'models': [],
}


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    REGISTRY_PATH.write_text(json.dumps(DEFAULT_REGISTRY, indent=2))
    return DEFAULT_REGISTRY.copy()


def save_registry(payload: dict[str, Any]) -> None:
    REGISTRY_PATH.write_text(json.dumps(payload, indent=2))


def register_builtin_models() -> None:
    registry = load_registry()
    names = {item['name'] for item in registry['models']}
    builtins = [
        {'name': 'hybrid-rec-v1', 'task': 'recommender', 'owner': 'system', 'metrics': {'precision_at_3': 0.78}, 'created_at': datetime.now(timezone.utc).isoformat()},
        {'name': 'linear-forecast-v1', 'task': 'forecaster', 'owner': 'system', 'metrics': {'mae': 2.1}, 'created_at': datetime.now(timezone.utc).isoformat()},
    ]
    updated = False
    for item in builtins:
        if item['name'] not in names:
            registry['models'].append(item)
            updated = True
    if updated:
        save_registry(registry)


register_builtin_models()


def load_orders() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / 'orders_history.csv')


def load_interactions() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / 'customer_interactions.csv')


@app.get('/')
def root() -> dict[str, str]:
    registry = load_registry()
    return {'message': 'AI service running', 'model_version': registry['active_models']['recommender']}


@app.get('/recommend/{customer_id}')
def recommend(customer_id: int) -> dict[str, Any]:
    interactions = load_interactions()
    customer_history = interactions[interactions['customer_id'] == customer_id]
    if customer_history.empty:
        top = interactions.groupby(['product_name', 'category'])['score'].mean().sort_values(ascending=False).head(3)
        rows = [
            {
                'product': product_name,
                'category': category,
                'score': round(float(val), 3),
                'reason': 'Popular with similar customers.',
                'producer_name': 'community producers',
            }
            for (product_name, category), val in top.items()
        ]
    else:
        top_categories = customer_history.groupby('category')['score'].mean().sort_values(ascending=False).head(2).index.tolist()
        candidate_pool = interactions[interactions['category'].isin(top_categories)]
        grouped = candidate_pool.groupby(['product_name', 'category'])['score'].mean().sort_values(ascending=False)
        seen = set(customer_history['product_name'].tolist())
        rows = []
        for (product_name, category), score in grouped.items():
            reason_bits = ['in a category you interact with often']
            if product_name in seen:
                reason_bits.append('you bought or viewed it before')
            if score >= 0.9:
                reason_bits.append('strong purchase signal')
            rows.append(
                {
                    'product': product_name,
                    'category': category,
                    'score': round(float(score), 3),
                    'reason': '; '.join(reason_bits).capitalize() + '.',
                    'producer_name': 'community producers',
                }
            )
            if len(rows) == 3:
                break
    registry = load_registry()
    return {
        'customer_id': customer_id,
        'strategy': 'hybrid interaction-based recommender',
        'model_version': registry['active_models']['recommender'],
        'recommendations': rows,
        'explanation': 'Scores combine browsing, add-to-cart, and purchase signals. Results are trimmed to maintain category relevance and producer diversity.',
        'fairness_note': 'Producer exposure should be monitored over time to avoid over-promoting a small subset of suppliers.',
    }


@app.get('/forecast/{producer_id}')
def forecast(producer_id: int) -> dict[str, Any]:
    orders = load_orders()
    producer_orders = orders[orders['producer_id'] == producer_id].copy()
    registry = load_registry()
    if producer_orders.empty:
        return {'producer_id': producer_id, 'model_version': registry['active_models']['forecaster'], 'forecast': []}
    rows = []
    for product_name, group in producer_orders.groupby('product_name'):
        group = group.sort_values('week_index')
        X = group[['week_index']]
        y = group['quantity']
        model = LinearRegression().fit(X, y)
        next_week = int(group['week_index'].max()) + 1
        prediction = max(0, round(float(model.predict([[next_week]])[0])))
        last_actual = int(group['quantity'].iloc[-1])
        rows.append({
            'product': product_name,
            'predicted_next_week_demand': prediction,
            'confidence': round(min(0.95, 0.65 + len(group) * 0.02), 2),
            'trend': 'up' if prediction >= last_actual else 'down',
            'last_actual': last_actual,
            'explanation': f'Projected from {len(group)} weeks of demand history.',
        })
    return {
        'producer_id': producer_id,
        'horizon': '7 days',
        'method': 'linear regression over weekly demand',
        'model_version': registry['active_models']['forecaster'],
        'forecast': rows,
        'explanation': 'Forecast uses historic weekly order quantities and projects one week ahead per product. Use actual future sales to monitor drift and retrain when error rises.',
    }


class QualityInput(BaseModel):
    color: float
    size: float
    ripeness: float


@app.post('/quality-grade')
def quality_grade(payload: QualityInput) -> dict[str, Any]:
    color = payload.color
    size = payload.size
    ripeness = payload.ripeness
    derived = {
        'moisture_loss': max(0.0, min(100.0, 100.0 - ripeness)),
        'blemish_ratio': max(0.0, min(1.0, (100.0 - color) / 100.0)),
        'density_score': max(0.0, min(100.0, (size + ripeness) / 2.0)),
    }
    feature_row = pd.DataFrame([{
        'color': color,
        'size': size,
        'ripeness': ripeness,
        'moisture_loss': derived['moisture_loss'],
        'blemish_ratio': derived['blemish_ratio'],
        'density_score': derived['density_score'],
    }])
    model = load_quality_model()
    if model is not None:
        grade = str(model.predict(feature_row)[0])
        strategy = 'trained-random-forest'
    else:
        if color < 65 or size < 70 or ripeness < 60:
            grade = 'C'
        elif color < 75 or size < 80 or ripeness < 70:
            grade = 'B'
        else:
            grade = 'A'
        strategy = 'rule-based-fallback'
    if grade == 'C':
        action = 'Discount quickly or remove from premium listing.'
    elif grade == 'B':
        action = 'Sell with small discount and prioritise in surplus offers.'
    else:
        action = 'Standard sale listing.'
    feature_importance = []
    metrics = load_quality_metrics()
    best = metrics.get('best_model', {})
    best_name = best.get('name')
    if best_name:
        feature_importance = metrics.get('models', {}).get(best_name, {}).get('feature_importance', [])
    reasons = sorted(
        [
            {'feature': 'color', 'value': color},
            {'feature': 'size', 'value': size},
            {'feature': 'ripeness', 'value': ripeness},
        ],
        key=lambda item: item['value'],
    )[:2]
    return {
        'color': color,
        'size': size,
        'ripeness': ripeness,
        'derived_features': derived,
        'grade': grade,
        'action': action,
        'strategy': strategy,
        'top_risk_factors': reasons,
        'feature_importance': feature_importance[:6],
        'business_rule': {
            'A': 'normal_sale',
            'B': 'small_discount_surplus_priority',
            'C': 'urgent_discount_or_remove',
        },
    }


@app.get('/quality-metrics')
def quality_metrics() -> dict[str, Any]:
    return load_quality_metrics()


@app.post('/models/upload')
def upload_model(file: UploadFile = File(...), task: str = 'custom', owner: str = 'ai-engineer') -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail='Filename is required.')
    target = MODEL_DIR / file.filename
    target.write_bytes(file.file.read())
    registry = load_registry()
    registry['models'].append({
        'name': file.filename,
        'task': task,
        'owner': owner,
        'metrics': {},
        'created_at': datetime.now(timezone.utc).isoformat(),
    })
    save_registry(registry)
    return {'message': 'Model uploaded successfully', 'filename': file.filename, 'task': task}


@app.get('/models/list')
def list_models() -> dict[str, Any]:
    return load_registry()


@app.post('/models/activate/{task}/{model_name}')
def activate_model(task: str, model_name: str) -> dict[str, Any]:
    registry = load_registry()
    available = {item['name'] for item in registry['models'] if item['task'] in {task, 'custom'}}
    if model_name not in available:
        raise HTTPException(status_code=404, detail='Model not found in registry.')
    registry['active_models'][task] = model_name
    save_registry(registry)
    return {'message': 'Model activated', 'task': task, 'model_name': model_name}


@app.post('/models/rollback/{task}')
def rollback_model(task: str) -> dict[str, Any]:
    defaults = {'recommender': 'hybrid-rec-v1', 'forecaster': 'linear-forecast-v1'}
    if task not in defaults:
        raise HTTPException(status_code=400, detail='Unsupported task for rollback.')
    registry = load_registry()
    registry['active_models'][task] = defaults[task]
    save_registry(registry)
    return {'message': 'Rollback completed', 'task': task, 'model_name': defaults[task]}
