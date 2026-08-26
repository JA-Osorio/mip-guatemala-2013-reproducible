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
        self.assertEqual(metadata["doi"], "10.5281/zenodo.22089741")
        self.assertEqual(metadata["concept_doi"], "10.5281/zenodo.22086007")
        self.assertRegex(metadata["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(metadata["products"], 152)
        self.assertTrue(metadata["mandatory_controls_passed"])
        self.assertLess(metadata["spectral_radius_a_domestic"], 1.0)
        self.assertTrue(metadata["official_source"])
        self.assertFalse(metadata["official_statistics"])
        self.assertEqual(metadata["analytical_status"], "experimental_derived_results")
        self.assertEqual(metadata["randomness"], "none")

    def test_alcance_y_acceso_colab(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "El alcance es estadístico y computacional", readme
        )
        colab_url = (
            "https://colab.research.google.com/github/JA-Osorio/"
            "mip-guatemala-2013-reproducible/blob/v1.1.0/"
            "04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb"
        )
        self.assertIn(colab_url, readme)
        self.assertIn("resultados analíticos experimentales", readme)
        self.assertRegex(readme, r"no constituyen\s+estadística oficial")

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

        self.assertEqual(len(code_cells), 16)
        self.assertTrue(
            all(cell.get("execution_count") is not None for cell in code_cells)
        )
        self.assertGreaterEqual(len(outputs), 15)
        self.assertEqual(mime_types.count("application/vnd.plotly.v1+json"), 6)
        self.assertEqual(mime_types.count("image/svg+xml"), 6)
        self.assertGreaterEqual(mime_types.count("text/html"), 9)
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
            all(cell.get("metadata", {}).get("scrolled") is False for cell in code_cells)
        )
        self.assertTrue(all(len(cell.get("outputs", [])) <= 1 for cell in code_cells))
        self.assertTrue(
            all(
                cell.get("metadata", {})
                .get("jupyter", {})
                .get("source_hidden", False)
                for cell in code_cells
            )
        )
        self.assertIn("$$", markdown)
        self.assertIn("Matriz Insumo-Producto (MIP) de Guatemala", markdown)
        self.assertIn("Nomenclatura de Productos de Guatemala (NPG)", markdown)
        self.assertIn("## Cómo citar este conjunto de datos y cuaderno", markdown)
        self.assertIn("## Referencias", markdown)
        self.assertNotIn("## Claves de interpretación", markdown)
        self.assertIn("(Banco de Guatemala, 2019b, 2019c)", markdown)
        self.assertIn(
            "(Hirschman, 1958; Miller & Blair, 2022; Rasmussen, 1956)",
            markdown,
        )
        self.assertIn("(Osorio, 2026)", markdown)
        self.assertIn("[Conjunto de datos]", markdown)
        self.assertIn(
            "[Conjunto de datos, código y cuaderno computacional]. Zenodo.",
            markdown,
        )
        self.assertIn("https://doi.org/10.5281/zenodo.22089741", markdown)
        self.assertIn("10.5281/zenodo.22086007", markdown)
        self.assertIn("resultados analíticos experimentales", markdown)
        self.assertIn("no constituyen estadística oficial", markdown)
        self.assertEqual(markdown.count('class="referencia-apa"'), 10)
        self.assertIn("text-indent: -2rem", markdown)
        self.assertIn("<em>Cuentas Nacionales de Guatemala", markdown)
        self.assertIn("<em>Matriz Insumo-Producto (MIP)", markdown)
        self.assertIn('<a href="https://banguat.gob.gt/', markdown)
        self.assertNotIn("display:flex;flex-wrap:wrap", markdown)
        self.assertNotIn("152 productos</span>", markdown)
        self.assertNotIn("- Banco de Guatemala. (2019a).", markdown)
        self.assertNotIn("**", markdown)
        self.assertNotIn("—", markdown)
        self.assertNotIn(r"\[", markdown)
        self.assertNotIn(r"\]", markdown)
        for forbidden in (
            "abrir en colab",
            "controles de calidad",
            "descargar qa",
            "<button",
        ):
            self.assertNotIn(forbidden, markdown.lower())

        table_outputs = []
        svg_outputs = []
        plotly_outputs = []
        for output in outputs:
            data = output.get("data", {})
            html_output = data.get("text/html", "")
            if isinstance(html_output, list):
                html_output = "".join(html_output)
            if '<table class="mip-tabla' in html_output:
                table_outputs.append(html_output)
            svg_output = data.get("image/svg+xml", "")
            if isinstance(svg_output, list):
                svg_output = "".join(svg_output)
            if svg_output:
                svg_outputs.append(svg_output)
            plotly_output = data.get("application/vnd.plotly.v1+json")
            if plotly_output:
                plotly_outputs.append(plotly_output)
        self.assertEqual(len(table_outputs), 8)
        self.assertTrue(all(output.count("<style>") == 1 for output in table_outputs))
        self.assertEqual(len(plotly_outputs), 6)
        trace_types = [
            trace["type"]
            for output in plotly_outputs
            for trace in output.get("data", [])
        ]
        self.assertEqual(trace_types.count("table"), 0)
        self.assertGreaterEqual(trace_types.count("bar"), 9)
        self.assertEqual(trace_types.count("scatter"), 4)
        self.assertEqual(trace_types.count("heatmap"), 3)
        self.assertTrue(all("Figura" in output or "Tabla" in output for output in svg_outputs))
        for collection in (svg_outputs, table_outputs):
            self.assertTrue(all("Nota." in output for output in collection))
            self.assertTrue(
                all("análisis reproducible de Osorio (2026)" in output for output in collection)
            )
            self.assertTrue(
                all("Banco de Guatemala (2019b)" in output for output in collection)
            )
            self.assertFalse(any("Juan Alejandro Osorio" in output for output in collection))
            self.assertFalse(any("Fuente de datos:" in output for output in collection))
            self.assertFalse(any("borrador en revisión" in output for output in collection))
            self.assertFalse(any("CC BY 4.0" in output for output in collection))
        self.assertFalse(
            any(re.search(r">P\d{3}<", output) for output in svg_outputs + table_outputs)
        )

        tablas_por_numero = {}
        for output in table_outputs:
            coincidencia = re.search(
                r"<span class='mip-rotulo'>Tabla (\d+)</span>",
                output,
            )
            self.assertIsNotNone(coincidencia)
            tablas_por_numero[int(coincidencia.group(1))] = output
            self.assertIn("table-layout:fixed;width:100%", output)
            self.assertIn("vertical-align:middle", output)
            self.assertNotIn("font-size:0px", output)
        self.assertEqual(set(tablas_por_numero), set(range(1, 9)))
        self.assertIn("Producción bruta", tablas_por_numero[1])
        self.assertEqual(tablas_por_numero[4].count('<table class="mip-tabla'), 2)
        self.assertIn(
            "Índices según Rasmussen (1956) y Hirschman (1958)",
            tablas_por_numero[4],
        )
        for unidad in (
            "Millones de quetzales de 2013",
            "Quetzales de producción doméstica por quetzal de demanda final",
            "Quetzales de insumos importados por quetzal de demanda final",
            "Quetzales de VAB por quetzal de demanda final",
            "Puestos por millón de quetzales de demanda final",
        ):
            self.assertIn(unidad, tablas_por_numero[5])
        tabla_6 = tablas_por_numero[6]
        self.assertIn("<th>Coeficiente total</th>", tabla_6)
        filas_tabla_6 = re.findall(
            r'<tr><td class="puesto">\d+</td><th>.*?</th>'
            r"<td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td></tr>",
            tabla_6,
        )
        self.assertEqual(len(filas_tabla_6), 8)
        for domestico, importado, total in filas_tabla_6:
            self.assertAlmostEqual(
                float(domestico.replace(",", ""))
                + float(importado.replace(",", "")),
                float(total.replace(",", "")),
                places=4,
            )

        for output in plotly_outputs:
            layout = output.get("layout", {})
            title = layout.get("title", {}).get("text", "")
            annotations = " ".join(
                annotation.get("text", "")
                for annotation in layout.get("annotations", [])
            )
            config = output.get("config", {})
            image_config = config.get("toImageButtonOptions", {})
            self.assertRegex(
                title,
                r"^<b>Figura \d+</b><br><i>.+</i>$",
            )
            self.assertTrue(annotations.strip().startswith("<i>Nota.</i>"))
            self.assertIn("análisis reproducible de Osorio (2026)", annotations)
            self.assertIn("Banco de Guatemala (2019b)", annotations)
            self.assertNotIn("Juan Alejandro Osorio", annotations)
            self.assertNotIn("Fuente de datos:", annotations)
            self.assertNotIn("borrador en revisión", annotations)
            self.assertNotIn("CC BY 4.0", annotations)
            self.assertEqual(layout.get("title", {}).get("xref"), "container")
            self.assertGreaterEqual(layout.get("title", {}).get("x", 0), 0.03)
            self.assertEqual(layout.get("title", {}).get("yref"), "container")
            self.assertEqual(layout.get("title", {}).get("yanchor"), "top")
            nota_visual = layout.get("annotations", [])[-1]
            self.assertAlmostEqual(
                layout.get("margin", {}).get("l", 0) + nota_visual.get("xshift", 0),
                36,
            )
            self.assertFalse(config.get("displaylogo", True))
            self.assertTrue(config.get("responsive"))
            self.assertFalse(config.get("scrollZoom", True))
            self.assertEqual(image_config.get("format"), "png")
            self.assertEqual(image_config.get("width"), 1400)
            self.assertGreaterEqual(image_config.get("height", 0), 700)
            self.assertEqual(image_config.get("scale"), 2)
            self.assertTrue(image_config.get("filename"))

        mapas = [
            output
            for output in plotly_outputs
            if [trace.get("type") for trace in output.get("data", [])]
            == ["heatmap", "heatmap", "heatmap"]
        ]
        self.assertEqual(len(mapas), 1)
        etiquetas_botones = [
            button["label"]
            for menu in mapas[0]["layout"].get("updatemenus", [])
            for button in menu.get("buttons", [])
        ]
        self.assertEqual(etiquetas_botones, ["Total", "Doméstica", "Importada"])
        menus = [
            menu
            for output in plotly_outputs
            for menu in output.get("layout", {}).get("updatemenus", [])
        ]
        self.assertEqual(len(menus), 2)
        self.assertTrue(all(menu.get("yanchor") == "bottom" for menu in menus))
        self.assertTrue(all(menu.get("y") <= 1.02 for menu in menus))

        source = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )
        self.assertIn("import plotly.graph_objects as go", source)
        self.assertIn("go.Heatmap", source)
        self.assertNotIn("go.Table", source)
        self.assertIn('PLOTLY_VERSION = "6.9.0"', source)
        self.assertIn('REPO_REF = "v1.1.0"', source)
        self.assertIn('"--branch", REPO_REF', source)
        self.assertIn("mip-guatemala-2013-reproducible-{REPO_REF}", source)
        self.assertIn('"describe", "--tags", "--exact-match"', source)
        self.assertIn("def tabla_indicadores_html", source)
        self.assertIn("def tabla_productos_html", source)
        self.assertIn("def tabla_rankings_html", source)
        self.assertIn("table-layout:fixed;width:100%", source)
        self.assertIn("vertical-align:middle", source)
        self.assertNotIn("def centrar_celda_plotly", source)
        self.assertNotIn("font-size:0px", source)
        self.assertIn("total_mostrado", source)
        self.assertNotIn("Q por Q de demanda final", source)
        self.assertNotIn("Q1 millón", source)
        self.assertIn("análisis reproducible de Osorio (2026)", source)
        self.assertIn("Banco de Guatemala (2019b)", source)
        self.assertNotIn("Autor de los cálculos, el diseño y la visualización", source)
        self.assertNotIn("Fuente de datos:", source)
        self.assertNotIn("borrador en revisión", source)
        self.assertNotIn("CC BY 4.0", source)
        self.assertIn(".mip-scroll{overflow:visible}", source)
        self.assertNotIn("overflow-x:auto", source)
        self.assertNotIn("elaboración propia", (source + "\n" + "\n".join(table_outputs + svg_outputs)).lower())

    def test_inventario_publico_usa_solo_fuentes_canonicas(self) -> None:
        registry = pd.read_csv(
            ROOT / "00_trazabilidad_fuentes" / "registro_fuentes_mip_2013.csv"
        )
        self.assertEqual(registry["id_fuente"].tolist(), ["F01", "F02", "F03"])
        self.assertEqual(set(registry["organismo"]), {"Banco de Guatemala"})
        for column in (
            "url_institucional_o_referencia",
            "fecha_publicacion",
            "fecha_consulta",
            "cita_sugerida",
            "condiciones_uso",
        ):
            self.assertIn(column, registry.columns)
            self.assertTrue(registry[column].notna().all())
        self.assertTrue(
            registry["url_institucional_o_referencia"]
            .str.startswith("https://banguat.gob.gt/")
            .all()
        )

        manifest = (ROOT / "manifiesto_archivos.txt").read_text(encoding="utf-8")
        self.assertNotIn(".venv/", manifest)
        self.assertNotIn(".egg-info/", manifest)
        self.assertNotIn("\n.git\t", "\n" + manifest)
        self.assertNotIn("cuaderno_tablas_numeradas_mip_2013.ipynb", manifest)
        records = [line.split("\t") for line in manifest.splitlines()[1:] if line]
        self.assertGreater(len(records), 60)
        for relative, size, digest in records:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(path.stat().st_size, int(size), relative)
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                digest,
                relative,
            )

    def test_dependencia_interactiva_declarada(self) -> None:
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        requirements = (
            ROOT / "04_reproduccion_python" / "requirements.txt"
        ).read_text(encoding="utf-8")
        self.assertIn('"plotly==6.9.0"', project)
        self.assertIn("plotly==6.9.0", requirements)
        self.assertIn('requires-python = ">=3.11"', project)
        for relative in (
            "README.md",
            "codemeta.json",
            "01_metodologia/guia_uso_analisis_io_y_actualizacion.md",
            "04_reproduccion_python/instrucciones_reproduccion_python.txt",
        ):
            self.assertIn("3.11", (ROOT / relative).read_text(encoding="utf-8"))

    def test_metadatos_de_publicacion_final(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
        self.assertIn("10.5281/zenodo.22089741", readme)
        self.assertIn("10.5281/zenodo.22086007", readme)
        self.assertNotIn("DOI reservado", readme)
        self.assertIn("date-released: 2026-08-25", citation)
        self.assertEqual(zenodo["version"], "1.1.0")
        self.assertIn("resultados analíticos experimentales", zenodo["notes"])

    def test_diccionario_usa_nombres_publicados(self) -> None:
        dictionary = pd.read_csv(RESULTS / "diccionario_variables.csv")
        ranking_fields = set(
            dictionary.loc[
                dictionary["archivo_o_grupo"]
                == "indicadores/rankings_io_por_producto_2013.csv",
                "variable",
            ]
        )
        actual_fields = set(
            pd.read_csv(
                RESULTS / "indicadores" / "rankings_io_por_producto_2013.csv",
                nrows=0,
            ).columns
        )
        self.assertIn("posicion_ordenada", ranking_fields)
        self.assertIn("posicion_ordenada", actual_fields)
        self.assertNotIn("posicion", ranking_fields)

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
