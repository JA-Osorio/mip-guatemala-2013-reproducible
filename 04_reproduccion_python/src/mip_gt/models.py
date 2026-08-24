from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class SourceLayout:
    sheet_domestic: str
    sheet_imported: str
    product_header_row: int
    product_first_row: int
    product_count: int
    code_column: int
    label_column: int
    matrix_first_column: int
    total_intermediate_column: int
    exports_column: int
    households_column: int
    npish_column: int
    government_column: int
    total_consumption_column: int
    gfcf_column: int
    inventories_column: int
    total_capital_column: int
    cif_fob_column: int
    total_utilization_column: int
    row_domestic_intermediate: int
    row_imported_intermediate: int
    row_taxes_products: int
    row_subsidies_products: int
    row_net_taxes_products: int
    row_value_added: int
    row_output: int
    row_gdp: int
    row_value_added_components: int
    row_compensation: int
    row_taxes_production_imports: int
    row_subsidies_production: int
    row_operating_surplus: int
    row_mixed_income: int
    row_jobs: int

    @property
    def product_last_row(self) -> int:
        return self.product_first_row + self.product_count - 1

    @property
    def matrix_last_column(self) -> int:
        return self.matrix_first_column + self.product_count - 1


@dataclass(frozen=True)
class MipSourceData:
    source_path: Path
    source_sha256: str
    codes: tuple[str, ...]
    labels: tuple[str, ...]
    column_codes: tuple[str, ...]
    z_domestic: np.ndarray
    z_imported: np.ndarray
    final_domestic: dict[str, np.ndarray]
    final_imported: dict[str, np.ndarray]
    total_intermediate_domestic_source: np.ndarray
    total_intermediate_imported_source: np.ndarray
    total_utilization_domestic: np.ndarray
    total_utilization_imported: np.ndarray
    domestic_intermediate_by_column_source: np.ndarray
    imported_intermediate_by_column_source: np.ndarray
    taxes_products: np.ndarray
    subsidies_products: np.ndarray
    net_taxes_products: np.ndarray
    value_added: np.ndarray
    output: np.ndarray
    gdp: np.ndarray
    value_added_components_source: np.ndarray
    compensation: np.ndarray
    taxes_production_imports: np.ndarray
    subsidies_production: np.ndarray
    operating_surplus: np.ndarray
    mixed_income: np.ndarray
    jobs: np.ndarray


@dataclass(frozen=True)
class MipSystem:
    source: MipSourceData
    a_domestic: np.ndarray
    a_imported: np.ndarray
    a_total_inputs: np.ndarray
    leontief_domestic: np.ndarray
    final_domestic_components: np.ndarray
    final_domestic_from_source_total: np.ndarray
    final_domestic_balanced: np.ndarray
    supply_use_gap: np.ndarray
    final_imported_components: np.ndarray
    final_imported_from_source_total: np.ndarray
    primary_coefficients: dict[str, np.ndarray]
    spectral_radius: float
    condition_number: float
    inverse_residual_max_abs: float


@dataclass(frozen=True)
class ControlResult:
    control_id: str
    description: str
    status: str
    value: float | int | str
    tolerance: float | int | str
    detail: str
    mandatory: bool = True

