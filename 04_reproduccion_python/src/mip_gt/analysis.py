"""Herramientas reutilizables para análisis insumo-producto.

Convención matricial
--------------------
Las filas de ``A`` son productos insumo y las columnas son productos que los
utilizan. Por tanto ``A[i, j]`` es el insumo ``i`` requerido por unidad de
producción ``j``. Un choque de demanda final es un vector columna ``dy`` y la
respuesta de producción es ``dx = (I - A_domestica)^-1 @ dy``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FLOAT_FORMAT = "%.15g"
OFFICIAL_GDP_2013_MILLION_QUETZALES = 416383.20533754566
OFFICIAL_NET_TAXES_ALL_USES_2013_MILLION_QUETZALES = 24365.050408378458


@dataclass(frozen=True)
class DemandShockImpact:
    """Descomposición completa de un choque de demanda final doméstica."""

    by_product: pd.DataFrame
    totals: dict[str, float]
    checks: pd.DataFrame


@dataclass(frozen=True)
class CanonicalIoData:
    """Matrices y vectores analíticos leídos de las salidas canónicas."""

    codes: tuple[str, ...]
    labels: tuple[str, ...]
    output: np.ndarray
    jobs: np.ndarray
    legacy_row_174: np.ndarray
    final_domestic_balanced: np.ndarray
    z_domestic: np.ndarray
    z_imported: np.ndarray
    a_domestic: np.ndarray
    a_imported: np.ndarray
    a_total_inputs: np.ndarray
    leontief_domestic: np.ndarray
    value_added_coefficients: np.ndarray
    net_tax_coefficients: np.ndarray
    employment_coefficients: np.ndarray


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


def _validate_codes_labels(
    codes: Sequence[str], labels: Sequence[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    code_tuple = tuple(str(code) for code in codes)
    label_tuple = tuple(str(label) for label in labels)
    if len(code_tuple) != len(label_tuple):
        raise ValueError("codes y labels deben tener la misma longitud")
    if not code_tuple:
        raise ValueError("Se requiere al menos un producto")
    if len(set(code_tuple)) != len(code_tuple):
        raise ValueError("codes contiene identificadores duplicados")
    return code_tuple, label_tuple


def safe_coefficient(numerator: np.ndarray, output: np.ndarray) -> np.ndarray:
    """Calcula coeficientes por unidad de producción sin dividir entre cero."""

    numerator = np.asarray(numerator, dtype=float)
    output = np.asarray(output, dtype=float)
    if numerator.shape != output.shape:
        raise ValueError("numerator y output deben tener la misma forma")
    if not np.isfinite(numerator).all() or not np.isfinite(output).all():
        raise ValueError("numerator y output deben contener valores finitos")
    coefficients = np.zeros_like(output, dtype=float)
    np.divide(numerator, output, out=coefficients, where=output != 0)
    return coefficients


def normalized_linkage(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    """Normaliza un vector de encadenamientos para que su media sea uno."""

    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not np.isfinite(array).all():
        raise ValueError(f"{name} debe ser un vector finito")
    mean = float(array.mean())
    if abs(mean) <= np.finfo(float).eps:
        raise ValueError(f"{name} tiene media cero y no puede normalizarse")
    return array / mean


def _linkage_type(backward: np.ndarray, forward: np.ndarray) -> list[str]:
    tolerance = 1e-12
    result: list[str] = []
    for back_value, forward_value in zip(backward, forward):
        back_high = back_value >= 1.0 - tolerance
        forward_high = forward_value >= 1.0 - tolerance
        if back_high and forward_high:
            result.append("clave")
        elif back_high:
            result.append("impulsor_demanda")
        elif forward_high:
            result.append("proveedor_estrategico")
        else:
            result.append("bajo_promedio")
    return result


def complete_io_indicator_frame(
    *,
    codes: Sequence[str],
    labels: Sequence[str],
    a_domestic: np.ndarray,
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    value_added_coefficients: Sequence[float] | np.ndarray,
    employment_coefficients: Sequence[float] | np.ndarray,
    net_tax_coefficients: Sequence[float] | np.ndarray | None = None,
    zero_output: Sequence[bool] | np.ndarray | None = None,
) -> pd.DataFrame:
    """Construye indicadores, multiplicadores, encadenamientos y rankings.

    Los multiplicadores responden a una unidad adicional de demanda final
    doméstica. Las importaciones intermedias son fugas y se calculan como
    ``A_importada @ L``. Los encadenamientos Rasmussen-Hirschman totales usan
    sumas de columnas y filas de la inversa doméstica y se normalizan a media
    uno. La suma de filas de ``L`` se etiqueta como índice de sensibilidad de
    dispersión hacia adelante: no es un multiplicador de oferta ni proviene de
    una inversa de Ghosh. Los índices directos aplican la misma normalización a
    ``A``.
    """

    code_tuple, label_tuple = _validate_codes_labels(codes, labels)
    n = len(code_tuple)
    a_d = _as_square(a_domestic, n, "a_domestic")
    a_m = _as_square(a_imported, n, "a_imported")
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    value_added = _as_vector(
        value_added_coefficients, n, "value_added_coefficients"
    )
    employment = _as_vector(
        employment_coefficients, n, "employment_coefficients"
    )
    net_taxes = (
        np.zeros(n, dtype=float)
        if net_tax_coefficients is None
        else _as_vector(net_tax_coefficients, n, "net_tax_coefficients")
    )
    zero = (
        np.zeros(n, dtype=bool)
        if zero_output is None
        else np.asarray(zero_output, dtype=bool)
    )
    if zero.shape != (n,):
        raise ValueError(f"zero_output debe tener longitud {n}")

    direct_domestic = a_d.sum(axis=0)
    direct_import = a_m.sum(axis=0)
    direct_total_intermediate = direct_domestic + direct_import
    output_multiplier = leontief.sum(axis=0)
    import_multiplier = (a_m @ leontief).sum(axis=0)
    value_added_multiplier = value_added @ leontief
    employment_multiplier = employment @ leontief
    net_tax_multiplier = net_taxes @ leontief

    backward_direct = normalized_linkage(
        direct_domestic, "encadenamiento_atras_directo"
    )
    forward_direct = normalized_linkage(
        a_d.sum(axis=1), "encadenamiento_adelante_directo"
    )
    backward_total = normalized_linkage(
        output_multiplier, "encadenamiento_atras_total"
    )
    forward_total = normalized_linkage(
        leontief.sum(axis=1), "encadenamiento_adelante_total"
    )

    frame = pd.DataFrame(
        {
            "codigo": code_tuple,
            "producto": label_tuple,
            "producto_produccion_cero": zero,
            "apto_para_simulacion": ~zero,
            "estado_simulacion": np.where(
                zero, "solo_completitud_algebraica", "apto"
            ),
            "coeficiente_insumo_domestico_directo": direct_domestic,
            "coeficiente_importacion_directa": direct_import,
            "coeficiente_intermedio_total_directo": direct_total_intermediate,
            "coeficiente_valor_agregado_directo": value_added,
            "coeficiente_impuestos_netos_sobre_insumos_intermedios_asociados_directo": net_taxes,
            "coeficiente_empleo_directo_puestos_por_millon": employment,
            "multiplicador_produccion_domestica": output_multiplier,
            "multiplicador_produccion_indirecta": output_multiplier - 1.0,
            "requerimiento_importacion_total": import_multiplier,
            "requerimiento_importacion_indirecta": import_multiplier
            - direct_import,
            "multiplicador_valor_agregado": value_added_multiplier,
            "multiplicador_valor_agregado_indirecto": value_added_multiplier
            - value_added,
            "impuestos_netos_sobre_insumos_intermedios_asociados_total": net_tax_multiplier,
            "impuestos_netos_sobre_insumos_intermedios_asociados_indirecto": net_tax_multiplier
            - net_taxes,
            "multiplicador_empleo_puestos_por_millon": employment_multiplier,
            "multiplicador_empleo_indirecto_puestos_por_millon": employment_multiplier
            - employment,
            "encadenamiento_atras_directo_normalizado": backward_direct,
            "indice_dispersion_adelante_directo_normalizado": forward_direct,
            "encadenamiento_adelante_directo_normalizado": forward_direct,
            "encadenamiento_atras_normalizado": backward_total,
            "indice_dispersion_adelante_rh_normalizado": forward_total,
            "encadenamiento_adelante_normalizado": forward_total,
            "metodo_indice_adelante": "Rasmussen-Hirschman_filas_L_no_Ghosh",
            "tipo_encadenamiento": _linkage_type(backward_total, forward_total),
        }
    )

    rank_columns = {
        "multiplicador_produccion_domestica": "ranking_multiplicador_produccion",
        "requerimiento_importacion_total": "ranking_requerimiento_importacion",
        "multiplicador_valor_agregado": "ranking_multiplicador_valor_agregado",
        "multiplicador_empleo_puestos_por_millon": "ranking_multiplicador_empleo",
        "encadenamiento_atras_normalizado": "ranking_encadenamiento_atras",
        "indice_dispersion_adelante_rh_normalizado": "ranking_indice_dispersion_adelante_rh",
    }
    for value_column, rank_column in rank_columns.items():
        frame[rank_column] = (
            frame[value_column].rank(method="min", ascending=False).astype(int)
        )
    return frame


def io_indicator_frame(
    *,
    codes: Sequence[str],
    labels: Sequence[str],
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    value_added_coefficients: Sequence[float] | np.ndarray,
    employment_coefficients: Sequence[float] | np.ndarray,
) -> pd.DataFrame:
    """Conserva el cuadro de nueve indicadores publicado en la versión 1.0.0.

    La suma normalizada de filas de ``L`` se conserva bajo su nombre legado
    ``encadenamiento_adelante_normalizado`` para compatibilidad. Su semántica es
    un índice Rasmussen-Hirschman de sensibilidad de dispersión, no un
    multiplicador de oferta ni un resultado de un modelo Ghosh.
    """

    codes_tuple, labels_tuple = _validate_codes_labels(codes, labels)
    n = len(codes_tuple)
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    a_m = _as_square(a_imported, n, "a_imported")
    value_added = _as_vector(
        value_added_coefficients, n, "value_added_coefficients"
    )
    employment = _as_vector(
        employment_coefficients, n, "employment_coefficients"
    )
    output_multiplier = leontief.sum(axis=0)
    row_dispersion = leontief.sum(axis=1)
    direct_import = a_m.sum(axis=0)

    return pd.DataFrame(
        {
            "codigo": codes_tuple,
            "producto": labels_tuple,
            "multiplicador_produccion_domestica": output_multiplier,
            "encadenamiento_atras_normalizado": normalized_linkage(
                output_multiplier, "encadenamiento_atras_normalizado"
            ),
            "encadenamiento_adelante_normalizado": normalized_linkage(
                row_dispersion, "encadenamiento_adelante_normalizado"
            ),
            "coeficiente_importacion_directa": direct_import,
            "requerimiento_importacion_total": (a_m @ leontief).sum(axis=0),
            "multiplicador_valor_agregado": value_added @ leontief,
            "multiplicador_empleo_puestos_por_millon": employment @ leontief,
        }
    )


def shock_vector(
    codes: Sequence[str],
    shock: Mapping[str, float] | Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Convierte un mapeo por código o una secuencia en un vector ordenado."""

    code_tuple = tuple(codes)
    n = len(code_tuple)
    if isinstance(shock, Mapping):
        unknown = sorted(set(shock) - set(code_tuple))
        if unknown:
            raise ValueError(f"El choque contiene códigos desconocidos: {unknown}")
        vector = np.asarray([float(shock.get(code, 0.0)) for code in code_tuple])
    else:
        vector = _as_vector(shock, n, "shock")
    if not np.isfinite(vector).all():
        raise ValueError("shock contiene valores no finitos")
    return vector


