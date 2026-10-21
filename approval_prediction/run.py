"""Run with python -B -m approval_prediction.run [--output PATH] [--audit-only]."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
os.environ.setdefault('TF_DETERMINISTIC_OPS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'.cache/approval_matplotlib'))

from .config import ROOT, OUTPUT, TARGET_VERSION
from .data import build_target, build_features


def source_hashes():
    paths = sorted((ROOT/'data/raw').glob('*.xlsx')) + sorted((ROOT/'data/processed').glob('*.csv'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    if not __debug__:
        raise RuntimeError('Do not use -O; assertions are required')
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--audit-only', action='store_true')
    parser.add_argument('--clean', action='store_true', help='Replace generated module outputs and rebuild from RAW')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT/'data' in out.parents or out == ROOT/'data':
        raise ValueError('Output must not overwrite source data or the project root')
    if out.exists() and any(out.iterdir()):
        if not args.clean:
            raise ValueError('Output is not empty. Use --clean to rebuild generated module outputs.')
        cache = (ROOT/'.cache').resolve()
        if out != OUTPUT.resolve() and cache not in out.parents:
            raise ValueError('Clean supports only module output or workspace cache children')
        # Each resolved file must be inside the explicitly verified generated root.
        for path in out.rglob('*'):
            if path.is_file():
                if out not in path.resolve().parents:
                    raise ValueError('Refusing cleanup outside the generated output root')
                path.unlink()
    for folder in ['tables', 'figures', 'models', 'docs']:
        (out/folder).mkdir(parents=True, exist_ok=True)
    before = source_hashes()
    sales, _, counts = build_target(out)
    dataset = build_features(sales)
    dataset.to_csv(out/'tables/modeling_dataset.csv', index=False)
    (out/'tables/grain_audit.json').write_text(json.dumps(counts, indent=2), encoding='utf-8')
    print(json.dumps(counts), flush=True)
    print(dataset.groupby(['split', 'chot_don']).size().to_string(), flush=True)
    from .documentation import write_audit_docs
    write_audit_docs(out, dataset)
    if args.audit_only:
        return
    from .modeling import train_and_evaluate
    from .evaluation import export_evaluation
    from .documentation import write_results
    from .validate import validate_outputs
    comparison, predictions, importance, frozen = train_and_evaluate(dataset, out)
    export_evaluation(out, dataset, comparison, predictions, importance, frozen)
    write_results(out, comparison, frozen)
    assert before == source_hashes(), 'Input files were modified'
    versions = {line.split('==')[0]: importlib.metadata.version(line.split('==')[0])
                for line in (ROOT/'requirements.txt').read_text().splitlines() if line.strip() and not line.startswith('#')}
    manifest = dict(python=platform.python_version(), packages=versions, seed=42, target_version=TARGET_VERSION,
                    source_sha256=before, source_unchanged=True,
                    code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))})
    (out/'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    manifest['dataset_sha256'] = hashlib.sha256((out/'tables/modeling_dataset.csv').read_bytes()).hexdigest()
    manifest['run_id'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest['git_revision'] = None  # Distribution contains no Git metadata.
    (out/'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    from .schema import write_model_schema
    write_model_schema(out)
    validate_outputs(out)
    print(comparison[['model','validation_macro_f1','test_macro_f1','test_roc_auc','threshold']].to_string(index=False), flush=True)
    print('PASS: model artifacts and schema verified', flush=True)


if __name__ == '__main__':
    main()
