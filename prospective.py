"""Explicitly freeze issued forecasts and score later, complete actual months."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from config import ROOT, TAB, PROC
from data_rules import monthly_series, sales_km
from forecasting import wape
from reporting import write_json


def freeze_record(forecast: pd.DataFrame, method: dict, issued_at: datetime) -> dict:
    """Capture the actual issuance time and all rules defining the future target."""
    if issued_at.tzinfo is None:
        raise ValueError('Issuance must include a timezone')
    return {
        'issued_at_utc': issued_at.astimezone(timezone.utc).isoformat(),
        'history_end': method['history_end'],
        'selected_model': method['selected_model'],
        'item_threshold_km': method['final_threshold_km'],
        'confirmed_project_orders': method['confirmed_project_orders'],
        'forecast': forecast[['thang', 'du_bao_km']].to_dict('records'),
    }


def evaluate_record(record: dict, mart: pd.DataFrame, complete_through: str,
                    as_of: datetime) -> tuple[pd.DataFrame, dict]:
    """Completeness is an explicit operator attestation; unobserved future is never scored."""
    cutoff = pd.Period(complete_through, freq='M')
    current = pd.Period(as_of.astimezone(timezone.utc).strftime('%Y-%m'), freq='M')
    if cutoff >= current:
        raise ValueError('Cannot attest a current or future month as complete')
    issued = datetime.fromisoformat(record['issued_at_utc'])
    predictions = pd.DataFrame(record['forecast'])
    months = pd.PeriodIndex(predictions['thang'], freq='M')
    after_issuance = months.start_time.tz_localize('UTC') > issued
    eligible = after_issuance & (months <= cutoff) & (months > pd.Period(record['history_end'], freq='M'))
    result = predictions.loc[eligible].copy()
    if result.empty:
        return result, {'status': 'NO_COMPLETED_PROSPECTIVE_MONTHS', 'months': 0}
    base = mart.loc[sales_km(mart)].copy()
    values = base['so_luong_km'].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Actual KM must be finite and nonnegative')
    base = base[~base['so_xac_nhan_don_hang'].isin(record['confirmed_project_orders'])
                & base['so_luong_km'].le(record['item_threshold_km'])]
    # Explicit completeness attestation permits zero for a completed month with no eligible rows.
    actual = monthly_series(base, pd.PeriodIndex(result['thang'], freq='M')).to_numpy()
    pred = result['du_bao_km'].to_numpy(dtype=float)
    result['actual_baseline_km'] = actual
    metric = wape(actual, pred)
    return result, {'status': 'EVALUATED', 'months': len(result),
                    'complete_through_attested': str(cutoff), 'wape_pct': None if np.isnan(metric) else metric,
                    'mae_km': float(np.abs(actual-pred).mean()), 'used_for_tuning': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('freeze')
    evaluate = commands.add_parser('evaluate')
    evaluate.add_argument('run_dir', type=Path)
    evaluate.add_argument('--complete-through', required=True, help='Explicit completeness attestation, YYYY-MM')
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if args.command == 'freeze':
        forecast = pd.read_csv(TAB / 'forecast.csv')
        method = json.loads((TAB / 'forecast_methodology.json').read_text(encoding='utf-8'))
        record = freeze_record(forecast, method, now)
        folder = ROOT / 'outputs/forecast_runs' / now.strftime('%Y%m%dT%H%M%S%fZ')
        folder.mkdir(parents=True, exist_ok=False)
        write_json(folder / 'issued_forecast.json', record)
        digest = hashlib.sha256((folder / 'issued_forecast.json').read_bytes()).hexdigest()
        (folder / 'issued_forecast.sha256').write_text(digest, encoding='utf-8')
        print(folder)
    else:
        path = args.run_dir / 'issued_forecast.json'
        expected = (args.run_dir / 'issued_forecast.sha256').read_text(encoding='utf-8').strip()
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen forecast was modified')
        record = json.loads(path.read_text(encoding='utf-8'))
        actual = pd.read_csv(PROC / 'mart_order_items.csv')
        rows, metrics = evaluate_record(record, actual, args.complete_through, now)
        print(json.dumps(metrics, indent=2))
        if not rows.empty:
            rows.to_csv(args.run_dir / 'forecast_vs_actual.csv', index=False, encoding='utf-8-sig')
            write_json(args.run_dir / 'evaluation.json', metrics)


if __name__ == '__main__':
    main()
