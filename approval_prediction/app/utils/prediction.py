import logging
import numpy as np
import pandas as pd
from .data_loader import schema, metadata, ArtifactError, validate_bundle
from .model_loader import model, preprocessor
from approval_prediction.registry import MODEL_REGISTRY

def validate_features(frame, contract):
    if list(frame.columns) != contract['order'] or len(frame) == 0:
        raise ArtifactError('Feature schema hoặc thứ tự cột không khớp model.')
    for name in contract['features']:
        if not pd.api.types.is_numeric_dtype(frame[name]):
            raise ArtifactError('Feature phải có kiểu số theo schema.')
        values = frame[name].to_numpy(dtype=float)
        if np.isinf(values).any() or (name not in contract['nullable'] and np.isnan(values).any()):
            raise ArtifactError('Feature có giá trị thiếu hoặc vô cực không hợp lệ.')
    return frame.astype('float64')

def _predict_models(frame, names=None, *, tolerate_errors=False):
    validate_bundle()
    contract = schema()
    frame = validate_features(frame, contract)
    frozen = metadata()
    names = [frozen['selected_model']] if names is None else list(names)
    if not names or len(names) != len(set(names)) or not set(names) <= set(MODEL_REGISTRY):
        raise ArtifactError('Danh sách model phải thuộc bốn mô hình được hỗ trợ và không trùng.')
    prep = preprocessor()
    if list(prep.feature_names_in_) != contract['order']:
        raise ArtifactError('Preprocessor không khớp feature schema.')
    x = prep.transform(frame)
    result, errors = [], {}
    for name in names:
        try:
            estimator = model(name)
            p = np.asarray(estimator(x.astype('float32'), training=False)).ravel() if name == 'mlp' else estimator.predict_proba(x)[:,1]
            if len(p) != len(frame) or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
                raise ArtifactError('Model trả về xác suất không hợp lệ.')
            threshold = frozen['selection'][name]['threshold']
            for idx, prob in enumerate(p):
                result.append(dict(row=idx, model=name, probability=float(prob), prediction=int(prob>=threshold),
                                   predicted_class='WIN' if prob >= threshold else 'LOST', threshold=threshold))
        except Exception as exc:
            message = f"{MODEL_REGISTRY[name]['display_name']}: không thể chạy inference ({exc})."
            if not tolerate_errors:
                raise ArtifactError(message) from exc
            logging.getLogger(__name__).exception('Inference failed for %s',name)
            errors[name] = message
    columns = ['row','model','probability','prediction','predicted_class','threshold']
    return pd.DataFrame(result, columns=columns), errors


def predict(frame, names=None):
    """Strict batch API used by verification; any requested-model failure raises."""
    return _predict_models(frame, names)[0]


def compare_all_models(frame):
    """One shared transformation; return successful results and explicit model errors."""
    return _predict_models(frame, list(MODEL_REGISTRY), tolerate_errors=True)

