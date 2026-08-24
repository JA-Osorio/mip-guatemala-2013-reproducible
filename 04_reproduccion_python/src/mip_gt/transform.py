from __future__ import annotations

import numpy as np

from .models import MipSourceData, MipSystem


def _divide_columns(matrix: np.ndarray, output: np.ndarray) -> np.ndarray:
    return np.divide(
        matrix,
        output[np.newaxis, :],
        out=np.zeros_like(matrix, dtype=float),
        where=output[np.newaxis, :] != 0,
    )


def _divide_vector(vector: np.ndarray, output: np.ndarray) -> np.ndarray:
    return np.divide(
        vector,
        output,
        out=np.zeros_like(vector, dtype=float),
        where=output != 0,
    )


def _sum_final_uses(components: dict[str, np.ndarray]) -> np.ndarray:
    """Reproduce la convención de totalización publicada en la MIP.

    La columna de ajuste CIF/FOB se muestra con su signo en la fuente, pero el
    total de utilización la resta. Conservamos el valor publicado en la
    extracción y aplicamos aquí el multiplicador contable -1.
    """
    total = np.zeros_like(next(iter(components.values())), dtype=float)
    for name, values in components.items():
        total += -values if name == "ajuste_cif_fob" else values
    return total


def build_system(source: MipSourceData) -> MipSystem:
    n = len(source.codes)
    output = source.output
    a_domestic = _divide_columns(source.z_domestic, output)
    a_imported = _divide_columns(source.z_imported, output)
    a_total_inputs = a_domestic + a_imported
    identity = np.eye(n)
    leontief = np.linalg.inv(identity - a_domestic)

    final_domestic_components = _sum_final_uses(source.final_domestic)
    final_imported_components = _sum_final_uses(source.final_imported)
    final_domestic_from_source_total = (
        source.total_utilization_domestic - source.total_intermediate_domestic_source
    )
    final_imported_from_source_total = (
        source.total_utilization_imported - source.total_intermediate_imported_source
    )
    final_domestic_balanced = output - source.z_domestic.sum(axis=1)
    supply_use_gap = output - source.total_utilization_domestic

    primary_coefficients = {
        "consumo_intermedio_domestico": _divide_vector(
            source.z_domestic.sum(axis=0), output
        ),
        "consumo_intermedio_importado": _divide_vector(
            source.z_imported.sum(axis=0), output
        ),
        "impuestos_netos_productos": _divide_vector(source.net_taxes_products, output),
        "valor_agregado_bruto": _divide_vector(source.value_added, output),
    }

    eigenvalues = np.linalg.eigvals(a_domestic)
    inverse_residual = (identity - a_domestic) @ leontief - identity

    return MipSystem(
        source=source,
        a_domestic=a_domestic,
        a_imported=a_imported,
        a_total_inputs=a_total_inputs,
        leontief_domestic=leontief,
        final_domestic_components=final_domestic_components,
        final_domestic_from_source_total=final_domestic_from_source_total,
        final_domestic_balanced=final_domestic_balanced,
        supply_use_gap=supply_use_gap,
        final_imported_components=final_imported_components,
        final_imported_from_source_total=final_imported_from_source_total,
        primary_coefficients=primary_coefficients,
        spectral_radius=float(np.max(np.abs(eigenvalues))),
        condition_number=float(np.linalg.cond(identity - a_domestic)),
        inverse_residual_max_abs=float(np.max(np.abs(inverse_residual))),
    )
