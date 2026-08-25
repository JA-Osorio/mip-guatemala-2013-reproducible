# Metodología cuantitativa de la MIP Guatemala 2013

## 1. Propósito y alcance

Este documento describe cómo se convierte la matriz insumo-producto (MIP)
producto por producto de Guatemala para 2013 en un sistema analítico
reproducible. Cubre la fuente, la extracción, las convenciones contables, la
construcción matricial, los indicadores publicados, las simulaciones de
demanda final, los controles de calidad y el procedimiento para incorporar una
MIP futura.

La versión 1.0.0 trabaja con 152 productos de la Nomenclatura de Productos de
Guatemala (`P001`–`P152`), a precios básicos y en millones de quetzales. El
modelo es producto por producto: no debe interpretarse automáticamente como
una matriz industria por industria.

## 2. Fuente, cobertura y trazabilidad

La entrada canónica es `MIP_AR2013_NPG.xlsx`, libro institucional del Banco de
Guatemala. La copia primaria no se redistribuye. Su ubicación esperada, huella
SHA-256 y referencias están documentadas en `00_trazabilidad_fuentes/`.

| Atributo | Especificación de esta versión |
|---|---|
| Año de referencia | 2013 |
| Unidad | Millones de quetzales |
| Valoración | Precios básicos |
| Cobertura | 152 productos, `P001`–`P152` |
| Hoja doméstica | `MIP_152x152` |
| Hoja importada | `M152x152` |
| Huella de la copia usada | `44ad0eb8136d3d42622c6727f911eb84e9c3d64a3f502fc706446dc3523af5a2` |

La huella identifica la copia exacta usada para la publicación. Una copia con
otra huella puede ser una revisión oficial legítima, pero debe tratarse como
una fuente distinta hasta comprobar estructura, valores y metadatos.

### 2.1 Rangos leídos

| Elemento | Hoja y rango | Tratamiento |
|---|---|---|
| Códigos de columnas | `MIP_152x152!D11:EY11` | Deben ser `P001`–`P152` y coincidir con las filas |
| Códigos y nombres | `MIP_152x152!B12:C163` | Se conservan orden y denominación |
| Transacciones domésticas | `MIP_152x152!D12:EY163` | Matriz `Zᵈ`, sin ajuste |
| Transacciones importadas | `M152x152!D12:EY163` | Matriz `Zᵐ`, sin ajuste |
| Subtotal intermedio | Ambas hojas, `EZ12:EZ163` | Control de sumas por fila |
| Demanda final | Ambas hojas, columnas `FA:FI` seleccionadas | Componentes no solapados |
| Utilización total | Ambas hojas, `FJ12:FJ163` | Control del total por producto |
| Insumos por origen | Hoja doméstica, filas `164` y `167` | Control de sumas por columna |
| Impuestos y subvenciones sobre productos | Hoja doméstica, filas `168:170` | Cuentas primarias |
| VAB y producción | Hoja doméstica, filas `172:173` | Vectores oficiales por producto |
| Fila legado rotulada PIB | Hoja doméstica, `D174:EY174` | Se conserva, pero no es aditiva ni apta para impactos de PIB |
| PIB oficial agregado | Hoja doméstica, `EZ174`/`FJ174` | Total institucional; no es un vector de coeficientes por producto |
| Componentes del VAB | Hoja doméstica, filas `176:181` | Desglose y control |
| Puestos de trabajo | Hoja doméstica, fila `183` | Cuenta satélite de empleo |

El detalle completo y legible por máquina está en
`00_trazabilidad_fuentes/especificacion_rangos_fuente.csv`.

### 2.2 Reglas de extracción

El libro se abre con los valores almacenados de las celdas. Las celdas vacías
se interpretan como cero; los booleanos no se aceptan como números. El proceso
exige que los códigos de filas y columnas coincidan en las dos hojas y que las
etiquetas no estén vacías. Los rangos están declarados en
`04_reproduccion_python/config_mip.yaml`; no se detectan por heurísticas.

Los subtotales de consumo final y de formación de capital se omiten porque ya
están representados por sus componentes. Esto evita doble conteo.

## 3. Notación y orientación

Se usan índices `i` para el producto que se suministra como insumo y `j` para
el producto cuya producción utiliza ese insumo.

