from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .models import ControlResult, MipSystem


FLOAT_FORMAT = "%.15g"


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8", float_format=FLOAT_FORMAT)


def _matrix_frame(system: MipSystem, matrix: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(matrix, columns=system.source.codes)
    frame.insert(0, "producto", system.source.labels)
    frame.insert(0, "codigo", system.source.codes)
    return frame


def _products_frame(system: MipSystem) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "orden": np.arange(1, len(system.source.codes) + 1),
            "codigo": system.source.codes,
            "producto": system.source.labels,
            "produccion_cero": system.source.output == 0,
            "unidad_monetaria": "millones de quetzales",
            "precios": "precios básicos",
            "anio_referencia": 2013,
        }
    )


def _final_frame(
    system: MipSystem,
    *,
    origin: str,
) -> pd.DataFrame:
    source = system.source
    components = source.final_domestic if origin == "domestico" else source.final_imported
    frame = pd.DataFrame({"codigo": source.codes, "producto": source.labels})
    for name, values in components.items():
        export_name = "ajuste_cif_fob_publicado" if name == "ajuste_cif_fob" else name
        frame[export_name] = values
    frame["ajuste_cif_fob_aplicado"] = -components["ajuste_cif_fob"]
    frame["total_componentes_no_solapados"] = (
        system.final_domestic_components
        if origin == "domestico"
        else system.final_imported_components
    )
    if origin == "domestico":
        frame["total_demanda_final_fuente"] = system.final_domestic_from_source_total
        frame["ajuste_balance_produccion_utilizacion"] = system.supply_use_gap
        frame["demanda_final_balanceada"] = system.final_domestic_balanced
    else:
        frame["total_demanda_final_fuente"] = system.final_imported_from_source_total
    return frame


