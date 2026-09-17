-- Datos reproducibles para pruebas de rendimiento de reservas_db.
-- Total: 100 000 solicitudes, 100 000 reservas, 200 000 eventos de historial,
-- 10 000 bloqueos y una configuración (410 001 filas).
--
-- Las vistas son temporales, no materializan datos y desaparecen al cerrar la
-- sesión. Cada INSERT escribe como máximo 10 000 filas y su COMMIT termina
-- antes de iniciar el lote siguiente.

USE reservas_db;
SET experimental_enable_temp_tables = on;

INSERT INTO configuraciones_reserva (
    id, anticipacion_minima_horas, anticipacion_maxima_dias,
    duracion_minima_minutos, duracion_maxima_minutos,
    permite_fines_semana, activo, creada_en, actualizada_en, version
)
VALUES (
    '60000000-0000-4000-8000-000000000001'::UUID,
    2, 180, 30, 240, TRUE, TRUE,
    '2026-01-01 00:00:00+00'::TIMESTAMPTZ,
    '2026-01-01 00:00:00+00'::TIMESTAMPTZ,
    0
)
ON CONFLICT (id) DO NOTHING;

CREATE TEMP VIEW seed_solicitudes AS
SELECT
    i AS seed_i,
    ('00000000-0000-4000-8000-' || lpad(i::STRING, 12, '0'))::UUID AS id,
    ('10000000-0000-4000-8000-' || lpad(((i - 1) % 5000 + 1)::STRING, 12, '0'))::UUID AS solicitante_id,
    ('11000000-0000-4000-8000-' || lpad(((i - 1) % 500 + 1)::STRING, 12, '0'))::UUID AS docente_id,
    ('12000000-0000-4000-8000-' || lpad(((i - 1) % 100 + 1)::STRING, 12, '0'))::UUID AS laboratorio_id,
    ('13000000-0000-4000-8000-' || lpad(((i - 1) % 300 + 1)::STRING, 12, '0'))::UUID AS materia_id,
    ('14000000-0000-4000-8000-' || lpad(((i - 1) % 8 + 1)::STRING, 12, '0'))::UUID AS periodo_lectivo_id,
    DATE '2026-07-01' + ((i - 1) % 549)::INT AS fecha_reserva,
    CASE (i - 1) % 4 WHEN 0 THEN TIME '08:00:00' WHEN 1 THEN TIME '10:00:00' WHEN 2 THEN TIME '14:00:00' ELSE TIME '16:00:00' END AS hora_inicio,
    CASE (i - 1) % 4 WHEN 0 THEN TIME '10:00:00' WHEN 1 THEN TIME '12:00:00' WHEN 2 THEN TIME '16:00:00' ELSE TIME '18:00:00' END AS hora_fin,
    5 + ((i - 1) % 36)::INT AS numero_participantes,
    'Carga académica reproducible para rendimiento' AS motivo,
    'Semilla SCLI número ' || i::STRING AS observacion,
    'APROBADA' AS estado,
    'seed-solicitud-' || lpad(i::STRING, 12, '0') AS clave_idempotencia,
    TIMESTAMPTZ '2026-01-01 00:00:00+00' + ((i - 1) % 259200) * INTERVAL '1 second' AS creada_en,
    TIMESTAMPTZ '2026-01-01 00:00:00+00' + ((i - 1) % 259200) * INTERVAL '1 second' AS actualizada_en,
    0::INT8 AS version
FROM generate_series(1, 100000) AS serie(i);

-- Diez lotes de 10 000 solicitudes; cada sentencia se confirma por separado.
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 1 AND 10000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 10001 AND 20000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 20001 AND 30000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 30001 AND 40000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 40001 AND 50000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 50001 AND 60000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 60001 AND 70000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 70001 AND 80000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 80001 AND 90000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO solicitudes_reserva SELECT id, solicitante_id, docente_id, laboratorio_id, materia_id, periodo_lectivo_id, fecha_reserva, hora_inicio, hora_fin, numero_participantes, motivo, observacion, estado, clave_idempotencia, creada_en, actualizada_en, version FROM seed_solicitudes WHERE seed_i BETWEEN 90001 AND 100000 ON CONFLICT (id) DO NOTHING; COMMIT;

CREATE TEMP VIEW seed_reservas AS
SELECT
    i AS seed_i,
    ('20000000-0000-4000-8000-' || lpad(i::STRING, 12, '0'))::UUID AS id,
    ('00000000-0000-4000-8000-' || lpad(i::STRING, 12, '0'))::UUID AS solicitud_id,
    ('12000000-0000-4000-8000-' || lpad(((i - 1) % 100 + 1)::STRING, 12, '0'))::UUID AS laboratorio_id,
    ('15000000-0000-4000-8000-' || lpad(((i - 1) % 50 + 1)::STRING, 12, '0'))::UUID AS responsable_id,
    DATE '2026-07-01' + ((i - 1) % 549)::INT AS fecha_reserva,
    CASE (i - 1) % 4 WHEN 0 THEN TIME '08:00:00' WHEN 1 THEN TIME '10:00:00' WHEN 2 THEN TIME '14:00:00' ELSE TIME '16:00:00' END AS hora_inicio,
    CASE (i - 1) % 4 WHEN 0 THEN TIME '10:00:00' WHEN 1 THEN TIME '12:00:00' WHEN 2 THEN TIME '16:00:00' ELSE TIME '18:00:00' END AS hora_fin,
    CASE (i - 1) % 10 WHEN 0 THEN 'FINALIZADA' WHEN 1 THEN 'EN_CURSO' ELSE 'PROGRAMADA' END AS estado,
    'RES-SEED-' || lpad(i::STRING, 12, '0') AS codigo_reserva,
    TIMESTAMPTZ '2026-01-01 00:05:00+00' + ((i - 1) % 259200) * INTERVAL '1 second' AS creada_en,
    TIMESTAMPTZ '2026-01-01 00:05:00+00' + ((i - 1) % 259200) * INTERVAL '1 second' AS actualizada_en,
    0::INT8 AS version
