from __future__ import annotations

import re

import numpy as np

from .models import ControlResult, MipSystem


def _max_abs(values: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(values, dtype=float))))


def _result(
    control_id: str,
    description: str,
    passed: bool,
    value: float | int | str,
    tolerance: float | int | str,
    detail: str,
    *,
    mandatory: bool = True,
) -> ControlResult:
    return ControlResult(
        control_id=control_id,
        description=description,
        status="APROBADO" if passed else ("ADVERTENCIA" if not mandatory else "FALLÓ"),
        value=value,
        tolerance=tolerance,
        detail=detail,
        mandatory=mandatory,
    )


def validate_system(
    system: MipSystem,
    *,
    expected_sha256: str,
    source_balance_tolerance: float,
    numeric_tolerance: float,
) -> list[ControlResult]:
    source = system.source
    n = len(source.codes)
    controls: list[ControlResult] = []

    controls.append(
        _result(
            "SRC-01",
            "Huella SHA-256 de la copia de referencia",
            source.source_sha256 == expected_sha256,
            source.source_sha256,
            expected_sha256,
            "Una huella distinta puede corresponder a otra copia oficial; requiere revisión de valores.",
            mandatory=False,
        )
    )
    controls.append(
        _result(
            "EST-01",
            "Cantidad de productos",
            n == 152,
            n,
            152,
            "La MIP producto por producto debe contener 152 productos.",
        )
    )
    expected_codes = tuple(f"P{i:03d}" for i in range(1, 153))
    controls.append(
        _result(
            "EST-02",
            "Secuencia completa de códigos NPG",
            source.codes == expected_codes,
            int(sum(code == expected for code, expected in zip(source.codes, expected_codes))),
            152,
            "Se esperan códigos consecutivos P001–P152.",
        )
    )
    controls.append(
        _result(
            "EST-03",
            "Coincidencia entre códigos de filas y columnas",
            source.codes == source.column_codes,
            int(sum(a == b for a, b in zip(source.codes, source.column_codes))),
            152,
            "La matriz simétrica debe usar la misma nomenclatura en ambos ejes.",
        )
    )
    controls.append(
        _result(
            "EST-04",
            "Etiquetas de producto no vacías",
            all(label and not re.fullmatch(r"\s*", label) for label in source.labels),
            sum(bool(label.strip()) for label in source.labels),
            152,
            "Cada código debe conservar su denominación oficial.",
        )
    )
    controls.append(
        _result(
            "MAT-01",
            "Dimensión de Z doméstica",
            source.z_domestic.shape == (152, 152),
            str(source.z_domestic.shape),
            "(152, 152)",
            "Bloque de transacciones intermedias de origen nacional.",
        )
    )
    controls.append(
        _result(
            "MAT-02",
            "Dimensión de Z importada",
            source.z_imported.shape == (152, 152),
            str(source.z_imported.shape),
            "(152, 152)",
            "Bloque de utilización intermedia de importaciones.",
        )
    )
    controls.append(
        _result(
            "MAT-03",
            "Transacciones intermedias no negativas",
            float(source.z_domestic.min()) >= 0 and float(source.z_imported.min()) >= 0,
            min(float(source.z_domestic.min()), float(source.z_imported.min())),
            ">= 0",
            "Los ajustes CIF/FOB pertenecen a demanda final, no a Z.",
        )
    )

    row_domestic_gap = (
        source.z_domestic.sum(axis=1) - source.total_intermediate_domestic_source
    )
    row_imported_gap = (
        source.z_imported.sum(axis=1) - source.total_intermediate_imported_source
    )
    controls.append(
        _result(
            "BAL-01",
            "Suma por fila de Z doméstica frente al subtotal de la fuente",
            _max_abs(row_domestic_gap) <= numeric_tolerance,
            _max_abs(row_domestic_gap),
            numeric_tolerance,
            "No se omiten ni duplican productos del bloque intermedio doméstico.",
        )
    )
    controls.append(
        _result(
            "BAL-02",
            "Suma por fila de Z importada frente al subtotal de la fuente",
            _max_abs(row_imported_gap) <= numeric_tolerance,
            _max_abs(row_imported_gap),
            numeric_tolerance,
            "No se omiten ni duplican productos del bloque intermedio importado.",
        )
    )
    col_domestic_gap = (
        source.z_domestic.sum(axis=0) - source.domestic_intermediate_by_column_source
    )
    col_imported_gap = (
        source.z_imported.sum(axis=0) - source.imported_intermediate_by_column_source
    )
    controls.append(
        _result(
            "BAL-03",
            "Suma por columna de Z doméstica frente al subtotal de la fuente",
            _max_abs(col_domestic_gap) <= numeric_tolerance,
            _max_abs(col_domestic_gap),
            numeric_tolerance,
            "Comprueba el total de insumos domésticos por producto producido.",
        )
    )
    controls.append(
        _result(
            "BAL-04",
            "Suma por columna de Z importada frente al subtotal de la fuente",
            _max_abs(col_imported_gap) <= numeric_tolerance,
            _max_abs(col_imported_gap),
            numeric_tolerance,
            "Comprueba el total de insumos importados por producto producido.",
        )
    )
    final_components_gap = (
        system.final_domestic_components - system.final_domestic_from_source_total
    )
    controls.append(
        _result(
            "BAL-05",
            "Componentes no solapados de demanda final doméstica",
            _max_abs(final_components_gap) <= numeric_tolerance,
            _max_abs(final_components_gap),
            numeric_tolerance,
            "Excluye subtotales duplicados y resta el ajuste CIF/FOB, como hace el total publicado.",
        )
    )
    final_imported_gap = (
        system.final_imported_components - system.final_imported_from_source_total
    )
    controls.append(
        _result(
            "BAL-06",
            "Componentes no solapados de demanda final importada",
            _max_abs(final_imported_gap) <= numeric_tolerance,
            _max_abs(final_imported_gap),
            numeric_tolerance,
            "Mantiene por separado las utilizaciones finales importadas y la convención CIF/FOB.",
        )
    )
    controls.append(
        _result(
            "BAL-07",
            "Diferencia producción–utilización publicada",
            _max_abs(system.supply_use_gap) <= source_balance_tolerance,
            _max_abs(system.supply_use_gap),
            source_balance_tolerance,
            "La fuente advierte diferencias de redondeo; el ajuste se conserva explícitamente.",
        )
    )
    exact_row_balance = (
        source.output - source.z_domestic.sum(axis=1) - system.final_domestic_balanced
    )
    controls.append(
        _result(
            "BAL-08",
            "Identidad exacta x = Z1 + y balanceada",
            _max_abs(exact_row_balance) <= numeric_tolerance,
            _max_abs(exact_row_balance),
            numeric_tolerance,
            "La demanda final balanceada incorpora sin ocultarlo el ajuste producción–utilización.",
        )
    )
    column_identity = source.output - (
        source.z_domestic.sum(axis=0)
        + source.z_imported.sum(axis=0)
        + source.net_taxes_products
        + source.value_added
    )
    controls.append(
        _result(
            "BAL-09",
            "Identidad de costos por columna",
            _max_abs(column_identity) <= source_balance_tolerance,
            _max_abs(column_identity),
            source_balance_tolerance,
            "x = insumos domésticos + importados + impuestos netos sobre productos + VAB.",
        )
    )
    vab_components = (
        source.compensation
        + source.taxes_production_imports
        + source.subsidies_production
        + source.operating_surplus
        + source.mixed_income
    )
    controls.append(
        _result(
            "BAL-10",
            "Componentes del VAB",
            _max_abs(vab_components - source.value_added_components_source)
            <= source_balance_tolerance,
            _max_abs(vab_components - source.value_added_components_source),
            source_balance_tolerance,
            "Las subvenciones se mantienen con el signo de la fuente.",
        )
    )
    controls.append(
        _result(
            "MOD-01",
            "Radio espectral de A doméstica",
            system.spectral_radius < 1,
            system.spectral_radius,
            "< 1",
            "Condición suficiente para la serie de Leontief.",
        )
    )
    controls.append(
        _result(
            "MOD-02",
            "Residuo de la inversa de Leontief",
            system.inverse_residual_max_abs <= 1e-10,
            system.inverse_residual_max_abs,
            1e-10,
            "Comprueba (I-A)L = I.",
        )
    )
    primary_sum = sum(system.primary_coefficients.values())
    positive_output = source.output != 0
    primary_gap = (
        _max_abs(primary_sum[positive_output] - 1)
        if np.any(positive_output)
        else 0.0
    )
    controls.append(
        _result(
            "MOD-03",
            "Suma de coeficientes contables por columna",
            primary_gap <= source_balance_tolerance,
            primary_gap,
            source_balance_tolerance,
            "Domésticos + importados + impuestos netos + VAB deben sumar uno cuando x>0.",
        )
    )
    zero_output = source.output == 0
    zero_columns_gap = 0.0
    if np.any(zero_output):
        zero_columns_gap = max(
            _max_abs(source.z_domestic[:, zero_output]),
            _max_abs(source.z_imported[:, zero_output]),
        )
    controls.append(
        _result(
            "MOD-04",
            "Columnas nulas para productos sin producción",
            zero_columns_gap <= numeric_tolerance,
            zero_columns_gap,
            numeric_tolerance,
            "Evita divisiones artificiales en productos con x=0.",
        )
    )
    return controls


def assert_mandatory_controls(controls: list[ControlResult]) -> None:
    failures = [c for c in controls if c.mandatory and c.status == "FALLÓ"]
    if failures:
        lines = "; ".join(f"{c.control_id}: {c.value}" for c in failures)
        raise RuntimeError(f"Fallaron controles obligatorios: {lines}")
