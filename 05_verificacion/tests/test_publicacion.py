from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "02_resultados_y_diccionario"
MATRICES = RESULTS / "matrices"
VECTORS = RESULTS / "vectores"
SOURCE = (
    ROOT
    / "00_trazabilidad_fuentes"
    / "fuentes_originales_no_redistribuidas"
    / "MIP_AR2013_NPG.xlsx"
)
SRC = ROOT / "04_reproduccion_python" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def matrix(name: str) -> tuple[pd.DataFrame, np.ndarray]:
    frame = pd.read_csv(MATRICES / name)
    return frame, frame.iloc[:, 2:].to_numpy(dtype=float)


class PublicacionDerivadaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.products = pd.read_csv(RESULTS / "productos_2013.csv")
        cls.z_dom_frame, cls.z_dom = matrix("Z_domestica_2013.csv")
        cls.z_imp_frame, cls.z_imp = matrix("Z_importada_2013.csv")
        _, cls.a_dom = matrix("A_domestica_2013.csv")
        _, cls.a_imp = matrix("A_importada_2013.csv")
        _, cls.leontief = matrix("Leontief_domestica_2013.csv")
        cls.output = pd.read_csv(VECTORS / "produccion_y_utilizacion_2013.csv")
        cls.primary = pd.read_csv(VECTORS / "cuentas_primarias_2013.csv")

    def test_nomenclatura_completa(self) -> None:
        expected = [f"P{i:03d}" for i in range(1, 153)]
        self.assertEqual(self.products["codigo"].tolist(), expected)
        self.assertEqual(self.z_dom_frame["codigo"].tolist(), expected)
        self.assertEqual(self.z_dom_frame.columns[2:].tolist(), expected)

    def test_dimensiones_matrices(self) -> None:
        for array in (self.z_dom, self.z_imp, self.a_dom, self.a_imp, self.leontief):
            self.assertEqual(array.shape, (152, 152))

    def test_totales_publicados(self) -> None:
        self.assertAlmostEqual(self.z_dom.sum(), 221245.39694770114, places=8)
        self.assertAlmostEqual(self.z_imp.sum(), 76354.12092101904, places=8)
        self.assertAlmostEqual(
            self.output["produccion_precios_basicos"].sum(),
            694946.5673502104,
            places=8,
        )
        self.assertAlmostEqual(
            self.primary["valor_agregado_bruto_oficial"].sum(),
            392018.15492916724,
            places=8,
        )

    def test_identidad_costos_por_columna(self) -> None:
        gap = self.primary["residuo_identidad_columna"].to_numpy(dtype=float)
        self.assertLessEqual(np.max(np.abs(gap)), 1e-8)

    def test_inversa_leontief(self) -> None:
        residual = (np.eye(152) - self.a_dom) @ self.leontief - np.eye(152)
        self.assertLessEqual(np.max(np.abs(residual)), 1e-10)

    def test_productos_sin_produccion(self) -> None:
        zero_codes = self.products.loc[self.products["produccion_cero"], "codigo"].tolist()
        self.assertEqual(zero_codes, ["P069", "P086", "P087", "P089", "P151", "P152"])
        zero_mask = self.output["produccion_precios_basicos"].to_numpy() == 0
        self.assertEqual(float(np.max(np.abs(self.a_dom[:, zero_mask]))), 0.0)
        self.assertEqual(float(np.max(np.abs(self.a_imp[:, zero_mask]))), 0.0)

    def test_convencion_cif_fob(self) -> None:
        domestic = pd.read_csv(VECTORS / "demanda_final_domestica_2013.csv")
        row = domestic.loc[domestic["codigo"] == "P105"].iloc[0]
        self.assertAlmostEqual(
            row["ajuste_cif_fob_publicado"], -23.9879956546108, places=11
        )
        self.assertAlmostEqual(
            row["ajuste_cif_fob_aplicado"], 23.9879956546108, places=11
        )
        components = (
            row["exportaciones_fob"]
            + row["consumo_hogares"]
            + row["consumo_isflsh"]
            + row["consumo_gobierno"]
            + row["formacion_bruta_capital_fijo"]
            + row["variacion_existencias"]
            + row["ajuste_cif_fob_aplicado"]
        )
        self.assertAlmostEqual(components, row["total_demanda_final_fuente"], places=8)

    def test_controles_publicados(self) -> None:
        controls = pd.read_csv(ROOT / "05_verificacion" / "controles_reproduccion.csv")
        self.assertEqual(len(controls), 22)
        mandatory = controls[controls["mandatory"]]
        self.assertTrue((mandatory["status"] == "APROBADO").all())

    def test_metadatos(self) -> None:
        metadata = json.loads((RESULTS / "metadatos_dataset.json").read_text("utf-8"))
        self.assertEqual(metadata["products"], 152)
        self.assertTrue(metadata["mandatory_controls_passed"])
        self.assertLess(metadata["spectral_radius_a_domestic"], 1.0)


@unittest.skipUnless(SOURCE.exists(), "La fuente primaria no se distribuye en GitHub")
class FuenteLocalTests(unittest.TestCase):
    def test_huella_fuente(self) -> None:
        digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "44ad0eb8136d3d42622c6727f911eb84e9c3d64a3f502fc706446dc3523af5a2",
        )

    def test_reconstruccion_en_memoria(self) -> None:
        from mip_gt.config import load_config, load_layout
        from mip_gt.extract import extract_source
        from mip_gt.transform import build_system
        from mip_gt.validate import validate_system

        config = load_config(ROOT / "04_reproduccion_python" / "config_mip.yaml")
        system = build_system(extract_source(SOURCE, load_layout(config)))
        controls = validate_system(
            system,
            expected_sha256=config["source"]["expected_sha256"],
            source_balance_tolerance=float(
                config["validation"]["source_balance_tolerance"]
            ),
            numeric_tolerance=float(config["validation"]["numeric_tolerance"]),
        )
        failures = [c for c in controls if c.mandatory and c.status != "APROBADO"]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