FROM generate_series(1, 100000) AS serie(i);

-- Diez lotes de 10 000 reservas.
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 1 AND 10000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 10001 AND 20000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 20001 AND 30000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 30001 AND 40000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 40001 AND 50000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 50001 AND 60000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 60001 AND 70000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 70001 AND 80000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 80001 AND 90000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO reservas SELECT id, solicitud_id, laboratorio_id, responsable_id, fecha_reserva, hora_inicio, hora_fin, estado, codigo_reserva, creada_en, actualizada_en, version FROM seed_reservas WHERE seed_i BETWEEN 90001 AND 100000 ON CONFLICT (id) DO NOTHING; COMMIT;

CREATE TEMP VIEW seed_historial AS
SELECT
    i AS seed_i,
    CASE WHEN i <= 100000
        THEN ('30000000-0000-4000-8000-' || lpad(i::STRING, 12, '0'))::UUID
        ELSE ('40000000-0000-4000-8000-' || lpad((i - 100000)::STRING, 12, '0'))::UUID
    END AS id,
    ('00000000-0000-4000-8000-' || lpad((((i - 1) % 100000) + 1)::STRING, 12, '0'))::UUID AS solicitud_id,
    CASE WHEN i <= 100000 THEN NULL ELSE 'PENDIENTE' END AS estado_anterior,
    CASE WHEN i <= 100000 THEN 'PENDIENTE' ELSE 'APROBADA' END AS estado_nuevo,
    CASE WHEN i <= 100000
        THEN ('10000000-0000-4000-8000-' || lpad((((i - 1) % 5000) + 1)::STRING, 12, '0'))::UUID
        ELSE ('15000000-0000-4000-8000-' || lpad((((i - 1) % 50) + 1)::STRING, 12, '0'))::UUID
    END AS usuario_accion_id,
    CASE WHEN i <= 100000 THEN 'Solicitud creada por semilla reproducible' ELSE 'Solicitud aprobada por semilla reproducible' END AS comentario,
    TIMESTAMPTZ '2026-01-01 00:00:00+00'
        + CASE WHEN i <= 100000 THEN INTERVAL '0 seconds' ELSE INTERVAL '5 minutes' END
        + (((i - 1) % 100000) % 259200) * INTERVAL '1 second' AS fecha_hora
FROM generate_series(1, 200000) AS serie(i);

-- Veinte lotes de 10 000 eventos de historial.
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 1 AND 10000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 10001 AND 20000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 20001 AND 30000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 30001 AND 40000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 40001 AND 50000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 50001 AND 60000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 60001 AND 70000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 70001 AND 80000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 80001 AND 90000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 90001 AND 100000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 100001 AND 110000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 110001 AND 120000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 120001 AND 130000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 130001 AND 140000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 140001 AND 150000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 150001 AND 160000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 160001 AND 170000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 170001 AND 180000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 180001 AND 190000 ON CONFLICT (id) DO NOTHING; COMMIT;
BEGIN; INSERT INTO historial_solicitudes SELECT id, solicitud_id, estado_anterior, estado_nuevo, usuario_accion_id, comentario, fecha_hora FROM seed_historial WHERE seed_i BETWEEN 190001 AND 200000 ON CONFLICT (id) DO NOTHING; COMMIT;

CREATE TEMP VIEW seed_bloqueos AS
SELECT
    i AS seed_i,
    ('50000000-0000-4000-8000-' || lpad(i::STRING, 12, '0'))::UUID AS id,
    ('12000000-0000-4000-8000-' || lpad(((i - 1) % 100 + 1)::STRING, 12, '0'))::UUID AS laboratorio_id,
    DATE '2026-07-01' + ((i - 1) % 549)::INT AS fecha,
    CASE (i - 1) % 2 WHEN 0 THEN TIME '12:00:00' ELSE TIME '18:00:00' END AS hora_inicio,
    CASE (i - 1) % 2 WHEN 0 THEN TIME '13:00:00' ELSE TIME '19:00:00' END AS hora_fin,
    'Mantenimiento programado de semilla' AS motivo,
    ('15000000-0000-4000-8000-' || lpad(((i - 1) % 50 + 1)::STRING, 12, '0'))::UUID AS creado_por,
    ((i - 1) % 5) <> 0 AS activo,
    TIMESTAMPTZ '2026-01-01 00:00:00+00' + ((i - 1) % 259200) * INTERVAL '1 second' AS creado_en,
    0::INT8 AS version
FROM generate_series(1, 10000) AS serie(i);

-- Un lote de 10 000 bloqueos.
BEGIN; INSERT INTO bloqueos_agenda SELECT id, laboratorio_id, fecha, hora_inicio, hora_fin, motivo, creado_por, activo, creado_en, version FROM seed_bloqueos WHERE seed_i BETWEEN 1 AND 10000 ON CONFLICT (id) DO NOTHING; COMMIT;

DROP VIEW seed_bloqueos;
DROP VIEW seed_historial;
DROP VIEW seed_reservas;
DROP VIEW seed_solicitudes;
