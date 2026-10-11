# Procedencia y cambios de la preparación

Fecha de revisión: 11 de octubre de 2026. Repositorio de origen: `alcaudon1974/gpt-5-6-sol-context-optimizer`, privado, rama `main`. Commit consultado: `da58ab3cffec2844ef99253ec6f416c6d2ee97d3`. El único commit visible en la consulta de historial identifica a Alfonso Ángel como autor y está fechado el 11 de agosto de 2026.

El 11 de octubre de 2026 Alfonso Ángel confirmó expresamente que puede licenciar este código bajo MIT y autorizó publicar únicamente la copia revisada como `alcaudon1974/nexura-context-optimizer`. Se incorporó `LICENSE` con Copyright (c) 2026 Alfonso Ángel y se retiró la propuesta de licencia pendiente de la copia publicable. La publicación sigue pendiente de ejecución; esta autorización no cambia la visibilidad de los repositorios privados de origen.

Se revisaron el README, las instrucciones y los criterios del origen antes de seleccionar estos cinco archivos. Esta copia no conserva la ubicación privada, las instrucciones de ejecución de Hermes ni su historial Git.

| Archivo del origen | SHA del blob de origen | Archivo del candidato y cambio |
|---|---|---|
| `src/context_optimizer.py` | `26ac477cf4df1bdcebda2fe6d96788e0e3bf0234` | `src/nexura_context_optimizer/context_optimizer.py`: núcleo conservado, sin cambios lógicos. |
| `src/cli.py` | `d5564ed290ae7095b3bd43cf9c8841ad63f9fe6d` | `src/nexura_context_optimizer/cli.py`: adaptado a paquete JSON, restauración, directorio explícito, lectura acotada y manejo de errores. |
| `src/__init__.py` | `5960790e2eed1a7939b614e0b7766ec8c40daf35` | `src/nexura_context_optimizer/__init__.py`: docstring conservado. |
| `tests/test_context_optimizer.py` | `1fc7a7598b8853fdf02324bccda3e3ee92e21dbd` | `tests/test_context_optimizer.py`: casos conservados; importaciones adaptadas al paquete. |
| `tests/test_cli.py` | `baa37e97d349257312b586dbdc5a4bf0ca1ac153` | `tests/test_cli.py`: protección de archivos y rutas conservada y ampliada; escenarios JSON/restauración, archivos temporales y procesos sin ventanas. |

La copia textual normaliza el final de fichero y no se presenta como copia binaria idéntica de estos blobs. Las huellas locales se recogen aparte en `MANIFIESTO_SHA256.json`.

Archivos nuevos: `package.py`, `test_package.py`, `pyproject.toml`, README, este documento, licencia MIT autorizada, texto sintético de ejemplo y recibo de verificación. No hay código añadido que contacte con servicios externos, ejecute modelos o modifique agentes.

No se copiaron `src/hermes_benchmark.py`, sus pruebas, `tests/test_evidence.py`, los directorios `evidence/`, `results/` o `benchmarks/`, el README y AGENTS originales ni el historial Git. Se excluyeron telemetría, identificadores de sesiones, rutas privadas, configuraciones, credenciales y resultados operativos.

Se observó un fallo esperado antes de implementar el módulo nuevo de empaquetado. Después pasaron la prueba de ida y vuelta y las 19 pruebas de la suite. Son pruebas sintéticas locales, no nuevos experimentos con GPT, Hermes u OpenClaw. La actualización de licencia y documentación no cambió el código o las pruebas y no requirió repetirlas. Estas comprobaciones se realizaron antes de la publicación y no ejecutaron workflows de GitHub, crearon cuentas o modificaron el repositorio privado original.
