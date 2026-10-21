from pathlib import Path
from approval_prediction.config import OUTPUT
APP = Path(__file__).resolve().parents[1]
MODELS = OUTPUT / 'models'
TABLES = OUTPUT / 'tables'
SCHEMA = MODELS / 'model_schema.json'
