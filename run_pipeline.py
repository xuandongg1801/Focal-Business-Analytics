"""Execute the six-stage pipeline with one current log per stage."""
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from config import ROOT, LOG, STAGES


def run_pipeline(verbose: bool = True) -> dict[str, str]:
    if not __debug__:
        raise RuntimeError('Do not use Python -O: data validation assertions must run')
    LOG.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg', OMP_NUM_THREADS='1')
    statuses = {}
    for stage in STAGES:
        result = subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/f'{stage}.py')],
                                cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        output = result.stdout + result.stderr
        (LOG/f'{stage}.log').write_text(output, encoding='utf-8')
        if result.returncode:
            print(output)
            raise RuntimeError(f'{stage} failed: see outputs/logs/{stage}.log')
        statuses[stage] = 'PASS'
        if verbose:
            print(output, end='')
            print(f'{stage}: PASS', flush=True)
    return statuses


if __name__ == '__main__':
    run_pipeline()
