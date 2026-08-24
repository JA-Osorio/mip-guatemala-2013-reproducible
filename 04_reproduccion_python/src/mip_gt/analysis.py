"""Indicadores básicos para usar la MIP en análisis insumo-producto."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def _as_vector(values: Sequence[float] | np.ndarray, n: int, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (n,):
        raise ValueError(f"{name} debe tener longitud {n}; se recibió {vector.shape}")
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} contiene valores no finitos")
    return vector


def _as_square(matrix: np.ndarray, n: int, name: str) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.shape != (n, n):
        raise ValueError(f"{name} debe tener forma {(n, n)}; se recibió {array.shape}")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contiene valores no finitos")
    return array


def safe_coefficient(numerator: np.ndarray, output: np.ndarray) -> np.ndarray:
    """Calcula coeficientes por unidad de producción sin dividir entre cero."""

    numerator = np.asarray(numerator, dtype=float)
    output = np.asarray(output, dtype=float)
    if numerator.shape != output.shape:
        raise ValueError("numerator y output deben tener la misma forma")
    coefficients = np.zeros_like(output, dtype=float)
    np.divide(numerator, output, out=coefficients, where=output != 0)
    return coefficients


def io_indicator_frame(
    *,
    codes: Sequence[str],
    labels: Sequence[str],
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    value_added_coefficients: Sequence[float] | np.ndarray,
    employment_coefficients: Sequence[float] | np.ndarray,
) -> pd.DataFrame:
    """Construye multiplicadores e índices IO comparables entre productos.

    Los multiplicadores se basan en la inversa doméstica ``L=(I-Aᵈ)⁻¹``.
    Las importaciones son fugas: el requerimiento total se calcula como
    ``1' Aᵐ L``. Los encadenamientos normalizados son los índices de
    Rasmussen-Hirschman obtenidos de las sumas de columnas y filas de ``L``.
    """

    codes = tuple(codes)
    labels = tuple(labels)
    if len(codes) != len(labels):
        raise ValueError("codes y labels deben tener la misma longitud")
    n = len(codes)
    a_m = _as_square(a_imported, n, "a_imported")
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    value_added = _as_vector(value_added_coefficients, n, "value_added_coefficients")
    employment = _as_vector(employment_coefficients, n, "employment_coefficients")

    output_multiplier = leontief.sum(axis=0)
    row_dispersion = leontief.sum(axis=1)
    backward = output_multiplier / output_multiplier.mean()
    forward = row_dispersion / row_dispersion.mean()
    direct_import = a_m.sum(axis=0)
    total_import = (a_m @ leontief).sum(axis=0)
    value_added_multiplier = value_added @ leontief
    employment_multiplier = employment @ leontief

    return pd.DataFrame(
        {
            "codigo": codes,
            "producto": labels,
            "multiplicador_produccion_domestica": output_multiplier,
            "encadenamiento_atras_normalizado": backward,
            "encadenamiento_adelante_normalizado": forward,
            "coeficiente_importacion_directa": direct_import,
            "requerimiento_importacion_total": total_import,
            "multiplicador_valor_agregado": value_added_multiplier,
            "multiplicador_empleo_puestos_por_millon": employment_multiplier,
        }
    )
