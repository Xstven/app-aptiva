SELECT p.id_pregunta, p.enunciado, o.letra, o.texto, o.es_correcta
FROM (SELECT id_pregunta, enunciado FROM preguntas
      WHERE id_componente = 1 AND activa ORDER BY random() LIMIT 10) p
JOIN opciones_respuesta o ON o.id_pregunta = p.id_pregunta
ORDER BY p.id_pregunta, o.letra;

SELECT * FROM vw_banco_por_componente ORDER BY nombre_componente, nombre_nivel;

SELECT p.id_pregunta, COUNT(o.id_opcion) AS opciones, COUNT(*) FILTER (WHERE o.es_correcta) AS correctas
FROM preguntas p LEFT JOIN opciones_respuesta o ON o.id_pregunta = p.id_pregunta
GROUP BY p.id_pregunta
HAVING COUNT(o.id_opcion) <> 4 OR COUNT(*) FILTER (WHERE o.es_correcta) <> 1;

SELECT * FROM vw_historial_estudiante ORDER BY fecha_inicio DESC;

SELECT c.nombre_componente, r.aciertos, r.total_preguntas, r.porcentaje
FROM resultados_componente r JOIN componentes c ON c.id_componente = r.id_componente
WHERE r.id_examen = 1;

SELECT d.id_examen, p.id_componente, COUNT(*) AS preguntas
FROM detalle_examen d JOIN preguntas p ON p.id_pregunta = d.id_pregunta
GROUP BY d.id_examen, p.id_componente HAVING COUNT(*) <> 10;

SELECT p.id_pregunta, c.nombre_componente, LEFT(p.enunciado, 60) AS enunciado,
       COUNT(*) AS veces, ROUND(100.0 * AVG(d.es_correcta::int), 1) AS porcentaje_acierto
FROM detalle_examen d
JOIN examenes e    ON e.id_examen = d.id_examen AND e.estado = 'FINALIZADO'
JOIN preguntas p   ON p.id_pregunta = d.id_pregunta
JOIN componentes c ON c.id_componente = p.id_componente
GROUP BY p.id_pregunta, c.nombre_componente, p.enunciado
ORDER BY porcentaje_acierto, veces DESC LIMIT 10;

SELECT fortalezas, debilidades, plan_estudio, modelo_ia, tiempo_respuesta_s,
       resumen_enviado ->> 'puntaje_global' AS puntaje
FROM diagnosticos_ia WHERE id_examen = 1;
