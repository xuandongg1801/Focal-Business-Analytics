"""The four supported estimators and their trusted local artifact locations."""
MODEL_REGISTRY = {
    'logistic': {'display_name': 'Logistic Regression', 'type': 'machine_learning', 'artifact': 'models/logistic.joblib'},
    'random_forest': {'display_name': 'Random Forest', 'type': 'machine_learning', 'artifact': 'models/random_forest.joblib'},
    'xgboost': {'display_name': 'XGBoost', 'type': 'machine_learning', 'artifact': 'models/xgboost.joblib'},
    'mlp': {'display_name': 'MLP Neural Network', 'type': 'deep_learning', 'artifact': 'models/mlp.keras'},
}
PREPROCESSOR_ARTIFACT = 'models/preprocessor.joblib'
PREPROCESSING_VERSION = 'train_median_standard_scaler'
