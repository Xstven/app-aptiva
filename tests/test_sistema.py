import json
import os
import sys
import time
from pathlib import Path

import pytest

TEST_URL = os.getenv("TEST_DATABASE_URL", "")
if not TEST_URL:
    pytest.skip("Defina TEST_DATABASE_URL (base de datos de pruebas) para ejecutar las pruebas.",
                allow_module_level=True)

os.environ["DATABASE_URL"] = TEST_URL
os.environ["GEMINI_API_KEY"] = ""

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import psycopg

from scripts.init_db import crear_bd
from src import db, examen


@pytest.fixture()
def bd():
    db.cerrar_pool()
    crear_bd(TEST_URL, silencioso=True)
    yield
    db.cerrar_pool()


def test_tablas_y_llaves(bd):
    with db.conexion() as con:
        tablas = {r["table_name"] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")}
        assert tablas == {"materias", "componentes", "nivel_dificultad", "preguntas", "opciones_respuesta",
                          "estudiantes", "examenes", "detalle_examen", "resultados_componente", "diagnosticos_ia"}
        pks = con.execute("SELECT COUNT(*) AS n FROM information_schema.table_constraints "
                          "WHERE table_schema='public' AND constraint_type='PRIMARY KEY'").fetchone()["n"]
        fks = con.execute("SELECT COUNT(*) AS n FROM information_schema.table_constraints "
                          "WHERE table_schema='public' AND constraint_type='FOREIGN KEY'").fetchone()["n"]
        assert pks == 10 and fks == 12


def test_restricciones_rechazan_datos_invalidos(bd):
    casos = [
        "INSERT INTO preguntas (id_componente, id_nivel, enunciado) VALUES (99, 1, 'x')",
        "INSERT INTO opciones_respuesta (id_pregunta, letra, texto) VALUES (1, 'E', 'x')",
        "INSERT INTO opciones_respuesta (id_pregunta, letra, texto) VALUES (1, 'A', 'otra')",
        "UPDATE opciones_respuesta SET es_correcta = TRUE WHERE id_pregunta = 1",
        "INSERT INTO estudiantes (documento, nombres, apellidos) VALUES ('abc', 'X', 'Y')",
    ]
    for sql in casos:
        with pytest.raises(psycopg.errors.IntegrityError):
            with db.conexion() as con:
                con.execute(sql)


def test_opcion_debe_pertenecer_a_la_pregunta(bd):
    with db.conexion() as con:
        id_est = db.obtener_o_crear_estudiante(con, "1000000009", "Ana", "Ruiz")
        sel = db.seleccionar_preguntas(con, 1)
        id_ex = db.crear_examen(con, id_est, 1, sel)
    otra = sel[1]["ids_opcion"]["A"]
    with pytest.raises(psycopg.errors.IntegrityError):
        with db.conexion() as con:
            con.execute("UPDATE detalle_examen SET id_opcion_seleccionada = %s WHERE id_examen = %s AND id_pregunta = %s",
                        (otra, id_ex, sel[0]["id_pregunta"]))


def test_banco_150_preguntas_validas(bd):
    with db.conexion() as con:
        conteo = {r["id_componente"]: r["n"] for r in con.execute(
            "SELECT id_componente, COUNT(*) AS n FROM preguntas GROUP BY id_componente")}
        assert conteo == {1: 50, 2: 50, 3: 50}
        malas = con.execute(
            "SELECT p.id_pregunta FROM preguntas p JOIN opciones_respuesta o USING (id_pregunta) "
            "GROUP BY p.id_pregunta HAVING COUNT(*) <> 4 OR COUNT(*) FILTER (WHERE o.es_correcta) <> 1 "
            "OR COUNT(DISTINCT o.texto) <> 4").fetchall()
        assert malas == []


def test_seleccion_aleatoria(bd):
    selecciones = []
    with db.conexion() as con:
        for _ in range(20):
            sel = db.seleccionar_preguntas(con, 1)
            assert len(sel) == 30 and len({p["id_pregunta"] for p in sel}) == 30
            for comp in (1, 2, 3):
                assert sum(1 for p in sel if p["id_componente"] == comp) == 10
            assert all(p["respuesta_correcta"] in "ABCD" and p["opcion_d"] for p in sel)
            selecciones.append(tuple(sorted(p["id_pregunta"] for p in sel)))
    assert len(set(selecciones)) > 1, "La selección no es aleatoria"


def test_banco_insuficiente_lanza_error(bd):
    with db.conexion() as con:
        con.execute("UPDATE preguntas SET activa = FALSE WHERE id_componente = 2 AND id_pregunta % 10 <> 0")
    with db.conexion() as con:
        with pytest.raises(db.ErrorBancoPreguntas):
            db.seleccionar_preguntas(con, 1)


def test_calificacion(bd):
    with db.conexion() as con:
        sel = db.seleccionar_preguntas(con, 1)
    resp = {}
    for p in sel:
        if p["id_componente"] == 1:
            resp[p["id_pregunta"]] = p["respuesta_correcta"]
        elif p["id_componente"] == 2:
            resp[p["id_pregunta"]] = next(l for l in "ABCD" if l != p["respuesta_correcta"])
    r = examen.calificar(sel, resp)
    assert r["puntaje_total"] == 10
    assert [c["aciertos"] for c in r["componentes"]] == [10, 0, 0]
    assert [c["porcentaje"] for c in r["componentes"]] == [100.0, 0.0, 0.0]
    assert r["componentes"][2]["sin_responder"] == 10


def test_flujo_completo(bd):
    with db.conexion() as con:
        id_est = db.obtener_o_crear_estudiante(con, "1000000001", "Ana", "Pérez")
    ex = examen.iniciar_examen(id_est, 1)
    resp = {p["id_pregunta"]: (p["respuesta_correcta"] if i % 3 else None) for i, p in enumerate(ex["preguntas"])}
    t0 = time.perf_counter()
    salida = examen.finalizar_examen(ex["id_examen"], ex["preguntas"], resp, ex["inicio"] - 600, "Ana")
    assert time.perf_counter() - t0 < 5
    assert salida["resultado"]["puntaje_total"] == 20
    with db.conexion() as con:
        e = db.examen(con, ex["id_examen"])
        assert e["estado"] == "FINALIZADO" and e["puntaje_total"] == 20 and e["tiempo_segundos"] >= 600
        assert len(db.resultados_componente(con, ex["id_examen"])) == 3
        d = db.diagnostico(con, ex["id_examen"])
        assert d and d["resumen_enviado"]["puntaje_global"] == "20/30"
        det = db.detalle_respuestas(con, ex["id_examen"])
        assert sum(1 for x in det if x["respuesta_estudiante"] is None) == 10
        assert len(db.historial(con, id_est)) == 1


def test_doble_envio_rechazado(bd):
    with db.conexion() as con:
        id_est = db.obtener_o_crear_estudiante(con, "1000000002", "Luis", "Mora")
    ex = examen.iniciar_examen(id_est, 1)
    examen.finalizar_examen(ex["id_examen"], ex["preguntas"], {}, ex["inicio"], "Luis")
    with pytest.raises(ValueError):
        examen.finalizar_examen(ex["id_examen"], ex["preguntas"], {}, ex["inicio"], "Luis")


def test_agregar_pregunta_valida(bd):
    with db.conexion() as con:
        nid = db.agregar_pregunta(con, 1, 1, "¿Cuánto es 2 + 2?", ["3", "4", "5", "6"], "B")
        assert nid == 151
        ops = con.execute("SELECT letra, es_correcta FROM opciones_respuesta WHERE id_pregunta = %s ORDER BY letra",
                          (nid,)).fetchall()
        assert [o["es_correcta"] for o in ops] == [False, True, False, False]
    with pytest.raises(ValueError):
        with db.conexion() as con:
            db.agregar_pregunta(con, 1, 1, "¿2 + 3?", ["5", "5", "6", "7"], "A")
