from __future__ import annotations

import atexit
import json
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL, PREGUNTAS_POR_COMPONENTE, ZONA_HORARIA


class ErrorBancoPreguntas(Exception):
    pass


class ErrorConfiguracion(Exception):
    pass


_pool: ConnectionPool | None = None
_url_pool: str | None = None

def _fecha(col: str) -> str:
    return f"to_char({col} AT TIME ZONE '{ZONA_HORARIA}', 'YYYY-MM-DD HH24:MI:SS')"


def _obtener_pool(url: str) -> ConnectionPool:
    global _pool, _url_pool
    if _pool is None or _url_pool != url:
        if _pool is not None:
            _pool.close()
        _pool = ConnectionPool(url, min_size=0, max_size=5, open=True, timeout=30,
                               kwargs={"row_factory": dict_row, "autocommit": False,
                                       "prepare_threshold": None},
                               check=ConnectionPool.check_connection)
        _url_pool = url
    return _pool


@contextmanager
def conexion(url: str | None = None):
    url = url or DATABASE_URL
    if not url:
        raise ErrorConfiguracion("No se configuró DATABASE_URL (archivo .env o Secrets de Streamlit).")
    with _obtener_pool(url).connection() as con:
        yield con


def cerrar_pool() -> None:
    global _pool, _url_pool
    if _pool is not None:
        _pool.close()
    _pool, _url_pool = None, None


atexit.register(cerrar_pool)


def bd_lista(url: str | None = None) -> bool:
    try:
        with conexion(url) as con:
            return con.execute("SELECT to_regclass('public.preguntas') IS NOT NULL AS ok").fetchone()["ok"]
    except Exception:
        return False


def materias(con) -> list[dict]:
    return con.execute("SELECT * FROM materias WHERE activa ORDER BY id_materia").fetchall()


def componentes(con, id_materia: int) -> list[dict]:
    return con.execute("SELECT * FROM componentes WHERE id_materia = %s ORDER BY id_componente",
                       (id_materia,)).fetchall()


def niveles(con) -> list[dict]:
    return con.execute("SELECT id_nivel, nombre_nivel FROM nivel_dificultad ORDER BY id_nivel").fetchall()


def obtener_o_crear_estudiante(con, documento: str, nombres: str, apellidos: str,
                               correo: str | None = None, programa: str | None = None,
                               semestre: int | None = None) -> int:
    fila = con.execute(
        """INSERT INTO estudiantes (documento, nombres, apellidos, correo, programa, semestre)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (documento) DO UPDATE SET
               nombres = EXCLUDED.nombres, apellidos = EXCLUDED.apellidos,
               correo = COALESCE(EXCLUDED.correo, estudiantes.correo),
               programa = COALESCE(EXCLUDED.programa, estudiantes.programa),
               semestre = COALESCE(EXCLUDED.semestre, estudiantes.semestre)
           RETURNING id_estudiante""",
        (documento.strip(), nombres.strip(), apellidos.strip(), correo or None, programa or None, semestre)).fetchone()
    return fila["id_estudiante"]


def buscar_estudiante(con, documento: str) -> dict | None:
    return con.execute("SELECT id_estudiante, documento, nombres, apellidos, correo, programa, semestre "
                       "FROM estudiantes WHERE documento = %s", (documento.strip(),)).fetchone()


def listar_estudiantes(con) -> list[dict]:
    return con.execute(
        "SELECT s.id_estudiante, s.documento, s.nombres, s.apellidos, COUNT(e.id_examen) AS examenes "
        "FROM estudiantes s LEFT JOIN examenes e ON e.id_estudiante = s.id_estudiante AND e.estado = 'FINALIZADO' "
        "GROUP BY s.id_estudiante ORDER BY s.apellidos, s.nombres").fetchall()


