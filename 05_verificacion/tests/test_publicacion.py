from __future__ import annotations

import hashlib
import json
import re
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
        zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
        package_version = __import__("mip_gt").__version__
        self.assertEqual(metadata["version"], zenodo["version"])
        self.assertEqual(metadata["version"], package_version)
        self.assertRegex(metadata["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(metadata["products"], 152)
        self.assertTrue(metadata["mandatory_controls_passed"])
        self.assertLess(metadata["spectral_radius_a_domestic"], 1.0)

    def test_alcance_y_acceso_colab(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "El alcance es estadístico y computacional", readme
        )
        colab_url = (
            "https://colab.research.google.com/github/JA-Osorio/"
            "mip-guatemala-2013-reproducible/blob/main/"
            "04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb"
        )
        self.assertIn(colab_url, readme)

    def test_cuaderno_ejecutado_plegado_y_con_salidas(self) -> None:
        notebook_path = (
            ROOT / "04_reproduccion_python" / "cuaderno_exploracion_mip_2013.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        code_cells = [
            cell for cell in notebook["cells"] if cell["cell_type"] == "code"
        ]
        outputs = [
            output for cell in code_cells for output in cell.get("outputs", [])
        ]
        mime_types = [
            mime_type
            for output in outputs
            for mime_type in output.get("data", {})
        ]
        markdown = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
            if cell["cell_type"] == "markdown"
        )

        self.assertEqual(len(code_cells), 7)
        self.assertTrue(
            all(cell.get("execution_count") is not None for cell in code_cells)
        )
        self.assertGreaterEqual(len(outputs), 16)
        self.assertEqual(mime_types.count("image/svg+xml"), 5)
        self.assertGreaterEqual(mime_types.count("text/html"), 11)
        self.assertNotIn("image/png", mime_types)
        self.assertFalse(any(output.get("output_type") == "error" for output in outputs))
        self.assertTrue(
            all(
                {"hide-input", "remove_input"}.issubset(
                    set(cell.get("metadata", {}).get("tags", []))
                )
                for cell in code_cells
            )
        )
        self.assertTrue(
            all(
                cell.get("metadata", {})
                .get("jupyter", {})
                .get("source_hidden", False)
                for cell in code_cells
            )
        )
        self.assertIn("$$", markdown)
        self.assertNotIn(r"\[", markdown)
        self.assertNotIn(r"\]", markdown)
        for forbidden in (
            "abrir en colab",
            "github",
            "controles de calidad",
            "descargar qa",
            "<button",
        ):
            self.assertNotIn(forbidden, markdown.lower())

        table_outputs = []
        svg_outputs = []
        for output in outputs:
            data = output.get("data", {})
            html_output = data.get("text/html", "")
            if isinstance(html_output, list):
                html_output = "".join(html_output)
            if "mip-tabla" in html_output:
                table_outputs.append(html_output)
            svg_output = data.get("image/svg+xml", "")
            if isinstance(svg_output, list):
                svg_output = "".join(svg_output)
            if svg_output:
                svg_outputs.append(svg_output)
        self.assertGreaterEqual(len(table_outputs), 8)
        self.assertTrue(all("<style>" in output for output in table_outputs))
        self.assertTrue(all("Servicios de" in output or "Productos de" in output or "Carne" in output for output in svg_outputs))
        self.assertFalse(any(re.search(r">P\d{3}<", output) for output in svg_outputs))

    def test_inventario_publico_usa_solo_fuentes_canonicas(self) -> None:
        registry = pd.read_csv(
            ROOT / "00_trazabilidad_fuentes" / "registro_fuentes_mip_2013.csv"
        )
        self.assertEqual(registry["id_fuente"].tolist(), ["F01", "F02", "F03"])
        self.assertEqual(set(registry["organismo"]), {"Banco de Guatemala"})

        manifest = (ROOT / "manifiesto_archivos.txt").read_text(encoding="utf-8")
        self.assertNotIn(".venv/", manifest)

    def test_repositorio_sin_aplicacion_tematica(self) -> None:
        text_extensions = {
            ".cff",
            ".csv",
            ".ipynb",
            ".json",
            ".md",
            ".py",
            ".txt",
            ".yaml",
            ".yml",
        }
        forbidden = (
            "eta" + "nol",
            "alcohol " + "carburante",
            "mezcla " + "e10",
        )
        matches: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in text_extensions:
                continue
            if any(
                part in {".git", "__pycache__", "fuentes_originales_no_redistribuidas"}
                for part in path.relative_to(ROOT).parts
            ):
                continue
            if path.name == "manifiesto_archivos.txt":
                continue
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(term in content for term in forbidden):
                matches.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(matches, [])

    def test_indicadores_io(self) -> None:
        indicators = pd.read_csv(RESULTS / "indicadores_io_2013.csv")
        self.assertEqual(len(indicators), 152)
        self.assertEqual(indicators["codigo"].tolist(), self.products["codigo"].tolist())
        expected_output_multiplier = self.leontief.sum(axis=0)
        expected_total_import = (self.a_imp @ self.leontief).sum(axis=0)
        np.testing.assert_allclose(
            indicators["multiplicador_produccion_domestica"],
            expected_output_multiplier,
            rtol=1e-12,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            indicators["requerimiento_importacion_total"],
            expected_total_import,
            rtol=1e-12,
            atol=1e-12,
        )
        self.assertAlmostEqual(
            indicators["encadenamiento_atras_normalizado"].mean(), 1.0, places=12
        )
        self.assertAlmostEqual(
            indicators["encadenamiento_adelante_normalizado"].mean(), 1.0, places=12
        )

    def test_diccionario_documenta_salidas_y_fila_174(self) -> None:
        dictionary = pd.read_csv(RESULTS / "diccionario_variables.csv")
        legacy = dictionary[
            (dictionary["archivo_o_grupo"] == "vectores/produccion_y_utilizacion_2013.csv")
            & (dictionary["variable"] == "producto_interno_bruto")
        ]
        self.assertEqual(len(legacy), 1)
        self.assertIn("no aditivo", legacy.iloc[0]["definicion"].lower())
        self.assertIn("no apto", legacy.iloc[0]["definicion"].lower())

        documented_groups = set(dictionary["archivo_o_grupo"])
        expected_groups = {
            "indicadores/indicadores_io_completos_2013.csv",
            "indicadores/impactos_choque_unitario_demanda_final_2013.csv",
            "indicadores/rankings_io_por_producto_2013.csv",
            "indicadores/validacion_identidades_io_2013.csv",
            "indicadores/control_semantico_vector_fila174_2013.csv",
        }
        self.assertTrue(expected_groups.issubset(documented_groups))

    def test_autoria_unica(self) -> None:
        zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [creator["name"] for creator in zenodo["creators"]],
            ["Osorio, Juan Alejandro"],
        )
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertEqual(citation.count("family-names:"), 1)
        self.assertIn('family-names: "Osorio"', citation)

    def test_doi_consistente(self) -> None:
        config = (
            ROOT / "04_reproduccion_python" / "config_mip.yaml"
        ).read_text(encoding="utf-8")
        doi_match = re.search(r'^\s*doi:\s*["\']([^"\']+)["\']', config, re.MULTILINE)
        self.assertIsNotNone(doi_match)
        doi = doi_match.group(1)
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        codemeta = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
        metadata = json.loads(
            (RESULTS / "metadatos_dataset.json").read_text(encoding="utf-8")
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f'doi: "{doi}"', citation)
        self.assertEqual(codemeta["identifier"], f"https://doi.org/{doi}")
        self.assertEqual(metadata["doi"], doi)
        self.assertIn(f"https://doi.org/{doi}", readme)


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
