from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "04_reproduccion_python" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SOURCE = (
    ROOT
    / "00_trazabilidad_fuentes"
    / "fuentes_originales_no_redistribuidas"
    / "MIP_AR2013_NPG.xlsx"
)
RESULTS = ROOT / "02_resultados_y_diccionario"
ANALYTICS = RESULTS / "indicadores"

from mip_gt.analysis import (  # noqa: E402
    analytical_output_frames,
    complete_io_indicator_frame,
    demand_shock_impact,
    io_indicator_frame,
    legacy_row_174_semantic_control,
    load_canonical_io_data,
)


class OrientacionSinteticaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.codes = ("P001", "P002")
        self.labels = ("Producto 1", "Producto 2")
        self.a_domestic = np.array([[0.10, 0.20], [0.30, 0.10]])
        self.a_imported = np.array([[0.05, 0.02], [0.01, 0.04]])
        self.leontief = np.linalg.inv(np.eye(2) - self.a_domestic)
        self.value_added = np.array([0.54, 0.55])
        self.net_taxes = np.array([0.00, 0.09])
        self.employment = np.array([2.0, 3.0])

    def test_choque_es_vector_columna_y_conserva_orientacion(self) -> None:
        shock = {"P001": 2.0, "P002": 1.0}
        expected_shock = np.array([2.0, 1.0])
        expected_output = np.linalg.solve(
            np.eye(2) - self.a_domestic, expected_shock
        )
        impact = demand_shock_impact(
            codes=self.codes,
            labels=self.labels,
            shock=shock,
            a_domestic=self.a_domestic,
            a_imported=self.a_imported,
            leontief_domestic=self.leontief,
            value_added_coefficients=self.value_added,
            employment_coefficients=self.employment,
            net_tax_coefficients=self.net_taxes,
        )
        np.testing.assert_allclose(
            impact.by_product["produccion_total"], expected_output, atol=1e-14
        )
        np.testing.assert_allclose(
            impact.by_product["importaciones_intermedias_totales"],
            self.a_imported @ expected_output,
            atol=1e-14,
        )
        np.testing.assert_allclose(
            impact.by_product["valor_agregado_total"],
            self.value_added * expected_output,
            atol=1e-14,
        )
        np.testing.assert_allclose(
            impact.by_product["empleo_total_puestos"],
            self.employment * expected_output,
            atol=1e-14,
        )
        self.assertTrue((impact.checks["estado"] == "APROBADO").all())
        self.assertEqual(
            set(impact.checks["control_id"]),
            {
                "CHOQUE-01",
                "CHOQUE-02",
                "CHOQUE-03",
                "CHOQUE-04",
                "CHOQUE-05",
                "CHOQUE-06",
            },
        )
        self.assertAlmostEqual(
            impact.totals["choque_demanda_final"],
            impact.totals["importaciones_intermedias_totales"]
            + impact.totals[
                "impuestos_netos_sobre_insumos_intermedios_asociados_totales"
            ]
            + impact.totals["valor_agregado_total"],
            places=13,
        )

    def test_indice_adelante_es_dispersion_rh_y_no_modelo_ghosh(self) -> None:
        indicators = complete_io_indicator_frame(
            codes=self.codes,
            labels=self.labels,
            a_domestic=self.a_domestic,
            a_imported=self.a_imported,
            leontief_domestic=self.leontief,
            value_added_coefficients=self.value_added,
            employment_coefficients=self.employment,
            net_tax_coefficients=self.net_taxes,
        )
        expected = self.leontief.sum(axis=1) / self.leontief.sum(axis=1).mean()
        np.testing.assert_allclose(
            indicators["indice_dispersion_adelante_rh_normalizado"], expected
        )
        np.testing.assert_allclose(
            indicators["encadenamiento_adelante_normalizado"], expected
        )
        self.assertEqual(
            set(indicators["metodo_indice_adelante"]),
            {"Rasmussen-Hirschman_filas_L_no_Ghosh"},
        )

    def test_api_legacy_admite_sistema_sin_consumo_intermedio(self) -> None:
        indicators = io_indicator_frame(
            codes=self.codes,
            labels=self.labels,
            a_imported=np.zeros((2, 2)),
            leontief_domestic=np.eye(2),
            value_added_coefficients=np.ones(2),
            employment_coefficients=np.array([2.0, 3.0]),
        )
        np.testing.assert_allclose(
            indicators["multiplicador_produccion_domestica"], 1.0
        )
        np.testing.assert_allclose(
            indicators["encadenamiento_atras_normalizado"], 1.0
        )
        np.testing.assert_allclose(
            indicators["encadenamiento_adelante_normalizado"], 1.0
        )


class SalidasAnaliticasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_canonical_io_data(ROOT)
        cls.frames = analytical_output_frames(ROOT)

    def test_indicadores_completos_y_encadenamientos(self) -> None:
        indicators = self.frames["indicadores_io_completos_2013.csv"]
        self.assertEqual(len(indicators), 152)
        self.assertEqual(indicators["codigo"].tolist(), list(self.data.codes))
        self.assertAlmostEqual(
            indicators["encadenamiento_atras_normalizado"].mean(), 1.0, places=13
        )
        self.assertAlmostEqual(
            indicators["indice_dispersion_adelante_rh_normalizado"].mean(),
            1.0,
            places=13,
        )
        np.testing.assert_allclose(
            indicators["indice_dispersion_adelante_rh_normalizado"],
            indicators["encadenamiento_adelante_normalizado"],
        )
        self.assertEqual(
            set(indicators["metodo_indice_adelante"]),
            {"Rasmussen-Hirschman_filas_L_no_Ghosh"},
        )

    def test_choque_unitario_p010_reconcilia_multiplicadores(self) -> None:
        product_index = self.data.codes.index("P010")
        impact = demand_shock_impact(
            codes=self.data.codes,
            labels=self.data.labels,
            shock={"P010": 1.0},
            a_domestic=self.data.a_domestic,
            a_imported=self.data.a_imported,
            leontief_domestic=self.data.leontief_domestic,
            value_added_coefficients=self.data.value_added_coefficients,
            employment_coefficients=self.data.employment_coefficients,
            net_tax_coefficients=self.data.net_tax_coefficients,
            zero_output=self.data.output == 0,
        )
        output_vector = self.data.leontief_domestic[:, product_index]
        self.assertAlmostEqual(
            impact.totals["produccion_total"], output_vector.sum(), places=13
        )
        self.assertAlmostEqual(
            impact.totals["importaciones_intermedias_totales"],
            (self.data.a_imported @ output_vector).sum(),
            places=13,
        )
        self.assertAlmostEqual(
            impact.totals["valor_agregado_total"],
            (self.data.value_added_coefficients * output_vector).sum(),
            places=13,
        )
        self.assertAlmostEqual(
            impact.totals[
                "impuestos_netos_sobre_insumos_intermedios_asociados_totales"
            ],
            (self.data.net_tax_coefficients * output_vector).sum(),
            places=13,
        )
        self.assertAlmostEqual(
            impact.totals["empleo_total_puestos"],
            (self.data.employment_coefficients * output_vector).sum(),
            places=10,
        )
        self.assertTrue((impact.checks["estado"] == "APROBADO").all())
        self.assertIn("CHOQUE-06", set(impact.checks["control_id"]))
        self.assertIn("CHOQUE-07", set(impact.checks["control_id"]))

    def test_choque_en_producto_sin_produccion_no_es_sustantivamente_apto(
        self,
    ) -> None:
        impact = demand_shock_impact(
            codes=self.data.codes,
            labels=self.data.labels,
            shock={"P069": 1.0},
            a_domestic=self.data.a_domestic,
            a_imported=self.data.a_imported,
            leontief_domestic=self.data.leontief_domestic,
            value_added_coefficients=self.data.value_added_coefficients,
            employment_coefficients=self.data.employment_coefficients,
            net_tax_coefficients=self.data.net_tax_coefficients,
            zero_output=self.data.output == 0,
        )
        product = impact.by_product.set_index("codigo").loc["P069"]
        self.assertFalse(bool(product["apto_para_simulacion"]))
        self.assertEqual(
            product["estado_simulacion"], "solo_completitud_algebraica"
        )
        control = impact.checks.set_index("control_id").loc["CHOQUE-07"]
        self.assertEqual(control["estado"], "NO_APTO_PARA_SIMULACION")
        self.assertAlmostEqual(control["valor_max_abs"], 1.0)

    def test_rankings_cubren_todos_los_productos(self) -> None:
        rankings = self.frames["rankings_io_por_producto_2013.csv"]
        self.assertEqual(len(rankings), 6 * 152)
        for _, block in rankings.groupby("indicador_id", sort=False):
            self.assertEqual(
                block["posicion_ordenada"].tolist(), list(range(1, 153))
            )
            np.testing.assert_array_equal(
                block["rango_con_empates"],
                block["valor"].rank(method="min", ascending=False).astype(int),
            )
            self.assertEqual(
                set(block["criterio_desempate"]), {"codigo_ascendente"}
            )
            self.assertEqual(set(block["codigo"]), set(self.data.codes))

    def test_productos_sin_produccion_solo_completitud_algebraica(self) -> None:
        expected_codes = {"P069", "P086", "P087", "P089", "P151", "P152"}
        indicators = self.frames["indicadores_io_completos_2013.csv"]
        unit_shocks = self.frames[
            "impactos_choque_unitario_demanda_final_2013.csv"
        ]
        for frame in (indicators, unit_shocks):
            excluded = frame.loc[~frame["apto_para_simulacion"]]
            self.assertEqual(set(excluded["codigo"]), expected_codes)
            self.assertEqual(
                set(excluded["estado_simulacion"]),
                {"solo_completitud_algebraica"},
            )
        zero_indices = [self.data.codes.index(code) for code in sorted(expected_codes)]
        for matrix in (
            self.data.a_domestic,
            self.data.a_imported,
            self.data.a_total_inputs,
        ):
            np.testing.assert_allclose(matrix[:, zero_indices], 0.0, atol=1e-14)
        np.testing.assert_allclose(
            self.data.leontief_domestic[:, zero_indices],
            np.eye(len(self.data.codes))[:, zero_indices],
            atol=1e-14,
        )
        rankings = self.frames["rankings_io_por_producto_2013.csv"]
        for _, block in rankings.groupby("indicador_id", sort=False):
            excluded = block.loc[~block["apto_para_simulacion"]]
            self.assertEqual(set(excluded["codigo"]), expected_codes)
            self.assertEqual(
                set(excluded["estado_simulacion"]),
                {"solo_completitud_algebraica"},
            )
        excluded_shocks = unit_shocks.loc[~unit_shocks["apto_para_simulacion"]]
        np.testing.assert_allclose(excluded_shocks["produccion_total"], 1.0)
        np.testing.assert_allclose(
            excluded_shocks["importaciones_intermedias_totales"], 0.0
        )
        np.testing.assert_allclose(excluded_shocks["valor_agregado_total"], 0.0)
        np.testing.assert_allclose(
            excluded_shocks[
                "impuestos_netos_sobre_insumos_intermedios_asociados_totales"
            ],
            0.0,
        )
        np.testing.assert_allclose(excluded_shocks["empleo_total_puestos"], 0.0)

    def test_vector_fila174_legado_no_se_usa_como_pib(self) -> None:
        control = self.frames["control_semantico_vector_fila174_2013.csv"].iloc[0]
        self.assertFalse(bool(control["apto_para_agregacion_pib"]))
        self.assertFalse(bool(control["usado_en_modelo_analitico"]))
        self.assertEqual(control["estado"], "NO_USAR_COMO_PIB")
        self.assertAlmostEqual(
            control["suma_vector_legado_millones_quetzales"],
            700275.4619025334,
            places=8,
        )
        self.assertAlmostEqual(
            control["impuestos_netos_insumos_intermedios_millones_quetzales"],
            5328.894552322932,
            places=8,
        )
        self.assertAlmostEqual(
            control["impuestos_netos_todos_los_usos_oficial_millones_quetzales"],
            24365.050408378458,
            places=8,
        )
        self.assertAlmostEqual(
            control["pib_oficial_ez174_fj174_millones_quetzales"],
            416383.20533754566,
            places=8,
        )
        self.assertAlmostEqual(
            control["residuo_identidad_vector_legado"], 0.0, places=8
        )
        self.assertLessEqual(
            control[
                "residuo_identidad_vector_legado_max_abs_por_producto"
            ],
            1e-9,
        )
        self.assertAlmostEqual(
            control["residuo_identidad_pib_oficial"], 0.0, places=8
        )
        for name in (
            "indicadores_io_completos_2013.csv",
            "impactos_choque_unitario_demanda_final_2013.csv",
            "rankings_io_por_producto_2013.csv",
        ):
            self.assertFalse(
                any(
                    "pib" in str(column).lower()
                    for column in self.frames[name].columns
                ),
                name,
            )

    def test_identidades_analiticas_aprobadas(self) -> None:
        checks = self.frames["validacion_identidades_io_2013.csv"]
        self.assertEqual(len(checks), 11)
        self.assertTrue((checks["estado"] == "APROBADO").all())
        self.assertLessEqual(checks["valor_max_abs"].max(), 1e-9)

    def test_salidas_versionadas_coinciden_con_funciones(self) -> None:
        for name, expected in self.frames.items():
            path = ANALYTICS / name
            self.assertTrue(path.is_file(), name)
            actual = pd.read_csv(path)
            pd.testing.assert_frame_equal(
                actual,
                expected,
                check_dtype=False,
                check_exact=False,
                rtol=1e-12,
                atol=1e-12,
            )