def demand_shock_impact(
    *,
    codes: Sequence[str],
    labels: Sequence[str],
    shock: Mapping[str, float] | Sequence[float] | np.ndarray,
    a_domestic: np.ndarray,
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    value_added_coefficients: Sequence[float] | np.ndarray,
    employment_coefficients: Sequence[float] | np.ndarray,
    net_tax_coefficients: Sequence[float] | np.ndarray | None = None,
    zero_output: Sequence[bool] | np.ndarray | None = None,
    tolerance: float = 1e-10,
) -> DemandShockImpact:
    """Descompone un choque en efectos directos, indirectos y totales.

    El choque se interpreta a precios básicos. Producción, importaciones
    intermedias y VAB se expresan en la misma unidad monetaria del choque. El
    empleo se expresa en puestos de trabajo cuando el coeficiente se proporciona
    en puestos por unidad monetaria. Si se aporta el coeficiente de impuestos,
    este representa exclusivamente impuestos netos sobre insumos intermedios
    asociados; no permite calcular PIB a precios de mercado porque faltan tasas
    por producto para los usos finales.
    """

    code_tuple, label_tuple = _validate_codes_labels(codes, labels)
    n = len(code_tuple)
    a_d = _as_square(a_domestic, n, "a_domestic")
    a_m = _as_square(a_imported, n, "a_imported")
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    value_added = _as_vector(
        value_added_coefficients, n, "value_added_coefficients"
    )
    employment = _as_vector(
        employment_coefficients, n, "employment_coefficients"
    )
    net_taxes = (
        np.zeros(n, dtype=float)
        if net_tax_coefficients is None
        else _as_vector(net_tax_coefficients, n, "net_tax_coefficients")
    )
    zero = (
        np.zeros(n, dtype=bool)
        if zero_output is None
        else np.asarray(zero_output, dtype=bool)
    )
    if zero.shape != (n,):
        raise ValueError(f"zero_output debe tener longitud {n}")
    final_demand = shock_vector(code_tuple, shock)

    production_direct = final_demand
    production_total = leontief @ final_demand
    production_indirect = production_total - production_direct
    imports_direct = a_m @ production_direct
    imports_indirect = a_m @ production_indirect
    imports_total = imports_direct + imports_indirect
    value_added_direct = value_added * production_direct
    value_added_indirect = value_added * production_indirect
    value_added_total = value_added_direct + value_added_indirect
    net_taxes_direct = net_taxes * production_direct
    net_taxes_indirect = net_taxes * production_indirect
    net_taxes_total = net_taxes_direct + net_taxes_indirect
    employment_direct = employment * production_direct
    employment_indirect = employment * production_indirect
    employment_total = employment_direct + employment_indirect

    by_product = pd.DataFrame(
        {
            "codigo": code_tuple,
            "producto": label_tuple,
            "producto_produccion_cero": zero,
            "apto_para_simulacion": ~zero,
            "estado_simulacion": np.where(
                zero, "solo_completitud_algebraica", "apto"
            ),
            "choque_demanda_final": final_demand,
            "produccion_directa": production_direct,
            "produccion_indirecta": production_indirect,
            "produccion_total": production_total,
            "importaciones_intermedias_directas": imports_direct,
            "importaciones_intermedias_indirectas": imports_indirect,
            "importaciones_intermedias_totales": imports_total,
            "valor_agregado_directo": value_added_direct,
            "valor_agregado_indirecto": value_added_indirect,
            "valor_agregado_total": value_added_total,
            "impuestos_netos_sobre_insumos_intermedios_asociados_directos": net_taxes_direct,
            "impuestos_netos_sobre_insumos_intermedios_asociados_indirectos": net_taxes_indirect,
            "impuestos_netos_sobre_insumos_intermedios_asociados_totales": net_taxes_total,
            "empleo_directo_puestos": employment_direct,
            "empleo_indirecto_puestos": employment_indirect,
            "empleo_total_puestos": employment_total,
        }
    )
    totals = {
        "choque_demanda_final": float(final_demand.sum()),
        "produccion_directa": float(production_direct.sum()),
        "produccion_indirecta": float(production_indirect.sum()),
        "produccion_total": float(production_total.sum()),
        "importaciones_intermedias_directas": float(imports_direct.sum()),
        "importaciones_intermedias_indirectas": float(imports_indirect.sum()),
        "importaciones_intermedias_totales": float(imports_total.sum()),
        "valor_agregado_directo": float(value_added_direct.sum()),
        "valor_agregado_indirecto": float(value_added_indirect.sum()),
        "valor_agregado_total": float(value_added_total.sum()),
        "impuestos_netos_sobre_insumos_intermedios_asociados_directos": float(
            net_taxes_direct.sum()
        ),
        "impuestos_netos_sobre_insumos_intermedios_asociados_indirectos": float(
            net_taxes_indirect.sum()
        ),
        "impuestos_netos_sobre_insumos_intermedios_asociados_totales": float(
            net_taxes_total.sum()
        ),
        "empleo_directo_puestos": float(employment_direct.sum()),
        "empleo_indirecto_puestos": float(employment_indirect.sum()),
        "empleo_total_puestos": float(employment_total.sum()),
    }

    residuals = {
        "CHOQUE-01": (
            "dx = dy + A_domestica @ dx",
            float(
                np.max(
                    np.abs(production_total - final_demand - a_d @ production_total)
                )
            ),
        ),
        "CHOQUE-02": (
            "produccion total = directa + indirecta",
            float(
                np.max(
                    np.abs(
                        production_total - production_direct - production_indirect
                    )
                )
            ),
        ),
        "CHOQUE-03": (
            "importaciones totales = directas + indirectas",
            float(
                np.max(np.abs(imports_total - imports_direct - imports_indirect))
            ),
        ),
        "CHOQUE-04": (
            "VAB total = directo + indirecto",
            float(
                np.max(
                    np.abs(value_added_total - value_added_direct - value_added_indirect)
                )
            ),
        ),
        "CHOQUE-05": (
            "empleo total = directo + indirecto",
            float(
                np.max(
                    np.abs(employment_total - employment_direct - employment_indirect)
                )
            ),
        ),
    }
    if net_tax_coefficients is not None:
        residuals["CHOQUE-06"] = (
            "choque a precios básicos = importaciones intermedias + impuestos netos sobre insumos intermedios asociados + VAB; no es PIB",
            abs(
                float(final_demand.sum())
                - float(imports_total.sum())
                - float(net_taxes_total.sum())
                - float(value_added_total.sum())
            ),
        )
    checks = pd.DataFrame(
        [
            {
                "control_id": control_id,
                "descripcion": description,
                "valor_max_abs": value,
                "tolerancia": tolerance,
                "estado": "APROBADO" if value <= tolerance else "FALLÓ",
            }
            for control_id, (description, value) in residuals.items()
        ]
    )
    if zero_output is not None:
        shock_not_suitable = (
            float(np.max(np.abs(final_demand[zero]))) if zero.any() else 0.0
        )
        checks = pd.concat(
            [
                checks,
                pd.DataFrame(
                    [
                        {
                            "control_id": "CHOQUE-07",
                            "descripcion": "El choque no asigna demanda final a productos con produccion base cero",
                            "valor_max_abs": shock_not_suitable,
                            "tolerancia": tolerance,
                            "estado": (
                                "APROBADO"
                                if shock_not_suitable <= tolerance
                                else "NO_APTO_PARA_SIMULACION"
                            ),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return DemandShockImpact(by_product=by_product, totals=totals, checks=checks)


def unit_demand_shock_summary(
    *,
    codes: Sequence[str],
    labels: Sequence[str],
    a_domestic: np.ndarray,
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    value_added_coefficients: Sequence[float] | np.ndarray,
    employment_coefficients: Sequence[float] | np.ndarray,
    net_tax_coefficients: Sequence[float] | np.ndarray | None = None,
    zero_output: Sequence[bool] | np.ndarray | None = None,
) -> pd.DataFrame:
    """Resume el impacto agregado de un choque unitario en cada producto.

    Los productos con producción base cero se conservan para completar el
    sistema algebraico, pero se marcan como no aptos para una simulación
    sustantiva: su columna de ``L`` reproduce mecánicamente el vector unitario.
    """

    indicators = complete_io_indicator_frame(
        codes=codes,
        labels=labels,
        a_domestic=a_domestic,
        a_imported=a_imported,
        leontief_domestic=leontief_domestic,
        value_added_coefficients=value_added_coefficients,
        employment_coefficients=employment_coefficients,
        net_tax_coefficients=net_tax_coefficients,
    )
    n = len(indicators)
    zero = (
        np.zeros(n, dtype=bool)
        if zero_output is None
        else np.asarray(zero_output, dtype=bool)
    )
    if zero.shape != (n,):
        raise ValueError(f"zero_output debe tener longitud {n}")
    a_d = _as_square(a_domestic, n, "a_domestic")
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    shock_residual = np.max(
        np.abs(leontief - np.eye(n) - a_d @ leontief), axis=0
    )
    return pd.DataFrame(
        {
            "codigo": indicators["codigo"],
            "producto": indicators["producto"],
            "producto_produccion_cero": zero,
            "apto_para_simulacion": ~zero,
            "estado_simulacion": np.where(
                zero, "solo_completitud_algebraica", "apto"
            ),
            "choque_demanda_final_unitario": np.ones(n),
            "produccion_directa": np.ones(n),
            "produccion_indirecta": indicators[
                "multiplicador_produccion_indirecta"
            ],
            "produccion_total": indicators["multiplicador_produccion_domestica"],
            "importaciones_intermedias_directas": indicators[
                "coeficiente_importacion_directa"
            ],
            "importaciones_intermedias_indirectas": indicators[
                "requerimiento_importacion_indirecta"
            ],
            "importaciones_intermedias_totales": indicators[
                "requerimiento_importacion_total"
            ],
            "valor_agregado_directo": indicators[
                "coeficiente_valor_agregado_directo"
            ],
            "valor_agregado_indirecto": indicators[
                "multiplicador_valor_agregado_indirecto"
            ],
            "valor_agregado_total": indicators["multiplicador_valor_agregado"],
            "impuestos_netos_sobre_insumos_intermedios_asociados_directos": indicators[
                "coeficiente_impuestos_netos_sobre_insumos_intermedios_asociados_directo"
            ],
            "impuestos_netos_sobre_insumos_intermedios_asociados_indirectos": indicators[
                "impuestos_netos_sobre_insumos_intermedios_asociados_indirecto"
            ],
            "impuestos_netos_sobre_insumos_intermedios_asociados_totales": indicators[
                "impuestos_netos_sobre_insumos_intermedios_asociados_total"
            ],
            "empleo_directo_puestos": indicators[
                "coeficiente_empleo_directo_puestos_por_millon"
            ],
            "empleo_indirecto_puestos": indicators[
                "multiplicador_empleo_indirecto_puestos_por_millon"
            ],
            "empleo_total_puestos": indicators[
                "multiplicador_empleo_puestos_por_millon"
            ],
            "residuo_identidad_produccion_max_abs": shock_residual,
        }
    )


def io_ranking_frame(indicators: pd.DataFrame) -> pd.DataFrame:
    """Convierte los principales indicadores en rankings largos y auditables."""

    required = {"codigo", "producto"}
    if not required.issubset(indicators.columns):
        raise ValueError("indicators no contiene codigo y producto")
    metrics = (
        (
            "multiplicador_produccion_domestica",
            "Multiplicador de producción doméstica",
            "millones por millón de demanda final",
        ),
        (
            "requerimiento_importacion_total",
            "Requerimiento total de importaciones intermedias",
            "millones por millón de demanda final",
        ),
        (
            "multiplicador_valor_agregado",
            "Multiplicador de valor agregado",
            "millones por millón de demanda final",
        ),
        (
            "multiplicador_empleo_puestos_por_millon",
            "Multiplicador de empleo",
            "puestos por millón de demanda final",
        ),
        (
            "encadenamiento_atras_normalizado",
            "Encadenamiento hacia atrás normalizado",
            "índice; media = 1",
        ),
        (
            "indice_dispersion_adelante_rh_normalizado",
            "Índice de sensibilidad de dispersión hacia adelante RH (filas de L)",
            "índice; media = 1",
        ),
    )
    frames: list[pd.DataFrame] = []
    for metric_id, metric_label, unit in metrics:
        if metric_id not in indicators.columns:
            raise ValueError(f"Falta el indicador requerido: {metric_id}")
        identity_columns = ["codigo", "producto"]
        for optional in (
            "producto_produccion_cero",
            "apto_para_simulacion",
            "estado_simulacion",
        ):
            if optional in indicators.columns:
                identity_columns.append(optional)
        ranking = indicators[identity_columns + [metric_id]].copy()
        ranking = ranking.sort_values(
            [metric_id, "codigo"], ascending=[False, True], kind="mergesort"
        ).reset_index(drop=True)
        ranking.insert(
            0,
            "rango_con_empates",
            ranking[metric_id].rank(method="min", ascending=False).astype(int),
        )
        ranking.insert(0, "posicion_ordenada", np.arange(1, len(ranking) + 1))
        ranking.insert(0, "criterio_desempate", "codigo_ascendente")
        ranking.insert(0, "unidad", unit)
        ranking.insert(0, "indicador", metric_label)
        ranking.insert(0, "indicador_id", metric_id)
        ranking = ranking.rename(columns={metric_id: "valor"})
        frames.append(ranking)
    return pd.concat(frames, ignore_index=True)


def io_identity_checks(
    *,
    a_domestic: np.ndarray,
    a_imported: np.ndarray,
    leontief_domestic: np.ndarray,
    a_total_inputs: np.ndarray | None = None,
    output: Sequence[float] | np.ndarray | None = None,
    z_domestic: np.ndarray | None = None,
    z_imported: np.ndarray | None = None,
    final_domestic_balanced: Sequence[float] | np.ndarray | None = None,
    value_added_coefficients: Sequence[float] | np.ndarray | None = None,
    net_tax_coefficients: Sequence[float] | np.ndarray | None = None,
    tolerance: float = 1e-9,
) -> pd.DataFrame:
    """Valida orientación, inversa, balances y coeficientes del sistema IO."""

    a_d = np.asarray(a_domestic, dtype=float)
    if a_d.ndim != 2 or a_d.shape[0] != a_d.shape[1]:
        raise ValueError("a_domestic debe ser cuadrada")
    n = a_d.shape[0]
    a_d = _as_square(a_d, n, "a_domestic")
    a_m = _as_square(a_imported, n, "a_imported")
    leontief = _as_square(leontief_domestic, n, "leontief_domestic")
    identity = np.eye(n)
    records: list[dict[str, Any]] = []

    def add(control_id: str, description: str, residual: np.ndarray | float) -> None:
        value = float(np.max(np.abs(np.asarray(residual, dtype=float))))
        records.append(
            {
                "control_id": control_id,
                "descripcion": description,
                "valor_max_abs": value,
                "tolerancia": tolerance,
                "estado": "APROBADO" if value <= tolerance else "FALLÓ",
            }
        )

    add("IO-01", "(I - A_domestica) @ L = I", (identity - a_d) @ leontief - identity)
    add("IO-02", "L @ (I - A_domestica) = I", leontief @ (identity - a_d) - identity)
    add("IO-03", "L = I + A_domestica @ L", leontief - identity - a_d @ leontief)

    if a_total_inputs is not None:
        a_total = _as_square(a_total_inputs, n, "a_total_inputs")
        add("IO-04", "A_total = A_domestica + A_importada", a_total - a_d - a_m)

    output_vector: np.ndarray | None = None
    positive_output: np.ndarray | None = None
    if output is not None:
        output_vector = _as_vector(output, n, "output")
        positive_output = output_vector != 0
        if z_domestic is not None:
            z_d = _as_square(z_domestic, n, "z_domestic")
            add(
                "IO-05",
                "Z_domestica = A_domestica @ diag(x)",
                z_d - a_d * output_vector[np.newaxis, :],
            )
        if z_imported is not None:
            z_m = _as_square(z_imported, n, "z_imported")
            add(
                "IO-06",
                "Z_importada = A_importada @ diag(x)",
                z_m - a_m * output_vector[np.newaxis, :],
            )
        if final_domestic_balanced is not None:
            final_demand = _as_vector(
                final_domestic_balanced, n, "final_domestic_balanced"
            )
            add(
                "IO-07",
                "x = A_domestica @ x + y_domestica_balanceada",
                output_vector - a_d @ output_vector - final_demand,
            )
            add(
                "IO-08",
                "x = L @ y_domestica_balanceada",
                output_vector - leontief @ final_demand,
            )

    if value_added_coefficients is not None and net_tax_coefficients is not None:
        value_added = _as_vector(
            value_added_coefficients, n, "value_added_coefficients"
        )
        net_taxes = _as_vector(net_tax_coefficients, n, "net_tax_coefficients")
        coefficient_sum = a_d.sum(axis=0) + a_m.sum(axis=0) + value_added + net_taxes
        residual = coefficient_sum - 1.0
        if positive_output is not None:
            residual = residual[positive_output]
        add(
            "IO-09",
            "Insumos domésticos + importados + impuestos netos sobre insumos intermedios + VAB suman uno por columna",
            residual,
        )

    backward = normalized_linkage(leontief.sum(axis=0), "backward")
    forward = normalized_linkage(leontief.sum(axis=1), "forward")
    add("IO-10", "Media del encadenamiento hacia atrás normalizado = 1", backward.mean() - 1)
    add(
        "IO-11",
        "Media del índice de sensibilidad de dispersión hacia adelante RH = 1; no Ghosh",
        forward.mean() - 1,
    )
    return pd.DataFrame(records)


def _read_matrix(path: Path, codes: tuple[str, ...]) -> np.ndarray:
    frame = pd.read_csv(path)
    if tuple(frame["codigo"].astype(str)) != codes:
        raise ValueError(f"Los códigos de fila no coinciden en {path}")
    if tuple(frame.columns[2:]) != codes:
        raise ValueError(f"Los códigos de columna no coinciden en {path}")
    matrix = frame.iloc[:, 2:].to_numpy(dtype=float)
    return _as_square(matrix, len(codes), path.name)


def _aligned_frame(path: Path, codes: tuple[str, ...]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if tuple(frame["codigo"].astype(str)) != codes:
        raise ValueError(f"El orden de productos no coincide en {path}")
    return frame


def load_canonical_io_data(root: str | Path) -> CanonicalIoData:
    """Carga el sistema analítico desde las salidas canónicas publicadas."""

    root_path = Path(root)
    results = root_path / "02_resultados_y_diccionario"
    matrices = results / "matrices"
    vectors = results / "vectores"
    products = pd.read_csv(results / "productos_2013.csv")
    codes = tuple(products["codigo"].astype(str))
    labels = tuple(products["producto"].astype(str))
    _validate_codes_labels(codes, labels)

    output_frame = _aligned_frame(vectors / "produccion_y_utilizacion_2013.csv", codes)
    coefficients = _aligned_frame(vectors / "coeficientes_primarios_2013.csv", codes)
    final_demand = _aligned_frame(vectors / "demanda_final_domestica_2013.csv", codes)
    output = output_frame["produccion_precios_basicos"].to_numpy(dtype=float)
    jobs = output_frame["puestos_trabajo"].to_numpy(dtype=float)

    return CanonicalIoData(
        codes=codes,
        labels=labels,
        output=output,
        jobs=jobs,
        legacy_row_174=output_frame["producto_interno_bruto"].to_numpy(
            dtype=float
        ),
        final_domestic_balanced=final_demand["demanda_final_balanceada"].to_numpy(
            dtype=float
        ),
        z_domestic=_read_matrix(matrices / "Z_domestica_2013.csv", codes),
        z_imported=_read_matrix(matrices / "Z_importada_2013.csv", codes),
        a_domestic=_read_matrix(matrices / "A_domestica_2013.csv", codes),
        a_imported=_read_matrix(matrices / "A_importada_2013.csv", codes),
        a_total_inputs=_read_matrix(matrices / "A_total_insumos_2013.csv", codes),
        leontief_domestic=_read_matrix(
            matrices / "Leontief_domestica_2013.csv", codes
        ),
        value_added_coefficients=coefficients["valor_agregado_bruto"].to_numpy(
            dtype=float
        ),
        net_tax_coefficients=coefficients["impuestos_netos_productos"].to_numpy(
            dtype=float
        ),
        employment_coefficients=safe_coefficient(jobs, output),
    )


def legacy_row_174_semantic_control(data: CanonicalIoData) -> pd.DataFrame:
    """Marca el vector legado de fila 174 como no aditivo y no usado.

    El vector D:EY de la fila 174 equivale a producción a precios básicos más
    impuestos netos sobre insumos intermedios por columna. No distribuye los
    impuestos netos sobre usos finales y, por ello, no es un vector de PIB ni
    sirve para construir un multiplicador de PIB.
    """

    output_total = float(data.output.sum())
    intermediate_net_taxes = float(
        (data.net_tax_coefficients * data.output).sum()
    )
    legacy_total = float(data.legacy_row_174.sum())
    legacy_product_residual = (
        data.legacy_row_174
        - data.output
        - data.net_tax_coefficients * data.output
    )
    value_added_total = float(
        (data.value_added_coefficients * data.output).sum()
    )
    return pd.DataFrame(
        [
            {
                "campo_legado": "produccion_y_utilizacion_2013.csv::producto_interno_bruto",
                "rango_fuente": "MIP_152x152!D174:EY174",
                "semantica_reconstruida": "produccion_precios_basicos_mas_impuestos_netos_sobre_insumos_intermedios",
                "apto_para_agregacion_pib": False,
                "usado_en_modelo_analitico": False,
                "suma_vector_legado_millones_quetzales": legacy_total,
                "produccion_precios_basicos_millones_quetzales": output_total,
                "impuestos_netos_insumos_intermedios_millones_quetzales": intermediate_net_taxes,
                "residuo_identidad_vector_legado": legacy_total
                - output_total
                - intermediate_net_taxes,
                "residuo_identidad_vector_legado_max_abs_por_producto": float(
                    np.max(np.abs(legacy_product_residual))
                ),
                "valor_agregado_bruto_oficial_millones_quetzales": value_added_total,
                "impuestos_netos_todos_los_usos_oficial_millones_quetzales": OFFICIAL_NET_TAXES_ALL_USES_2013_MILLION_QUETZALES,
                "pib_oficial_ez174_fj174_millones_quetzales": OFFICIAL_GDP_2013_MILLION_QUETZALES,
                "residuo_identidad_pib_oficial": OFFICIAL_GDP_2013_MILLION_QUETZALES
                - value_added_total
                - OFFICIAL_NET_TAXES_ALL_USES_2013_MILLION_QUETZALES,
                "diferencia_legado_menos_pib_oficial": legacy_total
                - OFFICIAL_GDP_2013_MILLION_QUETZALES,
                "estado": "NO_USAR_COMO_PIB",
            }
        ]
    )


def analytical_output_frames(root: str | Path) -> dict[str, pd.DataFrame]:
    """Construye todas las salidas analíticas sin escribir archivos."""

    data = load_canonical_io_data(root)
    indicators = complete_io_indicator_frame(
        codes=data.codes,
        labels=data.labels,
        a_domestic=data.a_domestic,
        a_imported=data.a_imported,
        leontief_domestic=data.leontief_domestic,
        value_added_coefficients=data.value_added_coefficients,
        employment_coefficients=data.employment_coefficients,
        net_tax_coefficients=data.net_tax_coefficients,
        zero_output=data.output == 0,
    )
    unit_shocks = unit_demand_shock_summary(
        codes=data.codes,
        labels=data.labels,
        a_domestic=data.a_domestic,
        a_imported=data.a_imported,
        leontief_domestic=data.leontief_domestic,
        value_added_coefficients=data.value_added_coefficients,
        employment_coefficients=data.employment_coefficients,
        net_tax_coefficients=data.net_tax_coefficients,
        zero_output=data.output == 0,
    )
    rankings = io_ranking_frame(indicators)
    checks = io_identity_checks(
        a_domestic=data.a_domestic,
        a_imported=data.a_imported,
        leontief_domestic=data.leontief_domestic,
        a_total_inputs=data.a_total_inputs,
        output=data.output,
        z_domestic=data.z_domestic,
        z_imported=data.z_imported,
        final_domestic_balanced=data.final_domestic_balanced,
        value_added_coefficients=data.value_added_coefficients,
        net_tax_coefficients=data.net_tax_coefficients,
    )
    return {
        "indicadores_io_completos_2013.csv": indicators,
        "impactos_choque_unitario_demanda_final_2013.csv": unit_shocks,
        "rankings_io_por_producto_2013.csv": rankings,
        "validacion_identidades_io_2013.csv": checks,
        "control_semantico_vector_fila174_2013.csv": legacy_row_174_semantic_control(
            data
        ),
    }


def write_analytical_outputs(root: str | Path) -> list[Path]:
    """Escribe salidas analíticas derivadas sin modificar matrices canónicas."""

    root_path = Path(root)
    output_dir = root_path / "02_resultados_y_diccionario" / "indicadores"
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, frame in analytical_output_frames(root_path).items():
        path = output_dir / name
        frame.to_csv(
            path,
            index=False,
            encoding="utf-8",
            float_format=FLOAT_FORMAT,
            lineterminator="\n",
        )
        paths.append(path)
    return paths


__all__ = [
    "CanonicalIoData",
    "DemandShockImpact",
    "analytical_output_frames",
    "complete_io_indicator_frame",
    "demand_shock_impact",
    "io_identity_checks",
    "io_indicator_frame",
    "io_ranking_frame",
    "legacy_row_174_semantic_control",
    "load_canonical_io_data",
    "normalized_linkage",
    "safe_coefficient",
    "shock_vector",
    "unit_demand_shock_summary",
    "write_analytical_outputs",
]