SQL_ALEATORIAS = """
    SELECT p.id_pregunta, p.id_componente, c.nombre_componente, p.id_nivel, n.nombre_nivel, p.enunciado
    FROM preguntas p
    JOIN componentes c      ON c.id_componente = p.id_componente
    JOIN nivel_dificultad n ON n.id_nivel      = p.id_nivel
    WHERE p.id_componente = %s AND p.activa
    ORDER BY random()
    LIMIT %s
"""


def _adjuntar_opciones(con, preguntas: list[dict]) -> None:
    ids = [p["id_pregunta"] for p in preguntas]
    filas = con.execute("SELECT id_opcion, id_pregunta, letra, texto, es_correcta FROM opciones_respuesta "
                        "WHERE id_pregunta = ANY(%s) ORDER BY id_pregunta, letra", (ids,)).fetchall()
    por_pregunta: dict[int, list[dict]] = {}
    for f in filas:
        por_pregunta.setdefault(f["id_pregunta"], []).append(f)
    for p in preguntas:
        ops = por_pregunta.get(p["id_pregunta"], [])
        if len(ops) != 4 or sum(o["es_correcta"] for o in ops) != 1:
            raise ErrorBancoPreguntas(f"La pregunta {p['id_pregunta']} no tiene 4 opciones con una sola correcta.")
        p["ids_opcion"] = {}
        for o in ops:
            p["opcion_" + o["letra"].lower()] = o["texto"]
            p["ids_opcion"][o["letra"]] = o["id_opcion"]
            if o["es_correcta"]:
                p["respuesta_correcta"] = o["letra"]


def seleccionar_preguntas(con, id_materia: int) -> list[dict]:
    seleccion: list[dict] = []
    comps = componentes(con, id_materia)
    if not comps:
        raise ErrorBancoPreguntas("La materia no tiene componentes configurados.")
    for comp in comps:
        n = comp["preguntas_por_examen"] or PREGUNTAS_POR_COMPONENTE
        filas = con.execute(SQL_ALEATORIAS, (comp["id_componente"], n)).fetchall()
        if len(filas) != n:
            raise ErrorBancoPreguntas(
                f"El componente '{comp['nombre_componente']}' solo tiene {len(filas)} preguntas activas (se requieren {n}).")
        seleccion.extend(filas)
    ids = [p["id_pregunta"] for p in seleccion]
    if len(ids) != len(set(ids)):
        raise ErrorBancoPreguntas("La selección contiene preguntas repetidas.")
    _adjuntar_opciones(con, seleccion)
    return seleccion


def crear_examen(con, id_estudiante: int, id_materia: int, preguntas: list[dict]) -> int:
    id_examen = con.execute(
        "INSERT INTO examenes (id_estudiante, id_materia, total_preguntas) VALUES (%s, %s, %s) RETURNING id_examen",
        (id_estudiante, id_materia, len(preguntas))).fetchone()["id_examen"]
    with con.cursor() as cur:
        cur.executemany("INSERT INTO detalle_examen (id_examen, id_pregunta, orden) VALUES (%s, %s, %s)",
                        [(id_examen, p["id_pregunta"], i) for i, p in enumerate(preguntas, start=1)])
    return id_examen


def guardar_calificacion(con, id_examen: int, resultado: dict, preguntas: list[dict], tiempo_segundos: int) -> None:
    fila = con.execute("SELECT estado FROM examenes WHERE id_examen = %s FOR UPDATE", (id_examen,)).fetchone()
    if not fila or fila["estado"] != "EN_CURSO":
        raise ValueError("El examen no existe o ya fue enviado.")
    ids_opcion = {p["id_pregunta"]: p["ids_opcion"] for p in preguntas}
    with con.cursor() as cur:
        cur.executemany(
            "UPDATE detalle_examen SET id_opcion_seleccionada = %s, es_correcta = %s "
            "WHERE id_examen = %s AND id_pregunta = %s",
            [(ids_opcion[d["id_pregunta"]].get(d["respuesta"]) if d["respuesta"] else None,
              d["correcta"], id_examen, d["id_pregunta"]) for d in resultado["detalle"]])
        cur.executemany(
            "INSERT INTO resultados_componente (id_examen, id_componente, aciertos, total_preguntas, porcentaje) "
            "VALUES (%s, %s, %s, %s, %s)",
            [(id_examen, c["id_componente"], c["aciertos"], c["total"], c["porcentaje"]) for c in resultado["componentes"]])
    con.execute("UPDATE examenes SET fecha_fin = now(), tiempo_segundos = %s, puntaje_total = %s, "
                "estado = 'FINALIZADO' WHERE id_examen = %s", (tiempo_segundos, resultado["puntaje_total"], id_examen))