| Símbolo | Dimensión | Definición |
|---|---:|---|
| `Zᵈ = [zᵈᵢⱼ]` | 152 × 152 | Flujo intermedio doméstico del producto `i` utilizado por el producto `j` |
| `Zᵐ = [zᵐᵢⱼ]` | 152 × 152 | Flujo intermedio importado del producto `i` utilizado por el producto `j` |
| `x` | 152 × 1 | Producción por producto a precios básicos |
| `fᵈ` | 152 × 1 | Demanda final doméstica balanceada |
| `Aᵈ` | 152 × 152 | Coeficientes técnicos domésticos |
| `Aᵐ` | 152 × 152 | Coeficientes técnicos importados |
| `Lᵈ` | 152 × 152 | Inversa de Leontief doméstica |
| `v` | 152 × 1 | VAB por producto |
| `n` | 152 × 1 | Puestos de trabajo por producto |

Por tanto, una **fila** de `Z` muestra los destinos intermedios de un producto
y una **columna** muestra la estructura de insumos del producto producido. Al
importar un CSV ancho, las dos primeras columnas (`codigo`, `producto`) son
identificadores; el bloque numérico empieza en `P001` y debe conservar el orden
`P001`–`P152` en ambos ejes.

## 4. Construcción de las cuentas básicas

### 4.1 Matrices doméstica e importada

`Zᵈ` y `Zᵐ` se extraen directamente de hojas separadas. No se estima el origen
de los insumos ni se reparte un total combinado. También se publica
`Zᵈ + Zᵐ` de forma indirecta mediante los coeficientes totales, pero se mantiene
la separación para no perder la interpretación de producción doméstica y fuga
importada.

### 4.2 Producción y utilización

`x` es el vector oficial de producción de la fila 173. Para cada producto, la
utilización doméstica publicada `uᵈ` se descompone como:

```text
uᵈ = Zᵈ 1 + fᵈ_fuente
fᵈ_fuente = uᵈ - Zᵈ 1
```

donde `1` es un vector columna de unos. La fuente presenta diferencias de
redondeo entre producción y utilización. El repositorio las conserva en:

```text
g = x - uᵈ
```

y construye una demanda final balanceada para el modelo:

```text
fᵈ_balanceada = x - Zᵈ 1 = fᵈ_fuente + g
```

No se aplica RAS ni se distribuye el residuo proporcionalmente. El ajuste queda
identificado por producto en
`demanda_final_domestica_2013.csv`. La mayor diferencia absoluta publicada es
Q0.19 millones.

### 4.3 Componentes de demanda final

Se extraen exportaciones FOB, consumo de hogares, consumo de ISFLSH, consumo
del gobierno, formación bruta de capital fijo, variación de existencias y
ajuste CIF/FOB. La fuente muestra el ajuste CIF/FOB con un signo, pero su total
de utilización lo resta. Por eso se conservan dos variables:

```text
ajuste_cif_fob_aplicado = -ajuste_cif_fob_publicado
```

El archivo distingue la suma de componentes no solapados, el total derivado de
la fuente y la demanda final balanceada. La demanda final importada se publica
por separado como cuenta de utilización; no se incorpora a `fᵈ`.

### 4.4 Identidad de costos

Para cada columna `j`, la producción se contrasta con los costos intermedios y
primarios:

```text
x = (Zᵈ)' 1 + (Zᵐ)' 1 + t + v
```

`t` son los impuestos netos sobre productos y `v` es el VAB oficial. Las
subvenciones conservan el signo de la fuente. El VAB no se calcula como
residuo: se extrae de su fila oficial y sus componentes se usan como control.

### 4.5 Advertencia sobre la fila rotulada como PIB

La columna `producto_interno_bruto` de
`produccion_y_utilizacion_2013.csv` conserva por trazabilidad los valores de
`D174:EY174`, pero **no debe sumarse ni utilizarse para impactos de PIB**. Esa
fila legado equivale, por producto, a producción a precios básicos más
impuestos netos de los usos intermedios; su suma es Q700,275.461903 millones y
no corresponde al PIB.

El PIB oficial agregado de la fuente es Q416,383.205338 millones en
`EZ174`/`FJ174`: VAB de Q392,018.154929 millones más impuestos netos sobre los
productos de todos los usos por Q24,365.050408 millones (`FJ170`). Estos
impuestos incluyen usos finales y no están disponibles como tasas por producto
de demanda final en la base publicada.

Por esa razón, el repositorio modela y publica el efecto sobre **VAB**, pero no
un multiplicador de PIB. Construirlo como `(VAB + impuestos intermedios)/x`
subestimaría o reasignaría incorrectamente los impuestos sobre los usos finales.

## 5. Coeficientes técnicos e inversa

Sea `Dₓ = diag(x)`. Los coeficientes se calculan por columna:

