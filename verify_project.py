"""Final-state verification of local data, models, documentation and application."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import urllib.request
import warnings
from PIL import Image

sys.dont_write_bytecode = True
from run_pipeline import run_pipeline
from config import ROOT, PROC, TAB, FIG, LOG, PROCESSED_FILES, TABLE_FILES, FIGURE_FILES
from reporting import write_json
from release_checks import check_source, check_clean_tree, clean_runtime, environment, fingerprint, sanitize_log


def command(label, args, env_override=None):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1', PYTHONWARNINGS='error::FutureWarning')
    env.update(env_override or {})
    print(f'STAGE: {label}', flush=True)
    result = subprocess.run([sys.executable,'-B',*args],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    output = result.stdout + result.stderr
    (LOG/(label+'.log')).write_text(sanitize_log(output),encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{label} failed; see outputs/logs/{label}.log')
    return output


def tests():
    xml = ROOT/'.cache/pytest-results.xml'
    xml.parent.mkdir(parents=True, exist_ok=True)
    output = command('unit_tests', ['-m','pytest','tests','approval_prediction/test_approval.py',
        'approval_prediction/app/test_app.py','-p','no:cacheprovider','-W','error::FutureWarning',
        '-q',f'--junitxml={xml}'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    counts = {key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    collected = sum(len(s.findall('testcase')) for s in suites)
    warning_count = re.search(r'(\d+) warnings?', output.splitlines()[-1])
    result = dict(collected=collected, run=collected,
        passed=collected-counts['failures']-counts['errors']-counts['skipped'],
        subtests_passed=counts['tests']-collected, warnings=int(warning_count[1]) if warning_count else 0,
        failed=counts['failures']+counts['errors'], skipped=counts['skipped'],
        future_warning_policy='error', runner='pytest',
        summary=output.strip().splitlines()[-1])
    if result['failed'] or result['skipped']:
        raise AssertionError('Tests failed/skipped; see outputs/logs/unit_tests.log')
    return result


def diagnostic_categories():
    text = '\n'.join(p.read_text(encoding='utf-8') for p in LOG.glob('*.log'))
    patterns = {'tensorflow_cpu_on_native_windows':'TensorFlow GPU support is not available',
                'keras_internal_deprecation':'tf.reset_default_graph',
                'streamlit_bare_test_context':'missing ScriptRunContext',
                'streamlit_bare_cache':'No runtime found',
                'future_warning':'FutureWarning'}
    return {name:text.count(pattern) for name,pattern in patterns.items()}


def artifact_hashes() -> dict[str,str]:
    files = []
    for folder, expected in [(PROC,PROCESSED_FILES),(TAB,TABLE_FILES),(FIG,FIGURE_FILES)]:
        actual = {p.name for p in folder.iterdir() if p.is_file()}
        if actual != set(expected):
            raise AssertionError(f'{folder.name}: missing={set(expected)-actual}; stale={actual-set(expected)}')
        files.extend(folder/name for name in expected)
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def app_server_smoke() -> dict:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    with (LOG/'streamlit_server.log').open('w',encoding='utf-8') as log:
        process = subprocess.Popen([sys.executable,'-B','-m','streamlit','run',str(ROOT/'approval_prediction/app/app.py'),
            '--server.headless=true',f'--server.port={port}','--server.address=127.0.0.1'],
            cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+30
            while time.monotonic()<deadline:
                if process.poll() is not None:
                    raise RuntimeError('Streamlit process exited; see streamlit_server.log')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                        if response.read()==b'ok':
                            return dict(status='PASS',health='ok',pages='Covered by AppFlowTests')
                except (OSError,TimeoutError):
                    time.sleep(.3)
            raise RuntimeError('Streamlit health timeout')
        finally:
            process.terminate()
            process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--check-only', action='store_true', help='Validate existing local artifacts without retraining or rewriting docs')
    parser.add_argument('--pandas22-path', type=Path, help='Isolated pandas 2.2 package directory for warning-sensitive data tests')
    args = parser.parse_args()
    LOG.mkdir(parents=True,exist_ok=True)
    os.environ.update(PYTHONWARNINGS='error::FutureWarning', PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR=str(ROOT/'.cache/matplotlib'))
    warnings.simplefilter('error', FutureWarning)
    started = datetime.now(timezone.utc).isoformat()
    result = dict(status='RUNNING', started_at=started, mode='snapshot_check' if args.check_only else 'full')
    evidence = LOG/'snapshot_check.json' if args.check_only else LOG/'verification.json'
    write_json(evidence, result)
    if not args.check_only:
        write_json(LOG/'final_handoff.json', dict(status='RUNNING', started_at=started))
    try:
        result['environment'] = environment()
        command('dependencies',['-m','pip','check'])
        result['dependencies'] = 'PASS'
        if args.check_only:
            verified = json.loads((LOG/'verification.json').read_text(encoding='utf-8'))
            if verified['status'] != 'PASS' or verified['source_sha256'] != fingerprint(source_only=True):
                raise AssertionError('Local source differs from fully verified state')
            if verified['artifact_sha256'] != artifact_hashes():
                raise AssertionError('Local data artifacts differ from verified state')
        else:
            result['pipeline'] = run_pipeline(verbose=False)
            command('model_training',['-m','approval_prediction.run','--clean'])
            first = artifact_hashes()
            run_pipeline(verbose=False)
            second = artifact_hashes()
            if first != second:
                raise AssertionError('Pipeline artifacts differ between two runs')
            result['pipeline_reproducibility'] = 'PASS'
            result['artifact_count'] = len(second)
            result['artifact_sha256'] = second
            from approval_prediction.verify import verify_reproducibility
            result['model_reproducibility'] = verify_reproducibility()
            command('technical_documentation',['scripts/write_documentation.py'])
        # All code/docs/model generation precedes the final test run.
        from approval_prediction.app.utils.data_loader import validate_bundle
        validate_bundle()
        result['artifact_schema'] = 'PASS'
        for name in FIGURE_FILES:
            with Image.open(FIG/name) as figure:
                figure.verify()
        command('imports',['scripts/check_imports.py'])
        result['imports'] = 'PASS'
        result.update(check_source())
        tested_sources = fingerprint(source_only=True)
        result['tests'] = tests()
        if args.pandas22_path:
            location = args.pandas22_path.resolve()
            output = command('pandas22_tests',['-m','unittest','discover','-s','tests','-v'],{'PYTHONPATH':str(location)})
            count = int(re.search(r'Ran (\d+) tests',output)[1])
            version = command('pandas22_version',['-c','import pandas; print(pandas.__version__)'],{'PYTHONPATH':str(location)}).strip()
            if version != '2.2.3':
                raise AssertionError('Compatibility run did not use pandas 2.2.3')
            result['pandas22_compatibility'] = dict(status='PASS', pandas=version, tests=count, future_warning_policy='error')
        result['app_server'] = app_server_smoke()
        if tested_sources != fingerprint(source_only=True):
            raise AssertionError('Source/docs changed during final tests')
        result['source_sha256'] = tested_sources
        result['diagnostics'] = diagnostic_categories()
        result['runtime_removed'] = clean_runtime()
        result['hygiene'] = check_clean_tree()
        result.update(check_source())
        result['latest_input_modified_at'] = datetime.fromtimestamp(max((ROOT/name).stat().st_mtime for name in tested_sources),timezone.utc).isoformat()
        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        result['status'] = 'PASS'
    except Exception as exc:
        result.update(status='FAIL', error=sanitize_log(str(exc)), completed_at=datetime.now(timezone.utc).isoformat())
        write_json(evidence,result)
        raise
    write_json(evidence,result)
    if not args.check_only:
        write_json(LOG/'final_handoff.json',dict(status='PASS', generated_at=result['completed_at'],
            verification='outputs/logs/verification.json', verification_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
            tests=result['tests'], environment=result['environment'], hygiene=result['hygiene']))
    print(json.dumps({k:v for k,v in result.items() if k not in {'source_sha256','artifact_sha256','model_reproducibility','runtime_removed'}},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