def guardar_diagnostico(con, id_examen: int, diag: dict, resumen: dict) -> None:
    con.execute(
        """INSERT INTO diagnosticos_ia (id_examen, fortalezas, debilidades, plan_estudio, resumen_enviado,
                                        modelo_ia, tiempo_respuesta_s)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (id_examen) DO UPDATE SET
               fortalezas = EXCLUDED.fortalezas, debilidades = EXCLUDED.debilidades,
               plan_estudio = EXCLUDED.plan_estudio, resumen_enviado = EXCLUDED.resumen_enviado,
               modelo_ia = EXCLUDED.modelo_ia, tiempo_respuesta_s = EXCLUDED.tiempo_respuesta_s,
               fecha_generacion = now()""",
        (id_examen, diag["fortalezas"], diag["debilidades"], diag["plan_estudio"],
         json.dumps(resumen, ensure_ascii=False), diag["modelo"], diag.get("tiempo_s")))


def anular_examen(con, id_examen: int) -> None:
    con.execute("UPDATE examenes SET estado = 'ANULADO' WHERE id_examen = %s AND estado = 'EN_CURSO'", (id_examen,))


def historial(con, id_estudiante: int) -> list[dict]:
    return con.execute(
        f"SELECT id_examen, {_fecha('fecha_inicio')} AS fecha_inicio, tiempo_segundos, puntaje_total, total_preguntas, "
        "ROUND(puntaje_total * 100.0 / total_preguntas, 1)::float AS porcentaje "
        "FROM examenes WHERE id_estudiante = %s AND estado = 'FINALIZADO' ORDER BY examenes.fecha_inicio DESC, id_examen DESC",
        (id_estudiante,)).fetchall()


def examen(con, id_examen: int) -> dict | None:
    return con.execute(
        f"SELECT e.id_examen, e.id_estudiante, e.estado, e.puntaje_total, e.total_preguntas, e.tiempo_segundos, "
        f"{_fecha('e.fecha_inicio')} AS fecha_inicio, s.documento, s.nombres, s.apellidos, m.nombre_materia "
        "FROM examenes e JOIN estudiantes s ON s.id_estudiante = e.id_estudiante "
        "JOIN materias m ON m.id_materia = e.id_materia WHERE e.id_examen = %s", (id_examen,)).fetchone()


def resultados_componente(con, id_examen: int) -> list[dict]:
    return con.execute(
        "SELECT c.nombre_componente, r.aciertos, r.total_preguntas, r.porcentaje::float AS porcentaje "
        "FROM resultados_componente r JOIN componentes c ON c.id_componente = r.id_componente "
        "WHERE r.id_examen = %s ORDER BY c.id_componente", (id_examen,)).fetchall()


def diagnostico(con, id_examen: int) -> dict | None:
    return con.execute(
        f"SELECT fortalezas, debilidades, plan_estudio, resumen_enviado, modelo_ia, "
        f"tiempo_respuesta_s::float AS tiempo_respuesta_s, {_fecha('fecha_generacion')} AS fecha_generacion "
        "FROM diagnosticos_ia WHERE id_examen = %s", (id_examen,)).fetchone()


