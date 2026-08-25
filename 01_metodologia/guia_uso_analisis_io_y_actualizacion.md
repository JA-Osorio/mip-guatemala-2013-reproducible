# Guía de uso para análisis IO y actualización

## 1. Elija la entrada adecuada

| Si necesita… | Empiece por… | Observación |
|---|---|---|
| Aprender el flujo con un ejemplo | `04_reproduccion_python/cuaderno_exploracion_mip_2013.ipynb` | Se abre en Colab y usa los resultados ya publicados |
| Consultar indicadores por producto | `02_resultados_y_diccionario/indicadores/indicadores_io_completos_2013.csv` | Incluye componentes directos, indirectos y totales |
| Comparar productos | `02_resultados_y_diccionario/indicadores/rankings_io_por_producto_2013.csv` | Seis rankings completos en formato largo |
| Simular un choque de demanda final | `Leontief_domestica_2013.csv`, `A_importada_2013.csv` y los coeficientes primarios | Conserve el orden `P001`–`P152` |
| Examinar transacciones | `Z_domestica_2013.csv` y `Z_importada_2013.csv` | Filas = insumos; columnas = productos que los usan |
| Trabajar en una hoja de cálculo | `03_modelo_hoja_calculo/modelo_mip_guatemala_2013.xlsx` | Vista auditable; no es la fuente canónica |
| Reconstruir todos los derivados | `04_reproduccion_python/reproducir_mip_guatemala_2013.py` | Requiere la fuente primaria por una ruta segura |
| Auditar la publicación | `05_verificacion/controles_reproduccion.csv` y `02_resultados_y_diccionario/indicadores/validacion_identidades_io_2013.csv` | Incluyen 22 controles base y 11 identidades analíticas |
| Auditar el campo legado PIB | `02_resultados_y_diccionario/indicadores/control_semantico_vector_fila174_2013.csv` | Documenta por qué no debe agregarse ni usarse en impactos |
| Entender cada decisión cuantitativa | `01_metodologia/metodologia_cuantitativa_mip_2013.md` | Es la referencia metodológica principal |

## 2. Ruta didáctica mínima

1. Abra el cuaderno de Colab desde el distintivo del `README.md`.
2. Revise `productos_2013.csv` y localice el código del producto de interés.
3. Defina un choque de demanda final en **millones de quetzales de 2013 a
   precios básicos**.
4. Ejecute la celda de simulación y separe producción directa, producción
   indirecta, importaciones, VAB y empleo asociado.
5. Verifique unidades, signos y productos con producción nula.
6. Guarde el vector de choque y los parámetros fuera de la base canónica.
7. Cite la versión 1.1.0 y el DOI `10.5281/zenodo.22089741`.

## 3. Archivos para un choque reproducible

| Componente | Archivo | Unidad |
|---|---|---|
| Códigos y orden | `02_resultados_y_diccionario/productos_2013.csv` | `P001`–`P152` |
| Inversa doméstica | `02_resultados_y_diccionario/matrices/Leontief_domestica_2013.csv` | Quetzales por quetzal |
| Coeficientes importados | `02_resultados_y_diccionario/matrices/A_importada_2013.csv` | Quetzales por quetzal |
| Coeficientes de VAB y costos | `02_resultados_y_diccionario/vectores/coeficientes_primarios_2013.csv` | Quetzales por quetzal |
| Producción y empleo | `02_resultados_y_diccionario/vectores/produccion_y_utilizacion_2013.csv` | Millones de quetzales y puestos |
| Indicadores precalculados | `02_resultados_y_diccionario/indicadores/indicadores_io_completos_2013.csv` | Según columna |
| Choques unitarios | `02_resultados_y_diccionario/indicadores/impactos_choque_unitario_demanda_final_2013.csv` | Q1 millón de demanda final por producto |

Los CSV de matrices contienen `codigo` y `producto` en las dos primeras
columnas. El bloque numérico restante debe ordenarse igual en filas, columnas y
vectores. Es más seguro unir tablas por `codigo` y después reordenar que confiar
en la posición original de una tabla modificada.

## 4. Cálculo básico

Sea `Δf` un vector de 152 posiciones:

```text
Δx              = Lᵈ Δf
Δx_indirecta    = (Lᵈ - I) Δf
Δm              = Aᵐ Δx
Δv              = diag(a_v) Δx
Δe              = diag(a_e) Δx
```

`Δf`, `Δx`, `Δm` y `Δv` se expresan en millones de quetzales. `Δe` se expresa
en puestos asociados. Las importaciones son fugas: no se suman a `Aᵈ` antes de
invertir.

Después de instalar el paquete, la función reutilizable evita ensamblar las
matrices manualmente:

```python
from mip_gt.analysis import demand_shock_impact, load_canonical_io_data

datos = load_canonical_io_data(".")
impacto = demand_shock_impact(
    codes=datos.codes,
    labels=datos.labels,
    shock={"P010": 100.0},
    a_domestic=datos.a_domestic,
    a_imported=datos.a_imported,
    leontief_domestic=datos.leontief_domestic,
    value_added_coefficients=datos.value_added_coefficients,
    employment_coefficients=datos.employment_coefficients,
)

impacto.totals
impacto.by_product
impacto.checks
```

El ejemplo representa Q100 millones adicionales de demanda final para `P010`.
`checks` debe quedar completamente aprobado antes de usar los resultados.

