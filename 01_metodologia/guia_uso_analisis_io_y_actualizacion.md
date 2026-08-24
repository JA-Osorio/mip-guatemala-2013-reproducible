# Guía de uso para análisis IO y actualización

## 1. Finalidad

Este repositorio deja la MIP producto por producto de Guatemala 2013 lista para análisis insumo-producto. La transformación conserva la separación entre insumos domésticos e importados, las cuentas primarias y los controles contables necesarios para construir modelos transparentes y reproducibles.

## 2. Archivos que debe usar

| Necesidad analítica | Archivo |
|---|---|
| Flujos intermedios domésticos | `02_resultados_y_diccionario/matrices/Z_domestica_2013.csv` |
| Flujos intermedios importados | `02_resultados_y_diccionario/matrices/Z_importada_2013.csv` |
| Coeficientes técnicos domésticos | `02_resultados_y_diccionario/matrices/A_domestica_2013.csv` |
| Coeficientes técnicos importados | `02_resultados_y_diccionario/matrices/A_importada_2013.csv` |
| Inversa de Leontief doméstica | `02_resultados_y_diccionario/matrices/Leontief_domestica_2013.csv` |
| Demanda final por componente | `02_resultados_y_diccionario/vectores/demanda_final_domestica_2013.csv` |
| Producción, PIB y empleo | `02_resultados_y_diccionario/vectores/produccion_y_utilizacion_2013.csv` |
| Coeficientes primarios | `02_resultados_y_diccionario/vectores/coeficientes_primarios_2013.csv` |
| Indicadores IO precalculados | `02_resultados_y_diccionario/indicadores_io_2013.csv` |

Los CSV de matrices incluyen `codigo` y `producto` en las dos primeras columnas. Las columnas restantes siguen el orden `P001`–`P152`. No debe alterarse ese orden al convertirlas en arreglos numéricos.

## 3. Modelo de cantidades

Sea `Aᵈ` la matriz de coeficientes domésticos, `Aᵐ` la matriz de coeficientes importados y `Lᵈ = (I - Aᵈ)⁻¹` la inversa de Leontief doméstica. Para un vector de demanda final adicional `Δf`:

```text
Δx = Lᵈ Δf
Δm = Aᵐ Lᵈ Δf
Δv = diag(v) Lᵈ Δf
Δe = diag(e) Lᵈ Δf
```

`v` es el coeficiente de valor agregado por unidad de producción y `e` el coeficiente de puestos de trabajo por millón de quetzales de producción. Las importaciones se tratan como fugas del circuito productivo doméstico.

## 4. Indicadores publicados

`indicadores_io_2013.csv` contiene:

- multiplicador de producción doméstica;
- encadenamiento hacia atrás normalizado;
- encadenamiento hacia adelante normalizado;
- coeficiente directo de importación;
- requerimiento total de importación;
- multiplicador de valor agregado;
- multiplicador de empleo por millón de quetzales de demanda final.

Los encadenamientos normalizados siguen la formulación de Rasmussen-Hirschman basada en sumas de columnas y filas de la inversa de Leontief. Un valor mayor que uno indica una intensidad superior al promedio del sistema.

## 5. Flujo recomendado para una investigación

1. Definir la pregunta, el producto o conjunto de productos y la unidad del choque.
2. Construir `Δf` con 152 posiciones y documentar la correspondencia de códigos.
3. Calcular `Δx` con la inversa doméstica.
4. Aplicar los coeficientes importados, de valor agregado o de empleo según la pregunta.
5. Separar resultados directos, indirectos y totales cuando la interpretación lo requiera.
6. Ejecutar controles de dimensiones, unidades, signos y orden de productos.
7. Declarar los supuestos del modelo: coeficientes fijos, ausencia de restricciones de capacidad y estructura económica de 2013.
8. Guardar parámetros y resultados en archivos separados de esta base canónica y citar la versión y el DOI utilizados.

## 6. Cómo incorporar una MIP oficial actualizada

Una nueva publicación oficial debe tratarse como una versión nueva, no como reemplazo silencioso de 2013.

1. Conservar intacta la versión y el DOI de 2013.
2. Registrar nombre, fecha, enlace, licencia y huella SHA-256 de la nueva fuente.
3. Crear una configuración específica para el nuevo año y verificar hojas, rangos, unidades, valoración y número de productos.
4. Construir una tabla de correspondencia si cambia la nomenclatura; no forzar equivalencias sin documentarlas.
5. Actualizar los sufijos de año de todos los resultados y los metadatos internos.
6. Ejecutar la conversión completa y exigir que todos los controles obligatorios sean aprobados.
7. Comparar agregados con la fuente y documentar revisiones metodológicas.
8. Ejecutar el cuaderno y las pruebas sobre el paquete público sin la fuente primaria.
9. Publicar una versión etiquetada y un depósito nuevo en Zenodo, vinculado conceptualmente con las versiones anteriores.

Si la estructura del libro cambia, deben modificarse primero los rangos de `config_mip.yaml` y las pruebas de extracción. Las salidas no deben generarse hasta que el mapeo de filas y columnas haya sido validado.

## 7. Reproducibilidad

El cuaderno de Colab es la entrada didáctica. El script `reproducir_mip_guatemala_2013.py` es la entrada canónica para reconstruir todos los resultados cuando se dispone de la fuente primaria. Las pruebas públicas verifican matrices, identidades, metadatos e indicadores sin redistribuir el libro oficial.