```text
Aᵈ = Zᵈ Dₓ⁻¹
Aᵐ = Zᵐ Dₓ⁻¹
Aᵗ = Aᵈ + Aᵐ
```

Así, `aᵈᵢⱼ` expresa los quetzales de insumo doméstico `i` requeridos
directamente por quetzal de producción `j`. `aᵐᵢⱼ` tiene la misma lectura para
el origen importado.

Seis productos tienen producción nula: `P069`, `P086`, `P087`, `P089`, `P151`
y `P152`. Como sus columnas de insumos también son nulas, sus coeficientes se
definen como cero. Esta regla evita divisiones indefinidas y no imputa
producción. Se conservan en las matrices por completitud contable y pueden
aparecer en exploración descriptiva, pero no deben seleccionarse como productos
objetivo de choques: no tienen coeficientes técnicos observados para inferir
impactos.

El sistema de cantidades domésticas es:

```text
x = Aᵈ x + fᵈ
(I - Aᵈ)x = fᵈ
x = Lᵈ fᵈ
Lᵈ = (I - Aᵈ)⁻¹
```

La inversa utiliza solo `Aᵈ`. Incluir `Aᵐ` convertiría insumos importados en
producción doméstica recirculante y cambiaría el significado del resultado.
`Aᵐ` se aplica después para medir requerimientos importados.

La existencia numérica de la inversa se comprueba con el radio espectral y el
residuo matricial. En esta versión:

| Control | Resultado |
|---|---:|
| Radio espectral de `Aᵈ` | 0.390615854513 |
| Número de condición de `I - Aᵈ` | 2.981038978787 |
| `max abs[(I - Aᵈ)Lᵈ - I]` | `1.332e-15` |

## 6. Coeficientes primarios y satélite

Para todo producto con `xⱼ > 0` se publican coeficientes directos por unidad de
producción:

```text
a_ci,dⱼ = sum_i(zᵈᵢⱼ) / xⱼ
a_ci,mⱼ = sum_i(zᵐᵢⱼ) / xⱼ
a_tⱼ    = tⱼ / xⱼ
a_vⱼ    = vⱼ / xⱼ
a_eⱼ    = nⱼ / xⱼ
```

`a_e` se expresa en puestos por millón de quetzales de producción porque `x`
está en millones. Para columnas con producción nula todos los coeficientes se
fijan en cero. La identidad normalizada de costos es:

```text
1' = 1'Aᵈ + 1'Aᵐ + a_t' + a_v'
```

dentro de la tolerancia de la fuente para columnas con producción positiva.

## 7. Multiplicadores y encadenamientos

Para un aumento unitario de demanda final del producto `j`:

| Indicador | Fórmula | Interpretación |
|---|---|---|
| Multiplicador de producción | `mˣⱼ = sum_i(Lᵈᵢⱼ)` | Producción doméstica directa e indirecta por unidad de demanda final |
| Encadenamiento hacia atrás | `BLⱼ = mˣⱼ / media(mˣ)` | Intensidad de compras domésticas respecto del promedio |
| Encadenamiento hacia adelante | `FLᵢ = sum_j(Lᵈᵢⱼ) / media_i(sum_j(Lᵈᵢⱼ))` | Índice de sensibilidad de dispersión respecto del promedio |
| Importación directa | `mᵈⱼ = sum_i(Aᵐᵢⱼ)` | Insumos importados directos por unidad de producción |
| Importación total | `mᵐ = 1'AᵐLᵈ` | Insumos importados directos e indirectos por unidad de demanda final |
| Multiplicador de VAB | `mᵛ = a_v'Lᵈ` | VAB doméstico asociado por unidad de demanda final |
| Multiplicador de empleo | `mᵉ = a_e'Lᵈ` | Puestos asociados por millón de quetzales de demanda final |

Los índices de Rasmussen-Hirschman están normalizados para que el promedio del
sistema sea uno. Un valor mayor que uno indica intensidad relativa superior al
promedio, no importancia absoluta ni causalidad. La suma normalizada de filas
de `Lᵈ` es el **índice de sensibilidad de dispersión de
Rasmussen-Hirschman**, a veces llamado encadenamiento hacia adelante. No
equivale a un multiplicador de oferta ni a un modelo de Ghosh.

El cuadro compacto `indicadores_io_2013.csv` conserva la interfaz original.
La tabla `indicadores/indicadores_io_completos_2013.csv` añade coeficientes y
multiplicadores directos, indirectos y totales, tipología de encadenamientos y
posiciones. Los seis rankings también se publican en formato largo en
`indicadores/rankings_io_por_producto_2013.csv`.

