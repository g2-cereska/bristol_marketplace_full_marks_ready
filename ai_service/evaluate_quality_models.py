import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DOCS_DIR = ROOT / 'docs' / 'figures'
MODEL_DIR = ROOT / 'ai_service' / 'models'
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)


def label_rule(color, size, ripeness):
    if color < 65 or size < 70 or ripeness < 60:
        return 'C'
    if color < 75 or size < 80 or ripeness < 70:
        return 'B'
    return 'A'


def make_dataset(n=2400):
    produce_types = np.array(['apple', 'banana', 'tomato', 'cucumber', 'carrot', 'orange'])
    rows = []
    for _ in range(n):
        color = float(np.clip(RNG.normal(78, 15), 35, 100))
        size = float(np.clip(RNG.normal(82, 12), 40, 100))
        ripeness = float(np.clip(RNG.normal(76, 16), 30, 100))
        moisture_loss = float(np.clip(100 - ripeness + RNG.normal(0, 6), 0, 100))
        blemish_ratio = float(np.clip((100 - color) / 100 + RNG.normal(0, 0.05), 0, 1))
        density_score = float(np.clip((size + ripeness) / 2 + RNG.normal(0, 5), 0, 100))
        label = label_rule(color, size, ripeness)
        rows.append({
            'produce_type': RNG.choice(produce_types),
            'color': round(color, 2),
            'size': round(size, 2),
            'ripeness': round(ripeness, 2),
            'moisture_loss': round(moisture_loss, 2),
            'blemish_ratio': round(blemish_ratio, 3),
            'density_score': round(density_score, 2),
            'grade': label,
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / 'quality_samples.csv', index=False)
    return df


def evaluate_model(name, estimator, X_train, X_test, y_train, y_test, feature_names):
    estimator.fit(X_train, y_train)
    preds = estimator.predict(X_test)
    labels = ['A', 'B', 'C']
    metrics = {
        'accuracy': round(float(accuracy_score(y_test, preds)), 4),
        'precision_macro': round(float(precision_score(y_test, preds, average='macro', zero_division=0)), 4),
        'recall_macro': round(float(recall_score(y_test, preds, average='macro', zero_division=0)), 4),
        'f1_macro': round(float(f1_score(y_test, preds, average='macro', zero_division=0)), 4),
        'classification_report': classification_report(y_test, preds, output_dict=True, zero_division=0),
    }
    cm = confusion_matrix(y_test, preds, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax)
    ax.set_title(f'{name} Confusion Matrix')
    fig.tight_layout()
    fig.savefig(DOCS_DIR / f'{name.lower().replace(" ", "_")}_confusion_matrix.png', dpi=180)
    plt.close(fig)

    importances = None
    feature_plot = None
    model_obj = estimator
    if isinstance(estimator, Pipeline):
        model_obj = estimator[-1]
    if hasattr(model_obj, 'feature_importances_'):
        importances = model_obj.feature_importances_
    elif hasattr(model_obj, 'coef_'):
        importances = np.mean(np.abs(model_obj.coef_), axis=0)
    if importances is not None:
        order = np.argsort(importances)[::-1]
        ranked = [
            {'feature': feature_names[idx], 'importance': round(float(importances[idx]), 4)}
            for idx in order
        ]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(range(len(feature_names)), [importances[idx] for idx in order])
        ax.set_xticks(range(len(feature_names)))
        ax.set_xticklabels([feature_names[idx] for idx in order], rotation=45, ha='right')
        ax.set_ylabel('Importance')
        ax.set_title(f'{name} Feature Importance')
        fig.tight_layout()
        feature_plot = DOCS_DIR / f'{name.lower().replace(" ", "_")}_feature_importance.png'
        fig.savefig(feature_plot, dpi=180)
        plt.close(fig)
        metrics['feature_importance'] = ranked
    return metrics, estimator


def main():
    df = make_dataset()
    feature_cols = ['color', 'size', 'ripeness', 'moisture_loss', 'blemish_ratio', 'density_score']
    X = df[feature_cols]
    y = df['grade']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    models = {
        'Logistic Regression': Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression(max_iter=1200))]),
        'SVM': Pipeline([('scaler', StandardScaler()), ('model', SVC(kernel='rbf', probability=True))]),
        'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42),
    }
    all_metrics = {
        'dataset': {
            'rows': int(len(df)),
            'features': feature_cols,
            'class_distribution': df['grade'].value_counts().sort_index().to_dict(),
            'produce_types': sorted(df['produce_type'].unique().tolist()),
        },
        'models': {},
    }
    best_name = None
    best_score = -1
    best_model = None
    for name, model in models.items():
        metrics, trained = evaluate_model(name, model, X_train, X_test, y_train, y_test, feature_cols)
        all_metrics['models'][name] = metrics
        if metrics['f1_macro'] > best_score:
            best_name = name
            best_score = metrics['f1_macro']
            best_model = trained
    all_metrics['best_model'] = {'name': best_name, 'selection_metric': 'f1_macro', 'score': best_score}

    pd.DataFrame([
        {
            'model': name,
            'accuracy': values['accuracy'],
            'precision_macro': values['precision_macro'],
            'recall_macro': values['recall_macro'],
            'f1_macro': values['f1_macro'],
        }
        for name, values in all_metrics['models'].items()
    ]).to_csv(DOCS_DIR / 'model_comparison.csv', index=False)

    comparison = pd.read_csv(DOCS_DIR / 'model_comparison.csv')
    fig, ax = plt.subplots(figsize=(8, 5))
    for metric in ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']:
        ax.plot(comparison['model'], comparison[metric], marker='o', label=metric)
    ax.set_ylim(0.7, 1.01)
    ax.set_ylabel('Score')
    ax.set_title('Quality Model Comparison')
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS_DIR / 'model_comparison.png', dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for grade in ['A', 'B', 'C']:
        subset = df[df['grade'] == grade]
        ax.scatter(subset['color'], subset['ripeness'], label=grade, alpha=0.4)
    ax.set_xlabel('Color score')
    ax.set_ylabel('Ripeness score')
    ax.set_title('Synthetic quality dataset distribution')
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS_DIR / 'quality_dataset_distribution.png', dpi=180)
    plt.close(fig)

    joblib.dump(best_model, MODEL_DIR / 'quality_random_forest.joblib')
    (MODEL_DIR / 'quality_metrics.json').write_text(json.dumps(all_metrics, indent=2))


if __name__ == '__main__':
    main()
