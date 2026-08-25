"""Herramientas reproducibles para la MIP producto por producto de Guatemala 2013."""

from .analysis import (
    DemandShockImpact,
    complete_io_indicator_frame,
    demand_shock_impact,
    io_identity_checks,
    io_ranking_frame,
    legacy_row_174_semantic_control,
    load_canonical_io_data,
    unit_demand_shock_summary,
    write_analytical_outputs,
)

__version__ = "1.1.0"

__all__ = [
    "DemandShockImpact",
    "complete_io_indicator_frame",
    "demand_shock_impact",
    "io_identity_checks",
    "io_ranking_frame",
    "legacy_row_174_semantic_control",
    "load_canonical_io_data",
    "unit_demand_shock_summary",
    "write_analytical_outputs",
]
