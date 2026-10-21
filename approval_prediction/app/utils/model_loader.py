"""Load only a requested local, trusted model; never train in the app."""
import os
import streamlit as st
from approval_prediction.config import ROOT
from approval_prediction.registry import MODEL_REGISTRY, PREPROCESSOR_ARTIFACT
from .paths import OUTPUT
from .data_loader import stamp, ArtifactError

@st.cache_resource(show_spinner=False)
def _load(identity, keras=False):
    try:
        if keras:
            os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.cache/approval_matplotlib'))
            os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
            import tensorflow as tf
            return tf.keras.models.load_model(identity[0], compile=False)
        import joblib
        return joblib.load(identity[0])
    except Exception as exc:
        raise ArtifactError('Không thể đọc model artifact. Kiểm tra dependency và phiên bản trong run_manifest.json.') from exc

def preprocessor(): return _load(stamp(OUTPUT/PREPROCESSOR_ARTIFACT))
def model(name):
    if name not in MODEL_REGISTRY:
        raise ArtifactError('Model chưa được hỗ trợ trong bản demo này.')
    info = MODEL_REGISTRY[name]
    return _load(stamp(OUTPUT/info['artifact']), info['type'] == 'deep_learning')
