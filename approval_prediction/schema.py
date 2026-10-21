"""Export a verifiable inference contract from a completed, real training run."""
import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from .config import FEATURES, OUTPUT, ROOT, FEATURE_DOMAINS
from .data import build_features
from .registry import MODEL_REGISTRY, PREPROCESSOR_ARTIFACT, PREPROCESSING_VERSION


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_model_schema(out=OUTPUT):
    """No training: verify shared feature parity, then bind the existing artifacts."""
    selection = json.loads((out/'models/selection.json').read_text(encoding='utf-8'))
    dataset = pd.read_csv(out/'tables/modeling_dataset.csv').fillna({'customer_id': ''})
    history = pd.read_csv(out/'tables/target_audit.csv').fillna({'customer_id': ''})
    rebuilt = build_features(history[history.include.eq(True)]).set_index('order_id')
    existing = dataset.set_index('order_id')
    if not existing.index.is_unique or set(existing.index) != set(rebuilt.index):
        raise ValueError('Modeling rows differ from reconciled target population')
    np.testing.assert_allclose(rebuilt.loc[existing.index, FEATURES], existing[FEATURES], equal_nan=True, atol=1e-12)
    prep = joblib.load(out/'models/preprocessor.joblib')
    if list(prep.feature_names_in_) != FEATURES or selection['features'] != FEATURES:
        raise ValueError('Feature contract differs from saved preprocessor')
    # A stale source snapshot must not be paired with trained models.
    manifest = json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['source_sha256'].items():
        if sha256(ROOT/name.replace('\\', '/')) != digest:
            raise ValueError('Source has changed; regenerate training outputs before preparing the app')
    model = selection['selected_model']
    periods = {split: dict(start=part.order_date.min(), end=part.order_date.max(), samples=len(part))
               for split, part in dataset.groupby('split')}
    artifacts = sorted(p for folder in ['tables', 'models'] for p in (out/folder).iterdir()
                       if p.is_file() and p.name != 'model_schema.json')
    schema = dict(schema_version=2, run_id=manifest['run_id'], runtime_versions=manifest['packages'],
        dataset_sha256=manifest['dataset_sha256'], git_revision=manifest['git_revision'], features=FEATURES,
        dtype={name: 'float64' for name in FEATURES}, order=FEATURES,
        feature_domains={f: dict(domain=FEATURE_DOMAINS[f][0], unit=FEATURE_DOMAINS[f][1]) for f in FEATURES},
        numerical=FEATURES, categorical=[], nullable=['recency_months'],
        date_ranges=periods, selected_model=model,
        threshold=selection['selection'][model]['threshold'],
        thresholds={n: v['threshold'] for n,v in selection['selection'].items()},
        selection_metric=selection['selection_metric'], target_version=selection['target_version'],
        history_policy='Strictly earlier calendar months; sales arrivals regardless of WIN/LOST',
        target_definition={'positive': 'WIN', 'negative': 'LOST', 'grain': 'one order',
            'implementation_sha256': sha256(ROOT/'approval_prediction/target.py')},
        models={name: dict(info, feature_schema=FEATURES, model_version=manifest['run_id'],
            preprocessing_artifact=PREPROCESSOR_ARTIFACT, preprocessing_version=PREPROCESSING_VERSION,
            preprocessing_sha256=sha256(out/PREPROCESSOR_ARTIFACT), training_cutoff=periods['train']['end'],
            validation_metrics=selection['selection'][name], decision_threshold=selection['selection'][name]['threshold'],
            artifact_sha256=sha256(out/info['artifact'])) for name, info in MODEL_REGISTRY.items()},
        implementation_sha256={f'approval_prediction/{name}': digest for name, digest in manifest['code_sha256'].items()},
        shared_feature_parity_rows=len(dataset),
        feature_implementation_sha256=sha256(ROOT/'approval_prediction/data.py'),
        artifact_sha256={p.relative_to(out).as_posix(): sha256(p) for p in artifacts},
        source_sha256=manifest['source_sha256'],
        evaluation=pd.read_csv(out/'tables/model_comparison.csv').set_index('model').loc[model].to_dict())
    (out/'models/model_schema.json').write_text(json.dumps(schema, indent=2), encoding='utf-8')
    return schema


if __name__ == '__main__':
    schema = write_model_schema()
    print(f"Schema verified: {schema['shared_feature_parity_rows']} rows; {schema['selected_model']}; threshold={schema['threshold']:.2f}")
