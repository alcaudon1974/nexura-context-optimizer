# Nexura Context Optimizer

Herramienta experimental de Python que agrupa párrafos idénticos consecutivos y permite recuperar el archivo UTF-8 original byte por byte. Sirve para estudiar representaciones más breves de textos repetitivos, preparar contextos y verificar que una transformación conserva los datos.

Versión experimental bajo licencia MIT, autorizada por Alfonso Ángel el 11 de octubre de 2026. La herramienta funciona sin modelos ni llamadas de red. Las pruebas descritas verifican esta utilidad independiente; la integración con agentes requiere su propia evaluación.

## Qué hace

- `optimize` crea un paquete JSON con texto agrupado, diccionario, versión, codificación, separador de párrafos, longitud original y SHA-256.
- `restore` valida el paquete y recupera los bytes originales, incluidos acentos, Unicode, BOM y saltos de línea LF o CRLF.
- Los textos sin repeticiones consecutivas suficientemente largas quedan sin transformar.
- Antes de guardar un paquete, comprueba que puede restaurar exactamente el original. No reemplaza archivos existentes y limita las rutas al directorio de trabajo elegido.
- Funciona sin modelos, cuentas, claves ni llamadas de red. El código y las pruebas utilizan la biblioteca estándar de Python.

El campo `packed_text` es una representación del contexto. El paquete completo también guarda metadatos y diccionario, por lo que puede ocupar más que el archivo original. Las cantidades de caracteres que informa la herramienta no son conteos de tokens ni pruebas de ahorro económico. La comprensión de esta representación por un modelo requiere medición independiente.

## Ejemplo en PowerShell

Requiere Python 3.10 o superior. Desde esta carpeta:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m nexura_context_optimizer.cli --workspace './examples' optimize entrada.txt --output paquete.json
python -m nexura_context_optimizer.cli --workspace './examples' restore paquete.json --output restaurado.txt
```

El ejemplo es texto sintético. Elija nombres de salida nuevos en cada ejecución. `--workspace` se escribe antes de `optimize` o `restore`; por defecto utiliza el directorio actual. Se admiten rutas relativas a ese directorio o rutas absolutas contenidas en él.

```powershell
python -m unittest discover -s tests -v
```

Se verificaron 19 pruebas locales con Python 3.12.14: ida y vuelta exacta, corrupción de datos y metadatos, entradas UTF-8 inválidas, límites de repetición, marcadores literales, protección de archivos y comandos reales de consola ejecutados sin ventanas auxiliares. `VERIFICACION.json` conserva el alcance y el resultado.

## Límites

- Solo UTF-8 válido y agrupación de repeticiones consecutivas de párrafos; no realiza resúmenes semánticos ni búsqueda de información.
- Entrada original máxima: 8 MiB. Paquete leído o escrito por la consola: 32 MiB. Restauración: máximo 100 000 repeticiones por grupo y 8 Mi caracteres, con verificación adicional de la longitud original en bytes.
- SHA-256 detecta corrupción accidental. No es firma, cifrado ni prueba de quién creó un paquete.
- El paquete contiene el texto y el diccionario en claro. Se debe revisar su contenido antes de compartirlo.
- Las pruebas no miden calidad de respuestas de modelos, costes, integración con agentes ni prestaciones en otros sistemas operativos. No se verificó la instalación como paquete; `pyproject.toml` prepara ese paso y declara cero dependencias de ejecución. Crear una distribución requiere la herramienta de construcción indicada allí.

Este candidato conserva el núcleo del experimento original y añade un formato intercambiable y restauración por consola. El historial y los resultados de sesiones reales no están incluidos. No promete un porcentaje de ahorro ni una instancia gratuita. Una eventual solicitud de apoyo debe describir esta utilidad pública de forma fiel y someter el uso del alojamiento a las condiciones del proveedor.

La procedencia y los cambios constan en `PROCEDENCIA.md`. La licencia MIT consta en `LICENSE` (Copyright © 2026 Alfonso Ángel).
