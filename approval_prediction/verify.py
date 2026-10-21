"""Compare two independently trained bundles, including saved-model inference."""
import os
import json
from pathlib import Path
import tempfile
import subprocess
import sys
from .config import ROOT, OUTPUT, FEATURES
from .registry import MODEL_REGISTRY, PREPROCESSOR_ARTIFACT


def verify_reproducibility() -> dict:
    cache = ROOT/'.cache'
    cache.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', PYTHONWARNINGS='error::FutureWarning')
    compared = []
    with tempfile.TemporaryDirectory(prefix='model_verify_', dir=cache) as directory:
        other = Path(directory).resolve()
        if other.parent != cache.resolve():
            raise ValueError('Verification directory must be a workspace cache child')
        result = subprocess.run([sys.executable,'-B','-m','approval_prediction.run','--output',str(other)],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        (ROOT/'outputs/logs/model_reproduction.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Independent training failed; see outputs/logs/model_reproduction.log')
        for folder in ['tables','figures','docs']:
            first = {p.name for p in (OUTPUT/folder).iterdir() if p.is_file()}
            second = {p.name for p in (other/folder).iterdir() if p.is_file()}
            if first != second:
                raise AssertionError(f'Artifact inventory differs: {folder}')
            for name in sorted(first):
                if (OUTPUT/folder/name).read_bytes() != (other/folder/name).read_bytes():
                    raise AssertionError(f'Non-deterministic artifact: {folder}/{name}')
                compared.append(f'{folder}/{name}')
        for name in ['models/selection.json', PREPROCESSOR_ARTIFACT] + [m['artifact'] for m in MODEL_REGISTRY.values() if m['type'] == 'machine_learning']:
            if (OUTPUT/name).read_bytes() != (other/name).read_bytes():
                raise AssertionError(f'Serialized model differs: {name}')
        os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS','0')
        import tensorflow as tf
        import numpy as np
        import pandas as pd
        import joblib
        a = tf.keras.models.load_model(OUTPUT/'models/mlp.keras', compile=False)
        b = tf.keras.models.load_model(other/'models/mlp.keras', compile=False)
        if len(a.get_weights()) != len(b.get_weights()):
            raise AssertionError('MLP architecture differs')
        for wa, wb in zip(a.get_weights(),b.get_weights()):
            np.testing.assert_array_equal(wa,wb)
        dataset = pd.read_csv(OUTPUT/'tables/modeling_dataset.csv')
        test = dataset[dataset.split.eq('test')]
        prep = joblib.load(OUTPUT/'models/preprocessor.joblib')
        prediction = np.asarray(a(prep.transform(test[FEATURES]).astype('float32'),training=False)).ravel()
        expected = pd.read_csv(OUTPUT/'tables/transaction_approval_predictions.csv').prob_mlp
        np.testing.assert_allclose(prediction,expected,rtol=1e-6,atol=1e-7)
    report = dict(status='PASS',fresh_output_rerun=True,exact_reproduced_artifacts=compared,
                  saved_mlp_weights_equal=True,saved_mlp_predictions_equal=True,frozen_selection_equal=True)
    (OUTPUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    from verify_project import main
    main()
