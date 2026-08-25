# MIP Guatemala 2013 reproducible

[![Validación](https://github.com/JA-Osorio/mip-guatemala-2013-reproducible/actions/workflows/validar.yml/badge.svg)](https://github.com/JA-Osorio/mip-guatemala-2013-reproducible/actions/workflows/validar.yml)
[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JA-Osorio/mip-guatemala-2013-reproducible/blob/main/04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22086008.svg)](https://doi.org/10.5281/zenodo.22086008)
[![Datos: CC BY 4.0](https://img.shields.io/badge/datos-CC%20BY%204.0-green.svg)](LICENSE)
[![Código: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-blue.svg)](LICENSE_CODE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)

Una versión abierta, auditable y lista para análisis de la matriz
insumo-producto (MIP) **producto por producto** de Guatemala para 2013,
publicada por el Banco de Guatemala.

El repositorio transforma el libro institucional en matrices y vectores
documentados para 152 productos, separa insumos domésticos e importados,
conserva la demanda final y las cuentas primarias oficiales, y publica
coeficientes técnicos, inversa de Leontief, multiplicadores y controles de
calidad. El alcance es estadístico y computacional; no contiene una aplicación
temática específica.

**Autor único:** Juan Alejandro Osorio.

## Qué puede hacer con este repositorio

| Objetivo | Archivo recomendado | Uso |
|---|---|---|
| Aprender el flujo sin instalar nada | [`cuaderno_exploracion_mip_2013.ipynb`](04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb) | Abrir en Colab, explorar productos y simular un choque |
| Consultar multiplicadores completos | [`indicadores_io_completos_2013.csv`](02_resultados_y_diccionario/indicadores/indicadores_io_completos_2013.csv) | Efectos directos, indirectos y totales, encadenamientos y rankings |
| Comparar choques unitarios | [`impactos_choque_unitario_demanda_final_2013.csv`](02_resultados_y_diccionario/indicadores/impactos_choque_unitario_demanda_final_2013.csv) | Un choque de Q1 millón en cada uno de los 152 productos |
| Simular demanda final | [`Leontief_domestica_2013.csv`](02_resultados_y_diccionario/matrices/Leontief_domestica_2013.csv) | Calcular producción doméstica directa e indirecta |
| Estimar insumos importados | [`A_importada_2013.csv`](02_resultados_y_diccionario/matrices/A_importada_2013.csv) | Aplicar coeficientes importados a la producción inducida |
| Analizar flujos intermedios | [`Z_domestica_2013.csv`](02_resultados_y_diccionario/matrices/Z_domestica_2013.csv) y [`Z_importada_2013.csv`](02_resultados_y_diccionario/matrices/Z_importada_2013.csv) | Inspeccionar origen y destino de transacciones |
| Obtener demanda final y cuentas primarias | [`vectores/`](02_resultados_y_diccionario/vectores/) | Consumo, inversión, exportaciones, producción, VAB y empleo |
| Usar una vista auditable en Excel | [`modelo_mip_guatemala_2013.xlsx`](03_modelo_hoja_calculo/modelo_mip_guatemala_2013.xlsx) | Revisar resultados y fórmulas de resumen |
| Reconstruir desde la fuente | [`reproducir_mip_guatemala_2013.py`](04_reproduccion_python/reproducir_mip_guatemala_2013.py) | Ejecutar extracción, transformación, validación y exportación |
| Auditar calidad y balances | [`controles_reproduccion.csv`](05_verificacion/controles_reproduccion.csv) y [`validacion_identidades_io_2013.csv`](02_resultados_y_diccionario/indicadores/validacion_identidades_io_2013.csv) | Revisar controles de conversión e identidades analíticas |
| Consultar variables y unidades | [`diccionario_variables.csv`](02_resultados_y_diccionario/diccionario_variables.csv) | Identificar definición, dominio y fórmula de matrices, vectores e indicadores |
| Entender el método completo | [`metodologia_cuantitativa_mip_2013.md`](01_metodologia/metodologia_cuantitativa_mip_2013.md) | Fuente, rangos, identidades, modelo, indicadores y límites |
| Adaptar una MIP futura | [`guia_uso_analisis_io_y_actualizacion.md`](01_metodologia/guia_uso_analisis_io_y_actualizacion.md) | Ruta operativa y lista de verificación |

## Resultados publicados

La versión 1.0.0 conserva la estructura oficial de 2013, a precios básicos y
en millones de quetzales.

| Resultado | Valor |
|---|---:|
| Productos | 152 (`P001`–`P152`) |
| Producción a precios básicos | 694,946.567350 |
| Valor agregado bruto oficial | 392,018.154929 |
| PIB oficial agregado, solo como referencia | 416,383.205338 |
| Transacciones intermedias domésticas | 221,245.396948 |
| Transacciones intermedias importadas | 76,354.120921 |
| Dimensión de `Zᵈ`, `Zᵐ`, `Aᵈ`, `Aᵐ` y `Lᵈ` | 152 × 152 |
| Productos con producción nula | 6 |
| Productos aptos como objetivo de simulación | 146 |
| Radio espectral de `Aᵈ` | 0.390615854513 |
| Número de condición de `I - Aᵈ` | 2.981038978787 |
| Residuo máximo de `(I - Aᵈ)Lᵈ - I` | `1.332e-15` |
| Mayor diferencia producción–utilización publicada | Q0.19 millones |
| Choques unitarios precalculados | 152 |
| Rankings largos | 6 indicadores × 152 productos |

La diferencia producción–utilización no se oculta con una edición manual: se
publica por producto y se incorpora explícitamente al vector de demanda final
balanceada utilizado por el sistema de Leontief.

### Estado de calidad

| Conjunto | Controles | Estado |
|---|---:|---|
| Fuente, estructura, matrices, balances y modelo base | 22 | 22 aprobados; 0 advertencias; 0 fallos |
| Identidades analíticas adicionales | 11 | 11 aprobadas |
| Salvaguarda semántica de la fila 174 | 1 | `NO_USAR_COMO_PIB`, estado esperado |

Los controles verifican códigos y dimensiones, sumas por fila y columna,
componentes no solapados de demanda final, identidad de costos, VAB,
productividad de la matriz, residuo de la inversa y tratamiento de productos
con producción nula. La validación analítica añade reconstrucción de `Z`,
equilibrio `x = Aᵈx + fᵈ`, medias normalizadas de los encadenamientos y
consistencia de la inversa por ambos lados.

### Salidas analíticas listas para reutilizar

| Archivo | Contenido |
|---|---|
| `indicadores/indicadores_io_completos_2013.csv` | Coeficientes directos, multiplicadores directos/indirectos/totales, encadenamientos, tipología y posiciones |
| `indicadores/impactos_choque_unitario_demanda_final_2013.csv` | Descomposición de producción, importaciones, VAB y empleo para un choque unitario por producto |
| `indicadores/rankings_io_por_producto_2013.csv` | Seis rankings en formato largo, con los 152 productos en cada bloque |
| `indicadores/validacion_identidades_io_2013.csv` | Once identidades analíticas, valor del residuo, tolerancia y estado |
| `indicadores/control_semantico_vector_fila174_2013.csv` | Evidencia reproducible de que la fila legado 174 no es aditiva ni se usa como PIB |

`indicadores_io_2013.csv` se conserva como cuadro compacto compatible con la
versión inicial.

## Ruta didáctica en cinco pasos

1. Abra el [cuaderno en Google
   Colab](https://colab.research.google.com/github/JA-Osorio/mip-guatemala-2013-reproducible/blob/main/04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb).
2. Busque el código del producto en
   `02_resultados_y_diccionario/productos_2013.csv`.
3. Defina un cambio de demanda final en millones de quetzales de 2013 a
   precios básicos.
4. Ejecute la simulación y examine producción directa, indirecta,
   importaciones, VAB y empleo asociado.
5. Guarde el vector de choque y cite la versión y el DOI junto con sus
   resultados.

El cuaderno es la entrada didáctica. El script maestro sigue siendo la entrada
canónica para reconstruir el conjunto de datos cuando se dispone del libro
fuente.

## Modelo cuantitativo

La celda `zᵈᵢⱼ` es el insumo doméstico `i` utilizado en la producción del
producto `j`; `zᵐᵢⱼ` tiene la misma orientación para insumos importados. Si `x`
es la producción por producto:

```text
Aᵈ = Zᵈ diag(x)⁻¹
Aᵐ = Zᵐ diag(x)⁻¹
Lᵈ = (I - Aᵈ)⁻¹
```

Para un choque `Δf` de demanda final doméstica:

```text
Δx              = Lᵈ Δf
Δx_indirecta    = (Lᵈ - I) Δf
Δm              = Aᵐ Δx
Δv              = diag(a_v) Δx
Δe              = diag(a_e) Δx
```

`Aᵐ` no se incluye en la inversa doméstica: las importaciones son fugas del
circuito productivo nacional y se calculan por separado. `a_v` es el
coeficiente de VAB y `a_e` el coeficiente de puestos por millón de quetzales de
producción.

La [metodología cuantitativa](01_metodologia/metodologia_cuantitativa_mip_2013.md)
detalla orientación, identidades, coeficientes, multiplicadores,
encadenamientos, simulaciones e interpretación.

## Convenciones contables que debe conocer

### Demanda final y balance

La utilización publicada cumple, dentro del redondeo de fuente:

```text
uᵈ = Zᵈ1 + fᵈ_fuente
```

Para que el sistema reproduzca exactamente la producción se publica además:

```text
fᵈ_balanceada = x - Zᵈ1
```

Ambos vectores y su diferencia permanecen visibles. No se aplica RAS ni un
prorrateo oculto.

### Ajuste CIF/FOB

La fuente muestra el ajuste CIF/FOB con un signo, pero el total de utilización
lo resta. Por ello el repositorio conserva el valor publicado y también el
valor aplicado, igual al primero multiplicado por `-1`. Esta convención evita
una diferencia artificial de Q47.975991 millones.

### Producción nula

`P069`, `P086`, `P087`, `P089`, `P151` y `P152` tienen producción nula y
columnas de insumos nulas. Sus coeficientes se fijan en cero; no se divide entre
cero ni se imputa producción. Permanecen en las matrices por completitud y
pueden usarse en exploración descriptiva, pero no deben ser productos objetivo
de choques o inferencias de impacto porque no tienen coeficientes técnicos
observados.

### Identidad de costos

```text
x = (Zᵈ)'1 + (Zᵐ)'1 + impuestos netos sobre productos + VAB
```

El VAB se toma de la fila oficial y no se obtiene como residuo.

### PIB: campo legado y alcance del modelo

El campo `producto_interno_bruto` de
`produccion_y_utilizacion_2013.csv` conserva por trazabilidad la fila
`D174:EY174`, pero no es aditivo ni apto para inferir impactos de PIB. Su suma,
Q700,275.461903 millones, representa producción básica más impuestos netos de
usos intermedios y no el PIB.

El PIB oficial agregado de la fuente es Q416,383.205338 millones
(`EZ174`/`FJ174`): VAB de Q392,018.154929 millones más Q24,365.050408 millones
de impuestos netos sobre productos de todos los usos (`FJ170`). Como la fuente
no distribuye los impuestos de demanda final en tasas por producto compatibles
con el choque, este repositorio modela **VAB** y no publica un multiplicador de
PIB.

La salvaguarda se publica de forma legible por máquina en
`indicadores/control_semantico_vector_fila174_2013.csv`. Los impuestos netos
sobre insumos intermedios asociados que aparecen en el cuadro analítico son un
diagnóstico separado y **no** un multiplicador de PIB.

## Fuente y trazabilidad

La entrada canónica es el libro `MIP_AR2013_NPG.xlsx`. Por prudencia jurídica,
la copia primaria no forma parte de la distribución pública. Puede mantenerse
en la ruta esperada o pasarse al script mediante `--fuente`:

```text
00_trazabilidad_fuentes/
└── fuentes_originales_no_redistribuidas/
    └── MIP_AR2013_NPG.xlsx
```

Huella SHA-256 de la copia usada:

```text
44ad0eb8136d3d42622c6727f911eb84e9c3d64a3f502fc706446dc3523af5a2
```

La trazabilidad se distribuye en tres capas:

- `registro_fuentes_mip_2013.csv`: procedencia, uso y redistribución;
- `especificacion_rangos_fuente.csv`: hojas, rangos y tratamiento;
- `instrucciones_fuente_original.txt`: instalación y verificación de huella.

## Reproducción en Python

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python 04_reproduccion_python/reproducir_mip_guatemala_2013.py
python -m unittest discover -s 05_verificacion/tests -v
```

Si la fuente está fuera del repositorio:

```bash
python 04_reproduccion_python/reproducir_mip_guatemala_2013.py \
  --fuente /ruta/segura/MIP_AR2013_NPG.xlsx
```

El script ejecuta, en orden:

1. carga de configuración y verificación de la fuente;
2. extracción de rangos declarados;
3. construcción de matrices, demanda final y cuentas primarias;
4. cálculo de coeficientes, inversa e indicadores;
5. controles contables y matriciales;
6. exportación de CSV, metadatos, informe y manifiesto.

Si falla un control obligatorio, la exportación se detiene.

## Estructura del repositorio

```text
00_trazabilidad_fuentes/       procedencia, huellas y rangos de extracción
01_metodologia/                método cuantitativo, uso y actualización
02_resultados_y_diccionario/   matrices, vectores, indicadores y diccionario
03_modelo_hoja_calculo/        vista Excel auditable de los derivados
04_reproduccion_python/        script, paquete, configuración y cuaderno
05_verificacion/               controles, balances, pruebas e informe
98_archivo_historico/          materiales aislados; no alimentan la reproducción
```

Los CSV anchos preservan las matrices completas. `datos_largos/` entrega
transacciones intermedias y demanda final en formato normalizado para R,
Python, bases de datos y visualización.

## Comparación con construcciones previas

`Z_domestica_2013.csv` se contrastó con dos libros históricos proporcionados
por el equipo. Ambos conservan el mismo bloque doméstico, con diferencia máxima
absoluta de `5.0022e-12`, atribuible a serialización numérica. No bastan para
reconstruir el sistema completo porque no preservan conjuntamente la matriz
importada, demanda final, producción, impuestos y VAB. El contraste está en
`05_verificacion/comparacion_con_construcciones_previas.csv`.

## Cómo actualizar cuando se publique otra MIP

Una nueva MIP debe tratarse como otro conjunto versionado, no como reemplazo de
2013. En síntesis:

1. preserve la fuente y registre su huella, licencia, unidad y valoración;
2. audite hojas, rangos, nomenclatura y tratamiento de importaciones;
3. cree una configuración y sufijos de año nuevos;
4. publique una correspondencia si cambia la clasificación;
5. valide bloques sin transformar antes de construir coeficientes;
6. documente cualquier balanceo sin ocultarlo en tolerancias;
7. ejecute pruebas contables y matriciales en un entorno limpio;
8. actualice diccionario, metodología, metadatos y DOI.

La lista completa está en la [guía de uso y
actualización](01_metodologia/guia_uso_analisis_io_y_actualizacion.md).

## Limitaciones

- La estructura técnica y laboral corresponde a 2013.
- El modelo supone coeficientes fijos, proporcionalidad, precios relativos
  constantes, capacidad suficiente y ausencia de sustitución endógena.
- Los resultados de empleo son puestos asociados a la producción media de
  2013, no creación neta ni permanencia laboral.
- El vector legado rotulado `producto_interno_bruto` no debe agregarse ni
  utilizarse en simulaciones; el resultado primario publicado es VAB.
- Los encadenamientos son índices relativos, no efectos causales ni criterios
  suficientes de priorización. La suma normalizada de filas de `Lᵈ` es el
  índice de sensibilidad de dispersión de Rasmussen-Hirschman, no un
  multiplicador de oferta ni un modelo de Ghosh.
- Las comparaciones temporales requieren armonizar clasificación, valoración y
  metodología.
- Este producto derivado no es una estadística oficial ni implica aval del
  Banco de Guatemala.

## Autoría, licencias y citación

Autor: **Juan Alejandro Osorio**.

Los datos derivados, la documentación y el libro auditable se distribuyen bajo
[CC BY 4.0](LICENSE). El código original y las celdas ejecutables del cuaderno,
bajo [MIT](LICENSE_CODE). Las fuentes primarias y los materiales de terceros
conservan sus condiciones de origen.

Citación sugerida:

> Osorio, Juan Alejandro (2026). *MIP Guatemala 2013 reproducible* (versión
> 1.0.0) [Conjunto de datos y código]. Zenodo.
> https://doi.org/10.5281/zenodo.22086008

Metadatos para gestores y repositorios: [`CITATION.cff`](CITATION.cff),
[`codemeta.json`](codemeta.json) y [`.zenodo.json`](.zenodo.json).
