INSERT INTO materias (id_materia, nombre_materia, creditos, nivel_prioridad, descripcion) VALUES
(1, 'Matemáticas', 4, 1, 'Evalúa razonamiento cuantitativo en Estadística, Geometría y Cálculo y Álgebra.');

INSERT INTO componentes (id_componente, id_materia, nombre_componente, descripcion, preguntas_por_examen) VALUES
(1, 1, 'Estadística',       'Medidas de tendencia central y dispersión, probabilidad y conteo.', 10),
(2, 1, 'Geometría',         'Áreas, perímetros, volúmenes, ángulos, Pitágoras y geometría analítica.', 10),
(3, 1, 'Cálculo y Álgebra', 'Ecuaciones, funciones, potencias, logaritmos, límites, derivadas e integrales.', 10);

INSERT INTO nivel_dificultad (id_nivel, nombre_nivel, descripcion, peso) VALUES
(1, 'Básico',     'Aplicación directa de una fórmula o concepto.', 1.0),
(2, 'Intermedio', 'Requiere dos o más pasos de razonamiento.', 1.5),
(3, 'Avanzado',   'Requiere análisis, combinación de conceptos o cálculo formal.', 2.0);

SELECT setval(pg_get_serial_sequence('materias', 'id_materia'),           (SELECT MAX(id_materia) FROM materias));
SELECT setval(pg_get_serial_sequence('componentes', 'id_componente'),     (SELECT MAX(id_componente) FROM componentes));
SELECT setval(pg_get_serial_sequence('nivel_dificultad', 'id_nivel'),     (SELECT MAX(id_nivel) FROM nivel_dificultad));