def detalle_respuestas(con, id_examen: int) -> list[dict]:
    return con.execute(
        "SELECT d.orden, c.nombre_componente, n.nombre_nivel, p.enunciado, "
        "sel.letra AS respuesta_estudiante, ok.letra AS respuesta_correcta, d.es_correcta "
        "FROM detalle_examen d "
        "JOIN preguntas p ON p.id_pregunta = d.id_pregunta "
        "JOIN componentes c ON c.id_componente = p.id_componente "
        "JOIN nivel_dificultad n ON n.id_nivel = p.id_nivel "
        "JOIN opciones_respuesta ok ON ok.id_pregunta = p.id_pregunta AND ok.es_correcta "
        "LEFT JOIN opciones_respuesta sel ON sel.id_opcion = d.id_opcion_seleccionada "
        "WHERE d.id_examen = %s ORDER BY d.orden", (id_examen,)).fetchall()


def promedios_globales(con) -> list[dict]:
    return con.execute(
        "SELECT c.nombre_componente, ROUND(AVG(r.porcentaje), 1)::float AS promedio, COUNT(*) AS examenes "
        "FROM resultados_componente r JOIN componentes c ON c.id_componente = r.id_componente "
        "GROUP BY c.id_componente, c.nombre_componente ORDER BY c.id_componente").fetchall()


def resumen_general(con) -> dict:
    return con.execute(
        "SELECT COUNT(*) AS examenes, COUNT(DISTINCT id_estudiante) AS estudiantes, "
        "ROUND(AVG(puntaje_total), 1)::float AS promedio, ROUND(AVG(tiempo_segundos) / 60.0, 1)::float AS minutos "
        "FROM examenes WHERE estado = 'FINALIZADO'").fetchone()


def banco_resumen(con) -> list[dict]:
    return con.execute(
        "SELECT nombre_materia, nombre_componente, nombre_nivel, total_preguntas AS total "
        "FROM vw_banco_por_componente ORDER BY nombre_componente, nombre_nivel").fetchall()


def preguntas_por_componente(con, id_componente: int) -> list[dict]:
    return con.execute(
        "SELECT p.id_pregunta, n.nombre_nivel AS nivel, p.enunciado, "
        "MAX(o.texto) FILTER (WHERE o.letra = 'A') AS \"A\", MAX(o.texto) FILTER (WHERE o.letra = 'B') AS \"B\", "
        "MAX(o.texto) FILTER (WHERE o.letra = 'C') AS \"C\", MAX(o.texto) FILTER (WHERE o.letra = 'D') AS \"D\", "
        "MAX(o.letra) FILTER (WHERE o.es_correcta) AS clave "
        "FROM preguntas p JOIN nivel_dificultad n ON n.id_nivel = p.id_nivel "
        "JOIN opciones_respuesta o ON o.id_pregunta = p.id_pregunta "
        "WHERE p.id_componente = %s AND p.activa "
        "GROUP BY p.id_pregunta, n.nombre_nivel ORDER BY p.id_pregunta", (id_componente,)).fetchall()


def agregar_pregunta(con, id_componente: int, id_nivel: int, enunciado: str, opciones: list[str], clave: str) -> int:
    opciones = [o.strip() for o in opciones]
    if not enunciado.strip():
        raise ValueError("El enunciado no puede estar vacío.")
    if len(opciones) != 4 or any(not o for o in opciones):
        raise ValueError("Se requieren exactamente 4 opciones no vacías.")
    if len(set(opciones)) != 4:
        raise ValueError("Las 4 opciones deben ser distintas.")
    if clave not in ("A", "B", "C", "D"):
        raise ValueError("La clave debe ser A, B, C o D.")
    id_p = con.execute("INSERT INTO preguntas (id_componente, id_nivel, enunciado) VALUES (%s, %s, %s) "
                       "RETURNING id_pregunta", (id_componente, id_nivel, enunciado.strip())).fetchone()["id_pregunta"]
    with con.cursor() as cur:
        cur.executemany("INSERT INTO opciones_respuesta (id_pregunta, letra, texto, es_correcta) VALUES (%s, %s, %s, %s)",
                        [(id_p, l, t, l == clave) for l, t in zip("ABCD", opciones)])
    return id_p