El cuadro completo también muestra impuestos netos sobre insumos intermedios
asociados, calculados con los coeficientes disponibles por columna. Esta
magnitud es diagnóstica y no debe rotularse ni interpretarse como PIB.

## 8. Simulación de un choque de demanda final

### 8.1 Preparación

El vector `Δf` debe tener 152 posiciones, seguir el orden `P001`–`P152` y usar
millones de quetzales de 2013 a precios básicos. Si una cifra viene en
quetzales, debe dividirse entre un millón antes del cálculo. Si procede de otro
año, debe explicarse la conversión de precios; el repositorio no deflacta
automáticamente.

### 8.2 Resultados

```text
Δx                = Lᵈ Δf
Δx_directa        = Δf
Δx_indirecta      = (Lᵈ - I) Δf
Δm_directa        = Aᵐ Δf
Δm_indirecta      = Aᵐ (Lᵈ - I) Δf
Δm_total          = Aᵐ Δx
Δv_directo        = diag(a_v) Δf
Δv_indirecto      = diag(a_v) (Lᵈ - I) Δf
Δv_total          = diag(a_v) Δx
Δe_directo        = diag(a_e) Δf
Δe_indirecto      = diag(a_e) (Lᵈ - I) Δf
Δe_total          = diag(a_e) Δx
```

Los totales escalares se obtienen sumando cada vector. Para un choque con
varios productos no deben sumarse multiplicadores pretabulados y luego volver
a aplicar `Lᵈ`; basta con multiplicar una sola vez el vector completo.

### 8.3 Ejemplo conceptual

Para un choque de Q100 millones en el producto `P010`:

1. Crear un vector de ceros y asignar `100` a la posición de `P010`.
2. Calcular `Δx = LᵈΔf`.
3. Calcular `AᵐΔx`, `diag(a_v)Δx` y `diag(a_e)Δx`.
4. Reportar resultados por producto y totales, siempre en las unidades
   anteriores.
5. Guardar el vector de choque, la versión del repositorio y el DOI junto con
   las salidas de la investigación.

El cuaderno de Colab implementa este flujo de forma parametrizable.
`indicadores/impactos_choque_unitario_demanda_final_2013.csv` precalcula la
misma descomposición para un choque de Q1 millón en cada producto y marca los
seis productos con producción nula.

## 9. Controles e identidades

La publicación se detiene si falla un control obligatorio. La conversión base
registra 22 controles aprobados, sin advertencias ni fallos. La capa analítica
añade 11 identidades aprobadas en
`02_resultados_y_diccionario/indicadores/validacion_identidades_io_2013.csv`.
Además, `control_semantico_vector_fila174_2013.csv` registra las identidades y
la prohibición de usar el vector legado como PIB.

| Grupo | Qué verifica |
|---|---|
| `SRC` | Huella de la copia usada; una diferencia genera revisión, no sustitución silenciosa |
| `EST` | 152 productos, secuencia de códigos, coincidencia de ejes y etiquetas |
| `MAT` | Dimensiones 152 × 152 y ausencia de negativos en los bloques intermedios |
| `BAL` | Subtotales por fila y columna, demanda final, producción-utilización, costos y VAB |
| `MOD` | Productividad, residuo de la inversa, coeficientes contables y columnas de producción nula |
| `IO` | Inversa por ambos lados, reconstrucción de `Z`, equilibrio, costos y normalización de encadenamientos |

Las identidades principales son:

```text
uᵈ = Zᵈ1 + fᵈ_fuente
x  = Zᵈ1 + fᵈ_balanceada
x  = (Zᵈ)'1 + (Zᵐ)'1 + t + v
(I - Aᵈ)Lᵈ = I
```

La tolerancia numérica general es `1e-8`; las identidades que reproducen
redondeos de fuente admiten hasta Q0.20 millones. Los valores efectivos y el
carácter obligatorio de cada prueba están en
`05_verificacion/controles_reproduccion.csv`.

## 10. Interpretación responsable

- Los resultados son comparativos estáticos: describen requerimientos bajo la
  estructura técnica de 2013, no una trayectoria temporal.
- La fila legado `producto_interno_bruto` no es agregable ni apta para estimar
  impactos. El efecto primario modelado es VAB; no se publica multiplicador de
  PIB por falta de tasas de impuestos de demanda final por producto.
- Los coeficientes son fijos; no hay sustitución entre insumos, cambios de
  tecnología, economías de escala ni restricciones de capacidad.
- El modelo no incorpora respuestas de precios, financiamiento, salarios,
  oferta laboral, recaudación inducida ni efectos de equilibrio general.
