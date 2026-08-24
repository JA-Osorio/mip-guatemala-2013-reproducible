from __future__ import annotations

from pathlib import Path

from .config import load_config, load_layout, resolve_from_root
from .export import (
    export_outputs,
    write_public_manifest,
    write_reproduction_report,
)
from .extract import extract_source
from .transform import build_system
from .validate import assert_mandatory_controls, validate_system


def reproduce(
    *,
    root: Path,
    config_path: Path,
    source_override: Path | None = None,
) -> dict[str, object]:
    config = load_config(config_path)
    layout = load_layout(config)
    source_path = source_override or resolve_from_root(root, config["source"]["path"])

    source = extract_source(source_path, layout)
    system = build_system(source)
    controls = validate_system(
        system,
        expected_sha256=config["source"]["expected_sha256"],
        source_balance_tolerance=float(config["validation"]["source_balance_tolerance"]),
        numeric_tolerance=float(config["validation"]["numeric_tolerance"]),
    )
    assert_mandatory_controls(controls)

    written = export_outputs(system, root, controls)
    report_path = root / "05_verificacion" / "informe_reproduccion_computacional_mip_2013.txt"
    write_reproduction_report(system, controls, report_path)
    written.append(report_path)

    manifest_path = root / "manifiesto_archivos.txt"
    write_public_manifest(root, manifest_path)
    written.append(manifest_path)

    return {
        "system": system,
        "controls": controls,
        "written": written,
        "report": report_path,
        "manifest": manifest_path,
    }

