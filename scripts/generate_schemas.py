"""Regenerate maintained JSON Schemas after contract changes."""

import json
from pathlib import Path

from src.blueprint.models import Decomposition, Design, UseCase
from src.tender.models import FactInput, TenderInput

root = Path(__file__).resolve().parents[1] / "blueprint" / "schemas"
root.mkdir(parents=True, exist_ok=True)
for name, model in [
    ("use-case", UseCase),
    ("design", Design),
    ("decomposition", Decomposition),
    ("tender", TenderInput),
    ("evidence", FactInput),
]:
    (root / f"{name}.schema.json").write_text(
        json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8"
    )