@unittest.skipUnless(SOURCE.exists(), "La fuente primaria no se distribuye en GitHub")
class EquivalenciaElementoAElementoFuenteLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from mip_gt.config import load_config, load_layout
        from mip_gt.extract import extract_source
        from mip_gt.transform import build_system

        config = load_config(ROOT / "04_reproduccion_python" / "config_mip.yaml")
        cls.system = build_system(extract_source(SOURCE, load_layout(config)))
        cls.data = load_canonical_io_data(ROOT)

    def assert_numeric_equal(self, actual: np.ndarray, expected: np.ndarray) -> None:
        np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-10)

    def test_matrices_exportadas_elemento_a_elemento(self) -> None:
        system = self.system
        self.assert_numeric_equal(self.data.z_domestic, system.source.z_domestic)
        self.assert_numeric_equal(self.data.z_imported, system.source.z_imported)
        self.assert_numeric_equal(self.data.a_domestic, system.a_domestic)
        self.assert_numeric_equal(self.data.a_imported, system.a_imported)
        self.assert_numeric_equal(self.data.a_total_inputs, system.a_total_inputs)
        self.assert_numeric_equal(
            self.data.leontief_domestic, system.leontief_domestic
        )

    def test_vectores_exportados_elemento_a_elemento(self) -> None:
        source = self.system.source
        output = pd.read_csv(RESULTS / "vectores" / "produccion_y_utilizacion_2013.csv")
        self.assert_numeric_equal(
            output["produccion_precios_basicos"].to_numpy(), source.output
        )
        self.assert_numeric_equal(
            output["total_utilizacion_precios_basicos"].to_numpy(),
            source.total_utilization_domestic,
        )
        self.assert_numeric_equal(
            output["diferencia_produccion_utilizacion"].to_numpy(),
            self.system.supply_use_gap,
        )
        self.assert_numeric_equal(
            output["producto_interno_bruto"].to_numpy(), source.gdp
        )
        self.assert_numeric_equal(output["puestos_trabajo"].to_numpy(), source.jobs)

        primary = pd.read_csv(RESULTS / "vectores" / "cuentas_primarias_2013.csv")
        expected_primary = {
            "consumo_intermedio_domestico": source.z_domestic.sum(axis=0),
            "consumo_intermedio_importado": source.z_imported.sum(axis=0),
            "impuestos_sobre_productos": source.taxes_products,
            "subvenciones_sobre_productos": source.subsidies_products,
            "impuestos_netos_sobre_productos": source.net_taxes_products,
            "valor_agregado_bruto_oficial": source.value_added,
            "produccion_precios_basicos": source.output,
        }
        for column, expected in expected_primary.items():
            self.assert_numeric_equal(primary[column].to_numpy(), expected)

        coefficients = pd.read_csv(
            RESULTS / "vectores" / "coeficientes_primarios_2013.csv"
        )
        for column, expected in self.system.primary_coefficients.items():
            self.assert_numeric_equal(coefficients[column].to_numpy(), expected)

        vab = pd.read_csv(
            RESULTS / "vectores" / "componentes_valor_agregado_2013.csv"
        )
        expected_vab = {
            "remuneracion_asalariados": source.compensation,
            "impuestos_produccion_importaciones": source.taxes_production_imports,
            "subvenciones_produccion": source.subsidies_production,
            "excedente_explotacion_bruto": source.operating_surplus,
            "ingreso_mixto_bruto": source.mixed_income,
            "valor_agregado_bruto_oficial": source.value_added_components_source,
        }
        for column, expected in expected_vab.items():
            self.assert_numeric_equal(vab[column].to_numpy(), expected)

    def test_demanda_final_exportada_elemento_a_elemento(self) -> None:
        source = self.system.source
        domestic = pd.read_csv(
            RESULTS / "vectores" / "demanda_final_domestica_2013.csv"
        )
        imported = pd.read_csv(
            RESULTS / "vectores" / "demanda_final_importada_2013.csv"
        )
        for origin_frame, components in (
            (domestic, source.final_domestic),
            (imported, source.final_imported),
        ):
            for name, expected in components.items():
                column = "ajuste_cif_fob_publicado" if name == "ajuste_cif_fob" else name
                self.assert_numeric_equal(origin_frame[column].to_numpy(), expected)
            self.assert_numeric_equal(
                origin_frame["ajuste_cif_fob_aplicado"].to_numpy(),
                -components["ajuste_cif_fob"],
            )
        self.assert_numeric_equal(
            domestic["demanda_final_balanceada"].to_numpy(),
            self.system.final_domestic_balanced,
        )
        self.assert_numeric_equal(
            domestic["total_demanda_final_fuente"].to_numpy(),
            self.system.final_domestic_from_source_total,
        )
        self.assert_numeric_equal(
            imported["total_demanda_final_fuente"].to_numpy(),
            self.system.final_imported_from_source_total,
        )

    def test_totales_oficiales_y_semantica_fila174(self) -> None:
        from openpyxl import load_workbook

        workbook = load_workbook(SOURCE, data_only=True, read_only=True)
        try:
            sheet = workbook["MIP_152x152"]
            legacy_row_total = sum(
                float(cell.value) for cell in sheet["D174:EY174"][0]
            )
            legacy_row = np.asarray(
                [float(cell.value) for cell in sheet["D174:EY174"][0]]
            )
            intermediate_net_taxes = sum(
                float(cell.value) for cell in sheet["D170:EY170"][0]
            )
            control = legacy_row_174_semantic_control(self.data).iloc[0]
            self.assertAlmostEqual(
                legacy_row_total,
                control["suma_vector_legado_millones_quetzales"],
                places=8,
            )
            self.assertAlmostEqual(
                intermediate_net_taxes,
                control[
                    "impuestos_netos_insumos_intermedios_millones_quetzales"
                ],
                places=8,
            )
            np.testing.assert_allclose(
                legacy_row,
                self.data.output
                + self.data.net_tax_coefficients * self.data.output,
                rtol=1e-13,
                atol=1e-9,
            )
            self.assertAlmostEqual(
                float(sheet["EZ172"].value),
                control["valor_agregado_bruto_oficial_millones_quetzales"],
                places=8,
            )
            self.assertAlmostEqual(
                float(sheet["FJ170"].value),
                control[
                    "impuestos_netos_todos_los_usos_oficial_millones_quetzales"
                ],
                places=8,
            )
            for address in ("EZ174", "FJ174"):
                self.assertAlmostEqual(
                    float(sheet[address].value),
                    control["pib_oficial_ez174_fj174_millones_quetzales"],
                    places=8,
                )
        finally:
            workbook.close()


if __name__ == "__main__":
    unittest.main()