def _transactions_long(system: MipSystem) -> pd.DataFrame:
    n = len(system.source.codes)
    input_codes = np.repeat(np.asarray(system.source.codes), n)
    input_labels = np.repeat(np.asarray(system.source.labels), n)
    destination_codes = np.tile(np.asarray(system.source.codes), n)
    destination_labels = np.tile(np.asarray(system.source.labels), n)
    frames = []
    for origin, matrix in (
        ("domestico", system.source.z_domestic),
        ("importado", system.source.z_imported),
    ):
        frames.append(
            pd.DataFrame(
                {
                    "origen": origin,
                    "producto_insumo_codigo": input_codes,
                    "producto_insumo": input_labels,
                    "producto_destino_codigo": destination_codes,
                    "producto_destino": destination_labels,
                    "valor_millones_quetzales": matrix.reshape(-1),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _final_long(system: MipSystem) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for origin, components in (
        ("domestico", system.source.final_domestic),
        ("importado", system.source.final_imported),
    ):
        for component, values in components.items():
            multiplier = -1.0 if component == "ajuste_cif_fob" else 1.0
            rows.append(
                pd.DataFrame(
                    {
                        "origen": origin,
                        "codigo": system.source.codes,
                        "producto": system.source.labels,
                        "componente": component,
                        "valor_publicado_millones_quetzales": values,
                        "multiplicador_contable": multiplier,
                        "valor_aplicado_millones_quetzales": values * multiplier,
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def export_outputs(system: MipSystem, root: Path, controls: list[ControlResult]) -> list[Path]:
    results = root / "02_resultados_y_diccionario"
    matrices = results / "matrices"
    vectors = results / "vectores"
    long_data = results / "datos_largos"
    verification = root / "05_verificacion"

    written: list[Path] = []

    matrix_outputs = {
        "Z_domestica_2013.csv": system.source.z_domestic,
        "Z_importada_2013.csv": system.source.z_imported,
        "A_domestica_2013.csv": system.a_domestic,
        "A_importada_2013.csv": system.a_imported,
        "A_total_insumos_2013.csv": system.a_total_inputs,
        "Leontief_domestica_2013.csv": system.leontief_domestic,
    }
    for name, matrix in matrix_outputs.items():
        path = matrices / name
        _write_csv(_matrix_frame(system, matrix), path)
        written.append(path)

    products_path = results / "productos_2013.csv"
    _write_csv(_products_frame(system), products_path)
    written.append(products_path)

    domestic_final_path = vectors / "demanda_final_domestica_2013.csv"
    _write_csv(_final_frame(system, origin="domestico"), domestic_final_path)
    written.append(domestic_final_path)

    imported_final_path = vectors / "demanda_final_importada_2013.csv"
    _write_csv(_final_frame(system, origin="importado"), imported_final_path)
    written.append(imported_final_path)

    source = system.source
    output_frame = pd.DataFrame(
        {
            "codigo": source.codes,
            "producto": source.labels,
            "produccion_precios_basicos": source.output,
            "total_utilizacion_precios_basicos": source.total_utilization_domestic,
            "diferencia_produccion_utilizacion": system.supply_use_gap,
            "producto_interno_bruto": source.gdp,
            "puestos_trabajo": source.jobs,
        }
    )
    output_path = vectors / "produccion_y_utilizacion_2013.csv"
    _write_csv(output_frame, output_path)
    written.append(output_path)

    primary_frame = pd.DataFrame(
        {
            "codigo": source.codes,
            "producto": source.labels,
            "consumo_intermedio_domestico": source.z_domestic.sum(axis=0),
            "consumo_intermedio_importado": source.z_imported.sum(axis=0),
            "impuestos_sobre_productos": source.taxes_products,
            "subvenciones_sobre_productos": source.subsidies_products,
            "impuestos_netos_sobre_productos": source.net_taxes_products,
            "valor_agregado_bruto_oficial": source.value_added,
            "produccion_precios_basicos": source.output,
        }
    )
    primary_frame["residuo_identidad_columna"] = primary_frame[
        "produccion_precios_basicos"
    ] - primary_frame[
        [
            "consumo_intermedio_domestico",
            "consumo_intermedio_importado",
            "impuestos_netos_sobre_productos",
            "valor_agregado_bruto_oficial",
        ]
    ].sum(axis=1)
    primary_path = vectors / "cuentas_primarias_2013.csv"
    _write_csv(primary_frame, primary_path)
    written.append(primary_path)

    vab_frame = pd.DataFrame(
        {
            "codigo": source.codes,
            "producto": source.labels,
            "remuneracion_asalariados": source.compensation,
            "impuestos_produccion_importaciones": source.taxes_production_imports,
            "subvenciones_produccion": source.subsidies_production,
            "excedente_explotacion_bruto": source.operating_surplus,
            "ingreso_mixto_bruto": source.mixed_income,
            "valor_agregado_bruto_oficial": source.value_added_components_source,
        }
    )
    vab_frame["suma_componentes"] = vab_frame[
        [
            "remuneracion_asalariados",
            "impuestos_produccion_importaciones",
            "subvenciones_produccion",
            "excedente_explotacion_bruto",
            "ingreso_mixto_bruto",
        ]
    ].sum(axis=1)
    vab_frame["residuo_componentes_vab"] = (
        vab_frame["valor_agregado_bruto_oficial"] - vab_frame["suma_componentes"]
    )
    vab_path = vectors / "componentes_valor_agregado_2013.csv"
    _write_csv(vab_frame, vab_path)
    written.append(vab_path)

    coefficients_frame = pd.DataFrame(
        {"codigo": source.codes, "producto": source.labels, **system.primary_coefficients}
    )
    coefficients_frame["suma_coeficientes"] = sum(system.primary_coefficients.values())
    coefficients_path = vectors / "coeficientes_primarios_2013.csv"
    _write_csv(coefficients_frame, coefficients_path)
    written.append(coefficients_path)

    transactions_path = long_data / "transacciones_intermedias_2013.csv"
    _write_csv(_transactions_long(system), transactions_path)
    written.append(transactions_path)

    final_long_path = long_data / "demanda_final_componentes_2013.csv"
    _write_csv(_final_long(system), final_long_path)
    written.append(final_long_path)

    controls_path = verification / "controles_reproduccion.csv"
    _write_csv(pd.DataFrame([asdict(control) for control in controls]), controls_path)
    written.append(controls_path)

    balance_frame = pd.DataFrame(
        {
            "codigo": source.codes,
            "producto": source.labels,
            "balance_fila_fuente": source.total_utilization_domestic
            - source.z_domestic.sum(axis=1)
            - system.final_domestic_from_source_total,
            "diferencia_produccion_utilizacion": system.supply_use_gap,
            "balance_fila_ajustado": source.output
            - source.z_domestic.sum(axis=1)
            - system.final_domestic_balanced,
            "balance_columna": source.output
            - (
                source.z_domestic.sum(axis=0)
                + source.z_imported.sum(axis=0)
                + source.net_taxes_products
                + source.value_added
            ),
        }
    )
    balance_path = verification / "balances_por_producto.csv"
    _write_csv(balance_frame, balance_path)
    written.append(balance_path)

    metadata = {
        "title": "Matriz insumo-producto producto por producto de Guatemala 2013 — paquete reproducible",
        "version": "0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file_name": source.source_path.name,
        "source_sha256": source.source_sha256,
        "year": 2013,
        "valuation": "precios básicos",
        "currency_unit": "millones de quetzales",
        "products": len(source.codes),
        "zero_output_products": [
            code for code, value in zip(source.codes, source.output) if value == 0
        ],
        "total_output_million_quetzales": float(source.output.sum()),
        "total_value_added_million_quetzales": float(source.value_added.sum()),
        "spectral_radius_a_domestic": system.spectral_radius,
        "condition_number_i_minus_a": system.condition_number,
        "inverse_residual_max_abs": system.inverse_residual_max_abs,
        "mandatory_controls_passed": all(
            control.status == "APROBADO" for control in controls if control.mandatory
        ),
    }
    metadata_path = results / "metadatos_dataset.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(metadata_path)
    return written


def write_reproduction_report(
    system: MipSystem,
    controls: list[ControlResult],
    path: Path,
) -> None:
    approved = sum(control.status == "APROBADO" for control in controls)
    warnings = sum(control.status == "ADVERTENCIA" for control in controls)
    failures = sum(control.status == "FALLÓ" for control in controls)
    source = system.source
    lines = [
        "INFORME DE REPRODUCCIÓN COMPUTACIONAL — MIP GUATEMALA 2013",
        "",
        f"Fuente: {source.source_path.name}",
        f"SHA-256: {source.source_sha256}",
        "Cobertura: 152 productos, año de referencia 2013",
        "Valoración: precios básicos; millones de quetzales",
        "",
        "RESULTADOS DE CONTROL",
        f"Aprobados: {approved}",
        f"Advertencias: {warnings}",
        f"Fallidos: {failures}",
        "",
        "TOTALES PRINCIPALES",
        f"Producción: {source.output.sum():.6f}",
        f"Valor agregado bruto oficial: {source.value_added.sum():.6f}",
        f"Transacciones intermedias domésticas: {source.z_domestic.sum():.6f}",
        f"Transacciones intermedias importadas: {source.z_imported.sum():.6f}",
        f"Radio espectral A doméstica: {system.spectral_radius:.12f}",
        f"Residuo máximo de (I-A)L-I: {system.inverse_residual_max_abs:.3e}",
        "",
        "CONTROLES",
    ]
    for control in controls:
        lines.append(
            f"[{control.status}] {control.control_id} — {control.description}: "
            f"valor={control.value}; tolerancia={control.tolerance}. {control.detail}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_public_manifest(root: Path, path: Path) -> None:
    excluded_parts = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "_rendered",
        "fuentes_originales_no_redistribuidas",
    }
    excluded_names = {path.name, ".DS_Store"}
    records: list[tuple[str, int, str]] = []
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(root)
        if any(part in excluded_parts for part in relative.parts):
            continue
        if file_path.name in excluded_names:
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        records.append((relative.as_posix(), file_path.stat().st_size, digest))
    lines = ["ruta\ttamano_bytes\tsha256"]
    lines.extend(f"{name}\t{size}\t{digest}" for name, size, digest in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
