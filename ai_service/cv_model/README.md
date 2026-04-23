# Computer Vision Extension

This folder adds a real image-based fruit and vegetable quality pipeline for the Bristol marketplace project.

## Files
- `prepare_dataset.py` splits the raw image dataset into train/val/test folders.
- `train_cv_model.py` trains a ResNet18 image classifier and writes metrics and plots.
- `predict_cv_model.py` loads the saved model and predicts a class for one image.

## Expected raw dataset layout
The source dataset should contain one folder per class, for example:
- `Apple_Healthy`
- `Apple_Rotten`
- `Banana_Healthy`
- `Banana_Rotten`
- `Carrot_Healthy`
- `Carrot_Rotten`

## Recommended workflow
1. Update the dataset paths inside `prepare_dataset.py` and `train_cv_model.py`.
2. Run `python ai_service/cv_model/prepare_dataset.py`
3. Install PyTorch:
   - `pip install torch torchvision pillow`
4. Run `python ai_service/cv_model/train_cv_model.py`
5. Review:
   - `ai_service/cv_model/cv_metrics.json`
   - `ai_service/cv_model/plots/cv_confusion_matrix.png`
   - `ai_service/cv_model/plots/cv_accuracy_curve.png`
   - `ai_service/cv_model/plots/cv_loss_curve.png`
6. Test prediction with `python ai_service/cv_model/predict_cv_model.py`

## Suggested report/demo points
- real image dataset usage
- transfer learning with ResNet18
- train/validation/test split
- accuracy, precision, recall, F1-score
- confusion matrix and class-level results
- how predictions can trigger discount or inventory actions
