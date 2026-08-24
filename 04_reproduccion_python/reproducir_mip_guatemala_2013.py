#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
SRC = SCRIPT_DIR / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mip_gt.run import reproduce  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrae, transforma, valida y publica los derivados reproducibles de "
            "la MIP producto por producto de Guatemala 2013."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=SCRIPT_DIR / "config_mip.yaml",
        help="Archivo YAML de configuración.",
    )
    parser.add_argument(
        "--fuente",
        type=Path,
        default=None,
        help="Ruta alternativa a MIP_AR2013_NPG.xlsx.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = reproduce(
        root=ROOT,
        config_path=args.config.resolve(),
        source_override=args.fuente.resolve() if args.fuente else None,
    )
    controls = result["controls"]
    approved = sum(control.status == "APROBADO" for control in controls)
    warnings = sum(control.status == "ADVERTENCIA" for control in controls)
    print(
        f"Reproducción completada: {approved} controles aprobados, "
        f"{warnings} advertencias, 0 fallos obligatorios."
    )
    print(f"Informe: {result['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