- Un multiplicador alto no implica que el producto deba priorizarse. La
  decisión requiere costos, restricciones, distribución y objetivos externos
  al modelo.
- Los puestos calculados con `a_e` son puestos **asociados** a la producción
  bajo la productividad media de 2013; no equivalen necesariamente a empleos
  nuevos, permanentes o adicionales.
- Los requisitos importados son insumos incorporados directa e indirectamente;
  no son una proyección de balanza de pagos y no incluyen por sí solos todas
  las importaciones finales.
- Los productos con producción nula se conservan para exploración descriptiva,
  pero no deben ser productos objetivo de choques ni inferencias de impacto.
  No tienen coeficientes técnicos observados; la identidad en la diagonal de
  `Lᵈ` no implica capacidad de respuesta doméstica.
- Agregar productos o comparar años exige una correspondencia explícita de
  nomenclaturas. Las diferencias pueden reflejar clasificación, valoración o
  metodología y no solo cambio económico.
- Este producto derivado no es una estadística oficial ni implica aval del
  Banco de Guatemala.

## 11. Procedimiento para incorporar una MIP futura

Una MIP nueva debe publicarse como otra versión o conjunto de datos; nunca debe
sobrescribir silenciosamente los archivos de 2013.

### Fase A — preservar y registrar

1. Guardar una copia inalterada de la fuente en un espacio con acceso
   controlado.
2. Registrar organismo, título, año de referencia, fecha de descarga, URL,
   licencia o condiciones de uso y huella SHA-256.
3. Determinar unidad, valoración, tipo de tabla (producto-producto,
   industria-industria u oferta-utilización) y tratamiento de importaciones.

### Fase B — auditar la estructura

4. Inventariar hojas, rangos, fórmulas, celdas combinadas, códigos, etiquetas,
   subtotales y ajustes especiales.
5. Crear una configuración nueva para el año; no modificar los parámetros de
   2013 para que una fuente diferente parezca compatible.
6. Si cambia la nomenclatura, construir una tabla de correspondencia con reglas
   explícitas para relaciones uno-a-uno, uno-a-muchos y muchos-a-uno. Conservar
   también los resultados en la clasificación original.

### Fase C — extraer y construir

7. Extraer primero bloques sin transformar y contrastar sus totales con la
   publicación institucional.
8. Construir `Zᵈ`, `Zᵐ`, `x`, demanda final y cuentas primarias preservando
   signos, valoración y origen.
9. Documentar cualquier balanceo. No aplicar RAS, prorrateos o imputaciones sin
   publicar el criterio, los parámetros, la matriz antes/después y los
   residuos.
10. Calcular `Aᵈ`, `Aᵐ` y `Lᵈ` solo después de aprobar las identidades
    contables y verificar producción nula y radio espectral.

### Fase D — validar y comparar

11. Adaptar las pruebas de dimensiones, códigos, subtotales, costos, VAB,
    inversión y coeficientes; las tolerancias deben responder a la precisión de
    la nueva fuente.
12. Comparar agregados y estructuras con 2013 mediante una nomenclatura
    armonizada, separando cambios reales de cambios metodológicos.
13. Revisar manualmente productos con producción nula, valores negativos,
    ajustes grandes o cambios extremos de coeficientes.

### Fase E — publicar sin romper trazabilidad

14. Usar sufijos de año y metadatos propios en todos los archivos.
15. Ejecutar script, pruebas, cuaderno y revisión del libro auditable desde una
    copia limpia del repositorio.
16. Actualizar diccionario, guía, manifiesto, citación, registro de cambios y
    DOI. Vincular la versión nueva con la de 2013 como relacionadas, no como si
    fueran el mismo conjunto de datos.

## 12. Archivos metodológicos relacionados

- `nt_00_metodologia_conversion_mip_2013.txt`: resumen de conversión y
  decisiones contables.
- `nt_01_especificacion_modelo_leontief_2013.txt`: especificación compacta del
  modelo.
- `guia_uso_analisis_io_y_actualizacion.md`: ruta operativa para reutilizar la
  base y mantener una versión futura.
- `../00_trazabilidad_fuentes/especificacion_rangos_fuente.csv`: rangos de
  extracción legibles por máquina.
- `../02_resultados_y_diccionario/diccionario_variables.csv`: definición de
  campos publicados.
- `../05_verificacion/controles_reproduccion.csv`: resultados y tolerancias de
  control.
- `../02_resultados_y_diccionario/indicadores/control_semantico_vector_fila174_2013.csv`:
  control legible por máquina del campo legado rotulado PIB.
