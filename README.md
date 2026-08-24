# MIP Guatemala 2013 reproducible

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JA-Osorio/mip-guatemala-2013-reproducible/blob/main/04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb)

Base analítica, documentada y reproducible para trabajar con la matriz insumo-producto (MIP) producto por producto de Guatemala para 2013, publicada por el Banco de Guatemala.

Este repositorio reconstruye una base analítica de 152 productos a precios básicos y en millones de quetzales. Separa explícitamente las transacciones domésticas de las importadas, conserva las cuentas primarias oficiales y produce los coeficientes técnicos y la inversa de Leontief doméstica.

El alcance es exclusivamente estadístico y computacional: conversión, documentación y validación de la MIP 2013 con la desagregación publicada por la fuente institucional.

## Resultado validado

La versión 1.0.0 produce y verifica:

- 152 productos con códigos consecutivos `P001`–`P152`;
- matriz de transacciones intermedias domésticas `Z_domestica_2013` de 152 × 152;
- matriz de utilización intermedia importada `Z_importada_2013` de 152 × 152;
- matrices de coeficientes `A_domestica_2013`, `A_importada_2013` y `A_total_insumos_2013`;
- inversa de Leontief doméstica `Leontief_domestica_2013`;
- indicadores IO listos para uso: multiplicadores, encadenamientos, intensidad importada, valor agregado y empleo;
- demanda final, producción, utilización, impuestos netos y valor agregado bruto oficial;
- 22 controles computacionales aprobados y ningún fallo obligatorio.

Totales principales de la fuente, en millones de quetzales:

| Magnitud | Total |
|---|---:|
| Producción a precios básicos | 694,946.567350 |
| Valor agregado bruto oficial | 392,018.154929 |
| Transacciones intermedias domésticas | 221,245.396948 |
| Transacciones intermedias importadas | 76,354.120921 |
| Radio espectral de `A_domestica` | 0.390615854513 |

El residuo máximo de `(I - A)L - I` es `1.332e-15`. La mayor diferencia producción–utilización publicada es Q0.19 millones y se conserva en una variable explícita; no se oculta mediante edición manual.

## Cuaderno en Google Colab

El cuaderno carga los resultados publicados, presenta los metadatos y controles y realiza una verificación matricial independiente. Puede ejecutarse sin instalar software local:

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JA-Osorio/mip-guatemala-2013-reproducible/blob/main/04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb)

## Uso para análisis insumo-producto

Los archivos publicados permiten pasar directamente de la base contable al análisis. Para un cambio de demanda final doméstica `Δf`, el cambio bruto de producción es:

```text
Δx = Lᵈ Δf
```

A partir de `Δx` pueden estimarse los requerimientos importados, el valor agregado y los puestos de trabajo asociados mediante sus coeficientes por unidad de producción. `02_resultados_y_diccionario/indicadores_io_2013.csv` entrega indicadores precalculados para los 152 productos y el cuaderno de Colab incluye un choque parametrizable.

La guía [Uso analítico y actualización](01_metodologia/guia_uso_analisis_io_y_actualizacion.md) explica las matrices disponibles, las ecuaciones, un flujo recomendado para nuevas investigaciones y el procedimiento para incorporar una nueva MIP oficial sin sobrescribir la versión 2013.

## Fuente y trazabilidad

La entrada canónica es el libro oficial producto por producto de 2013. Por prudencia jurídica, la copia primaria no forma parte de la distribución pública del repositorio. Su ruta esperada es:

```text
00_trazabilidad_fuentes/
└── fuentes_originales_no_redistribuidas/
    └── MIP_AR2013_NPG.xlsx
```

Huella SHA-256 de la copia usada para esta versión:

```text
44ad0eb8136d3d42622c6727f911eb84e9c3d64a3f502fc706446dc3523af5a2
```

El registro de fuentes, los identificadores de Drive y los rangos extraídos están en:

- `00_trazabilidad_fuentes/registro_fuentes_mip_2013.csv`;
- `00_trazabilidad_fuentes/especificacion_rangos_fuente.csv`;
- `00_trazabilidad_fuentes/instrucciones_fuente_original.txt`.

## Reproducción en Python

