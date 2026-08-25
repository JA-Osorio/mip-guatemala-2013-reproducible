MIP GUATEMALA 2013 REPRODUCIBLE — v1.0.0

DOI: https://doi.org/10.5281/zenodo.22086008

Paquete para extraer, transformar y validar la matriz insumo-producto producto
por producto de Guatemala 2013. La fuente oficial se mantiene fuera de la
distribución pública; el script maestro acepta su ruta mediante --fuente.

Comando principal:

  python 04_reproduccion_python/reproducir_mip_guatemala_2013.py

Pruebas:

  python -m unittest discover -s 05_verificacion/tests -v

Salida validada: 152 productos, matrices doméstica e importada separadas,
coeficientes técnicos, inversa de Leontief doméstica, cuentas primarias,
demanda final, multiplicadores, choques unitarios, rankings, balances,
metadatos y manifiesto.

Consulte README.md para la ruta didáctica, la tabla de archivos, los resultados,
los controles y el acceso directo al cuaderno ejecutable en Google Colab. La
especificación completa está en
01_metodologia/metodologia_cuantitativa_mip_2013.md y el procedimiento para una
MIP futura en 01_metodologia/guia_uso_analisis_io_y_actualizacion.md.
