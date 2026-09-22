# Pruebas de carga de Reservas

Este módulo usa Locust 2.x y solo ejecuta consultas de lectura contra endpoints reales
de `reservas-solicitudes-service`.

La prueba integrada entra exclusivamente por el API Gateway en el puerto `8080`.

## Preparación

```powershell
python -m pip install -r tests/load/requirements.txt
```

El host no está codificado en `locustfile.py`. Debe proporcionarse mediante `--host`
o la variable de entorno nativa `LOCUST_HOST`. La prueba también requiere una cuenta
de pruebas con permiso `RESERVA_LEER`, configurada mediante `LOCUST_USERNAME` y
`LOCUST_PASSWORD`. Por ejemplo, para una instancia local:

```powershell
$env:LOCUST_HOST = "http://localhost:8080"
$env:LOCUST_USERNAME = "<USUARIO_PRUEBAS>"
$env:LOCUST_PASSWORD = "<CONTRASENA_PRUEBAS>"
```

## Escenario nominal

Usa el `locustfile.py` principal con 50 usuarios durante 5 minutos. Los usuarios se
incorporan a razón de 10 por segundo hasta alcanzar la carga nominal:

```powershell
python -m locust -f tests/load/locustfile.py --headless --users 50 --spawn-rate 10 --run-time 5m
```

## Escenario ramp

`ramp_locustfile.py` reutiliza `ReservasUser` y añade únicamente `RampTo200Users`.
La forma calcula cada segundo el objetivo lineal correspondiente al tiempo transcurrido:
parte de 0, agrega aproximadamente un usuario cada 3 segundos, alcanza cerca de 200
usuarios al final y detiene la ejecución al completar 10 minutos.

```powershell
python -m locust -f tests/load/ramp_locustfile.py --headless
```

También se puede reemplazar `LOCUST_HOST` con `--host http://localhost:8080` en cada
comando. Antes de ejecutar estos escenarios debe comprobarse que el host apunta al
ambiente autorizado. No es obligatorio insertar reservas: si el listado está vacío,
el detalle se omite de forma controlada.

Las métricas se agrupan con los nombres `GET /api/v1/reservas` y
`GET /api/v1/reservas/{id}`. El detalle solo utiliza identificadores UUID descubiertos
en respuestas válidas del listado; si no hay reservas, se continúa consultando el
listado sin fabricar IDs ni crear datos.

En CI se ejecuta un smoke de carga obligatorio y controlado contra el stack temporal
del job `integration`: 2 usuarios, incorporación de 1 usuario/s y duración de 10
segundos. Nunca se dirige automáticamente a un ambiente externo.
