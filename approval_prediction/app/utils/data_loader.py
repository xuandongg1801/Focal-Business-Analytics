"""Cache by file identity; reject mixed or stale bundles before showing results."""
import json
import importlib.metadata
import streamlit as st
import pandas as pd
from approval_prediction.schema import sha256
from approval_prediction.config import ROOT, TARGET_VERSION, validate_feature_names
from approval_prediction.registry import MODEL_REGISTRY, PREPROCESSOR_ARTIFACT, PREPROCESSING_VERSION
from .paths import OUTPUT, TABLES, MODELS, SCHEMA

class ArtifactError(RuntimeError): pass

def stamp(path):
    if not path.is_file():
        if path.parent == MODELS:
            raise ArtifactError('Không tìm thấy model artifact. Hãy chạy pipeline training trước. Nếu đã có model, chạy python -m approval_prediction.schema để tạo schema.')
        raise ArtifactError(f'Không tìm thấy output {path.name}. Hãy chạy pipeline training trước.')
    info = path.stat()
    return (str(path), info.st_mtime_ns, info.st_size)

@st.cache_data(show_spinner=False)
def _json(identity):
    from pathlib import Path
    return json.loads(Path(identity[0]).read_text(encoding='utf-8'))

def metadata(): return _json(stamp(MODELS/'selection.json'))
def schema(): return _json(stamp(SCHEMA))

@st.cache_data(show_spinner=False)
def _csv(identity):
    return pd.read_csv(identity[0]).fillna({'customer_id': ''})

def table(name):
    if '/' in name or '\\' in name or '..' in name: raise ArtifactError('Tên bảng không hợp lệ.')
    return _csv(stamp(TABLES/name))

@st.cache_data(show_spinner=False)
def _check_bundle(identities, contract):
    for path, expected in identities:
        from pathlib import Path
        if sha256(Path(path[0])) != expected:
            raise ArtifactError('Model, dữ liệu hoặc output đã thay đổi. Hãy hoàn tất pipeline và tạo lại model_schema.json trước khi demo.')
    selected = metadata()
    if selected['features'] != contract['features'] or selected['selected_model'] != contract['selected_model']:
        raise ArtifactError('Model metadata không khớp schema.')
    try:
        validate_feature_names(contract['features'])
    except ValueError as exc:
        raise ArtifactError(str(exc)) from exc
    if contract['target_version'] != TARGET_VERSION or selected['target_version'] != TARGET_VERSION:
        raise ArtifactError('Target contract không khớp rule WIN/LOST.')
    if set(contract['models']) != set(MODEL_REGISTRY) or set(selected['selection']) != set(MODEL_REGISTRY):
        raise ArtifactError('Bundle phải có đúng bốn mô hình.')
    if set(contract['thresholds']) != set(MODEL_REGISTRY) or contract['selected_model'] not in MODEL_REGISTRY:
        raise ArtifactError('Model selection hoặc thresholds không hợp lệ.')
    for name, expected in MODEL_REGISTRY.items():
        info = contract['models'][name]
        threshold = selected['selection'][name]['threshold']
        if (not 0 <= threshold <= 1 or info['decision_threshold'] != threshold
            or contract['thresholds'][name] != threshold
            or any(info[key] != value for key, value in expected.items())
            or info['feature_schema'] != contract['features']
            or info['preprocessing_version'] != PREPROCESSING_VERSION
            or info['preprocessing_artifact'] != PREPROCESSOR_ARTIFACT
            or info['preprocessing_sha256'] != contract['artifact_sha256'][PREPROCESSOR_ARTIFACT]
            or info['artifact_sha256'] != contract['artifact_sha256'][expected['artifact']]
            or info['validation_metrics'] != selected['selection'][name]
            or info['training_cutoff'] != contract['date_ranges']['train']['end']
            or info['model_version'] != contract['run_id']):
            raise ArtifactError('Metadata từng model không khớp bundle.')
    return True

def validate_bundle():
    contract = schema()
    for package, expected in contract['runtime_versions'].items():
        if importlib.metadata.version(package) != expected:
            raise ArtifactError(f'Runtime {package} không khớp model. Cài requirements.txt rồi train lại artifacts.')
    pairs = [(stamp(OUTPUT/name), digest) for name,digest in contract['artifact_sha256'].items()]
    pairs += [(stamp(ROOT/name.replace('\\', '/')), digest) for name,digest in contract['source_sha256'].items()]
    pairs += [(stamp(ROOT/name), digest) for name, digest in contract['implementation_sha256'].items()]
    return _check_bundle(tuple(pairs), contract)

def history():
    data = table('target_audit.csv')
    return data[data.include.eq(True)].copy()

@st.cache_data(show_spinner=False)
def _customer_codes(identity):
    from approval_prediction.data import private_id
    data = pd.read_csv(identity[0], usecols=['ma_khach', 'la_don_ban_hang'])
    codes = data.loc[data.la_don_ban_hang.eq(True), 'ma_khach'].dropna().unique()
    return {private_id(code, 'C_'): str(code) for code in codes}

def customer_codes(): return _customer_codes(stamp(ROOT/'data/processed/fact_order_header.csv'))

@st.cache_data(show_spinner=False)
def _markets(identity):
    from approval_prediction.data import private_id
    data = pd.read_csv(identity[0], usecols=['ma_khach_hang', 'thi_truong'])
    return {private_id(r.ma_khach_hang, 'C_'): r.thi_truong for r in data.itertuples() if pd.notna(r.ma_khach_hang)}

def markets(): return _markets(stamp(ROOT/'data/processed/dim_customer.csv'))

