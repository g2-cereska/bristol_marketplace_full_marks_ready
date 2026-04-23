# AI Evaluation Upgrade

This package now includes a stronger academic AI evaluation bundle for the produce quality component.

## What was added

- Synthetic tabular quality dataset (`data/quality_samples.csv`) derived from the case-study grading thresholds.
- Model comparison across three classifiers: Logistic Regression, SVM, and Random Forest.
- Metrics for each model: accuracy, precision, recall, F1-score, classification report, and confusion matrix.
- Visual explainability through feature-importance plots for interpretable models.
- Saved best model artifact: `ai_service/models/quality_random_forest.joblib`.
- Metrics JSON for the API: `ai_service/models/quality_metrics.json`.
- New API endpoint: `/quality-metrics`.

## Business linkage

- Grade A -> standard sale listing
- Grade B -> small discount and surplus prioritisation
- Grade C -> urgent discount or removal from premium listing

## Important note

This improves the AI evidence significantly, but it is still a **quality scoring model based on engineered features**, not a full image-based computer vision model trained on the Kaggle fruit/vegetable image dataset.
If the marker expects true computer vision, that still needs to be added separately.
