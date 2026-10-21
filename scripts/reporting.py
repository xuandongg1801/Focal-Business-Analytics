"""Explicit plot setup and strict JSON writing; importing creates no files."""
import json
import os
from pathlib import Path
from config import ROOT, FIG

COLOR_MAIN = '#1f6f8b'
COLOR_ACC = '#e0803c'
COLOR_GREY = '#8d98a1'
COLOR_RED = '#c0392b'


def configure_plots():
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
    os.environ.setdefault('MPLBACKEND', 'Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.titleweight': 'bold'})
    FIG.mkdir(parents=True, exist_ok=True)
    return plt


def save_figure(fig, name: str) -> None:
    import matplotlib.pyplot as plt
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def write_json(path: Path, values: dict) -> None:
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
