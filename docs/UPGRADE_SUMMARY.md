# Submission Upgrade Summary

## AI improvements
- Added confusion matrix, precision, recall, F1-score, and classification report outputs.
- Added three-model comparison and selected best model by macro F1-score.
- Added feature-importance based explainability.
- Added persisted trained model and metrics endpoint.

## DESD improvements
- Existing authentication, role separation, and order lifecycle were retained and highlighted with stronger tests.
- Code hygiene improved by removing `import *` in admin.
- Test coverage expanded for authentication and permissions flows.

## Remaining gap
- Full image-based CV training on the Kaggle dataset is still not implemented in this package.
