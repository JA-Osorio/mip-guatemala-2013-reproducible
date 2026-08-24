MIP GUATEMALA 2013 REPRODUCIBLE — v0.1.0

Paquete para extraer, transformar y validar la matriz insumo-producto producto
por producto de Guatemala 2013. La fuente oficial se mantiene fuera de la
distribución pública; el script maestro acepta su ruta mediante --fuente.

Comando principal:

  python 04_reproduccion_python/reproducir_mip_guatemala_2013.py

Pruebas:

  python -m unittest discover -s 05_verificacion/tests -v

Salida validada: 152 productos, matrices doméstica e importada separadas,
coeficientes técnicos, inversa de Leontief doméstica, cuentas primarias,
demanda final, balances, metadatos y manifiesto.

Consulte README.md para la metodología, las limitaciones y la estructura
completa. Este repositorio no contiene escenarios de etanol.