Se recomienda Python 3.10 o posterior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python 04_reproduccion_python/reproducir_mip_guatemala_2013.py
python -m unittest discover -s 05_verificacion/tests -v
```

La fuente también puede estar fuera del repositorio:

```bash
python 04_reproduccion_python/reproducir_mip_guatemala_2013.py \
  --fuente /ruta/segura/MIP_AR2013_NPG.xlsx
```

El script maestro ejecuta, en orden:

1. verificación de la huella y extracción de rangos;
2. separación de flujos domésticos e importados;
3. construcción de coeficientes técnicos e inversa doméstica;
4. controles de estructura, contabilidad y álgebra matricial;
5. exportación de CSV, metadatos, balances, informe y manifiesto.

Si falla un control obligatorio, la publicación de resultados se detiene.

## Convenciones contables y del modelo

Sea `Zᵈ` la matriz doméstica, `Zᵐ` la matriz importada y `x` el vector de producción:

```text
Aᵈ = Zᵈ diag(x)⁻¹
Aᵐ = Zᵐ diag(x)⁻¹
Lᵈ = (I - Aᵈ)⁻¹
```

Para los seis productos con producción nula (`P069`, `P086`, `P087`, `P089`, `P151`, `P152`), los coeficientes se fijan en cero únicamente porque sus columnas de insumos también son nulas. No se divide entre cero ni se imputa producción.

La identidad de costos por producto es:

```text
x = 1′Zᵈ + 1′Zᵐ + impuestos netos sobre productos + VAB
```

El modelo de cantidades utiliza `Aᵈ`: las importaciones se tratan como fugas y se publican por separado para análisis de dependencia importadora o de precios. Sumar `Aᵐ` dentro de la inversa doméstica cambiaría la interpretación económica.

### Ajuste CIF/FOB

La fuente muestra el ajuste CIF/FOB con un signo, pero el total de utilización lo **resta**. Por ello se publican dos variables:

- `ajuste_cif_fob_publicado`: valor tal como aparece en la celda;
- `ajuste_cif_fob_aplicado`: valor publicado multiplicado por `-1` para reproducir el total.

Esta convención evita una diferencia artificial de Q47.975991 millones al comparar componentes y total de utilización.

## Estructura

```text
00_trazabilidad_fuentes/       fuentes, huellas y rangos
01_metodologia/                notas metodológicas y ecuaciones
02_resultados_y_diccionario/   CSV derivados, indicadores IO y diccionario
03_modelo_hoja_calculo/        libro Excel auditable
04_reproduccion_python/        script maestro, paquete y cuaderno
05_verificacion/               pruebas, balances e informes
98_archivo_historico/          reservado; no alimenta la reproducción
```

Los CSV anchos preservan matrices completas. `datos_largos/` ofrece versiones normalizadas para R, Python, bases de datos o herramientas de visualización.

## Hallazgo sobre construcciones previas

Se comparó `Z_domestica_2013.csv` con dos libros históricos proporcionados por el equipo: `mtriz io.xlsx` y `MIO.xlsx`. Ambos contienen el mismo bloque doméstico, con diferencia máxima absoluta de `5.0022e-12`, atribuible a serialización numérica. Sin embargo, no son fuentes suficientes para reconstruir el sistema porque no conservan conjuntamente la matriz importada, demanda final, producción, impuestos y VAB. El detalle está en `05_verificacion/comparacion_con_construcciones_previas.csv`.

## Limitaciones

- La versión 1.0.0 representa la estructura económica de 2013. Una nueva MIP oficial debe incorporarse como otra versión documentada y validada, sin reinterpretar ni sobrescribir los resultados de 2013.
- El modelo de Leontief supone coeficientes fijos, proporcionalidad y ausencia de restricciones de capacidad.
- La matriz producto por producto depende de supuestos de tecnología y homogeneidad descritos por la metodología oficial.
- Este producto derivado no es una estadística oficial ni implica aval del Banco de Guatemala.

## Autoría y licencias

Autor: Juan Alejandro Osorio.

Los datos derivados y la documentación se distribuyen bajo CC BY 4.0; el código original y las celdas ejecutables del cuaderno, bajo MIT. Las fuentes primarias y los materiales de terceros conservan sus condiciones de origen.
