"""Import project libraries without executing command entry points or Streamlit UI."""
from pathlib import Path
import importlib
import os
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))


def main():
    os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".cache/import_matplotlib"))
    os.environ.setdefault("MPLBACKEND","Agg")
    modules = ['run_pipeline', 'prospective']
    modules += [p.stem for p in (ROOT/'scripts').glob('*.py') if p.stem != 'check_imports']
    modules += ['.'.join(p.relative_to(ROOT).with_suffix('').parts) for p in (ROOT/'approval_prediction').rglob('*.py')
                if p.name not in {'app.py','__init__.py'} and not p.name.startswith('test_')]
    for name in sorted(modules):
        importlib.import_module(name)
    print(f'PASS: {len(modules)} local modules imported; app entry covered by AppFlowTests')


if __name__ == '__main__':
    main()
