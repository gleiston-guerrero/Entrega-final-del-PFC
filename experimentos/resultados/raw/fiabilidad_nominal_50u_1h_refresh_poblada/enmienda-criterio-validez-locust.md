# Enmienda del criterio operativo de validez de las repeticiones

## Motivo

Durante la repetición oficial rep-07 se observó un HTTP 500 real y Locust
finalizó con código de salida 1, aunque la ejecución completó la ventana
planificada de 3600 segundos, mantuvo tráfico de negocio no degenerado,
ejecutó renovaciones de sesión y produjo todos los artefactos de evidencia.

El gate auxiliar `exit_code_zero`, utilizado inicialmente en el procesamiento
posterior de las repeticiones, podía provocar el descarte de una observación
desfavorable precisamente por contener un fallo HTTP. Esto introduciría un
sesgo de selección incompatible con el objetivo de medir fiabilidad.

## Criterio corregido

A partir de rep-07, el código de salida de Locust se conserva íntegramente
como dato observado, pero no se utiliza por sí solo como criterio de
exclusión de una repetición.

Una repetición se considera estructuralmente válida cuando:

- completa la duración prevista dentro de la tolerancia establecida;
- ejecuta las 50 autenticaciones iniciales esperadas;
- presenta renovaciones de sesión;
- contiene tráfico GET de listado y consulta por identificador;
- mantiene tráfico de negocio y consultas por identificador después de
  los primeros 900 segundos;
- no contiene eventos fuera de la ventana temporal registrada;
- produce los artefactos finales requeridos;
- conserva íntegramente cualquier HTTP 4xx/5xx observado.

Los HTTP 5xx son parte de la variable de respuesta de fiabilidad y no una
causa para eliminar, reiniciar o repetir una ejecución.

## Alcance

Esta enmienda modifica exclusivamente el criterio operativo de validación
posterior de las repeticiones. No modifica:

- el software desplegado;
- el dataset controlado;
- el número de usuarios;
- la tasa de incorporación;
- la duración;
- el harness de Locust;
- los endpoints ejercitados;
- los resultados raw ya obtenidos.

rep-07 y rep-08 conservaron sus códigos de salida reales y todos los HTTP
5xx registrados. Ninguna de esas observaciones fue eliminada o sustituida.