### Controles mínimos de una investigación

- `Δf` tiene longitud 152, valores finitos y códigos únicos.
- El producto objetivo no es uno de los seis productos con producción nula;
  estos solo son aptos para exploración descriptiva.
- Todas las magnitudes monetarias usan la misma valoración y año de precios.
- El choque no se aplica a subtotales además de sus componentes.
- La suma directa más indirecta coincide con la producción total calculada.
- Se identifican por separado resultados por producto y sumas agregadas.
- Los parámetros, la fecha de consulta, el código y el DOI quedan registrados.
- La interpretación reconoce coeficientes fijos, capacidad no restringida y
  estructura de 2013.
- Los impactos primarios se reportan como VAB; no se usa ni se suma el campo
  legado `producto_interno_bruto`.

## 5. Cómo leer los indicadores

| Campo | Lectura correcta |
|---|---|
| `multiplicador_produccion_domestica` | Producción doméstica total por unidad adicional de demanda final |
| `encadenamiento_atras_normalizado` | Intensidad de requerimientos hacia atrás respecto del promedio; promedio = 1 |
| `encadenamiento_adelante_normalizado` | Índice de sensibilidad de dispersión de Rasmussen-Hirschman: suma normalizada de fila de Leontief |
| `coeficiente_importacion_directa` | Insumos importados directos por unidad de producción |
| `requerimiento_importacion_total` | Insumos importados directos e indirectos por unidad de demanda final |
| `multiplicador_valor_agregado` | VAB doméstico asociado por unidad de demanda final |
| `multiplicador_empleo_puestos_por_millon` | Puestos asociados por millón de quetzales de demanda final |

Los indicadores comparan estructuras. No son beneficios netos, predicciones,
elasticidades ni recomendaciones de política. El índice de sensibilidad de
dispersión, a veces llamado encadenamiento hacia adelante, no equivale a un
multiplicador de oferta ni a un modelo de Ghosh.

## 6. Reproducir desde la fuente

Se recomienda Python 3.10 o posterior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python 04_reproduccion_python/reproducir_mip_guatemala_2013.py \
  --fuente /ruta/segura/MIP_AR2013_NPG.xlsx
python -m unittest discover -s 05_verificacion/tests -v
```

Al terminar, revise:

- `05_verificacion/controles_reproduccion.csv`;
- `05_verificacion/balances_por_producto.csv`;
- `05_verificacion/informe_reproduccion_computacional_mip_2013.txt`;
- `manifiesto_archivos.txt`.

La reproducción se detiene si falla un control obligatorio. Una huella de
fuente diferente exige revisar la procedencia y todos los controles; no debe
aceptarse solo porque el archivo abre.

## 7. Procedimiento operativo para una MIP futura

### Antes de programar

1. Preserve la fuente original y calcule su SHA-256.
2. Registre organismo, año, valoración, unidad, clasificación, enlace y
   condiciones de redistribución.
3. Determine si la nueva publicación es comparable: una tabla de oferta y
   utilización o una MIP industria-industria requiere transformaciones
   diferentes.
4. Inventaríe hojas, rangos, subtotales, ajustes, signos y celdas con fórmulas.

### Durante la adaptación

5. Cree una configuración por año y mantenga intacta la de 2013.
6. Construya una correspondencia de nomenclaturas cuando cambien códigos o
   agregaciones; publique la correspondencia y conserve la clasificación
   original.
7. Extraiga matrices y vectores sin balancear; compare primero con los totales
   oficiales.
8. Documente por separado cualquier corrección, imputación o balanceo. No use
   una tolerancia mayor para ocultar una discrepancia estructural.
9. Vuelva a construir `Aᵈ`, `Aᵐ` y `Lᵈ` solo cuando las identidades contables
   sean satisfactorias.

### Antes de publicar

10. Ejecute controles de estructura, balances, signos, producción nula, radio
    espectral, inversión y coeficientes.
11. Compare los agregados y patrones con 2013 usando una clasificación
    armonizada, pero separe cambios metodológicos de cambios económicos.
12. Use nombres con el nuevo año; actualice diccionario, notas, metadatos,
    pruebas, libro auditable y cuaderno.
13. Ejecute todo en un entorno limpio y compruebe que la versión pública pueda
    validarse sin redistribuir la fuente restringida.
14. Publique una versión y DOI nuevos, relacionados con 2013, sin sustituir el
    depósito histórico.

Una lista metodológica más detallada está en
`metodologia_cuantitativa_mip_2013.md`, sección 11.

## 8. Qué no debe hacerse

- No corregir manualmente el Excel derivado para luego usarlo como entrada.
- No sumar `Aᵐ` a la inversa doméstica sin redefinir el modelo.
- No mezclar quetzales con millones de quetzales.
- No interpretar puestos asociados como creación neta de empleo.
- No sumar ni usar para impactos la fila legado `producto_interno_bruto`. El
  repositorio modela VAB y no publica un multiplicador de PIB.
- No usar `P069`, `P086`, `P087`, `P089`, `P151` o `P152` como objetivo de un
  choque: carecen de coeficientes técnicos observados.
- No comparar coeficientes entre años sin armonizar valoración y nomenclatura.
- No reemplazar los archivos 2013 con una matriz futura que use los mismos
  nombres.
