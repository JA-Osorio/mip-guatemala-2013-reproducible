from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import SourceLayout


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("La configuración debe ser un objeto YAML.")
    return config


def load_layout(config: dict[str, Any]) -> SourceLayout:
    return SourceLayout(**config["source_layout"])


def resolve_from_root(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path

