VERIFICACIÓN

controles_reproduccion.csv registra 22 controles de estructura, matrices,
balances y modelo.

balances_por_producto.csv conserva los residuos por producto y la diferencia
publicada entre producción y utilización.

comparacion_con_construcciones_previas.csv documenta el contraste con dos
libros históricos proporcionados por el equipo. Esos libros no se redistribuyen.

tests/test_publicacion.py puede ejecutarse aun cuando la fuente original no
esté disponible, porque valida los CSV publicados. Si la fuente está en su ruta
esperada, también verifica su huella y reconstrucción completa.

