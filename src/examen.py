from __future__ import annotations

import time
from collections import OrderedDict

from . import db
from .gemini_ai import generar_diagnostico


def iniciar_examen(id_estudiante: int, id_materia: int) -> dict:
    with db.conexion() as con:
        preguntas = db.seleccionar_preguntas(con, id_materia)
        id_examen = db.crear_examen(con, id_estudiante, id_materia, preguntas)
    return {"id_examen": id_examen, "preguntas": preguntas, "inicio": time.time()}


def calificar(preguntas: list[dict], respuestas: dict[int, str | None]) -> dict:
    por_comp: "OrderedDict[int, dict]" = OrderedDict()
    detalle = []
    for p in preguntas:
        r = respuestas.get(p["id_pregunta"])
        ok = r is not None and r == p["respuesta_correcta"]
        detalle.append({"id_pregunta": p["id_pregunta"], "respuesta": r, "correcta": ok,
                        "id_componente": p["id_componente"], "nivel": p["nombre_nivel"]})
        c = por_comp.setdefault(p["id_componente"], {"id_componente": p["id_componente"],
                                                     "nombre": p["nombre_componente"], "aciertos": 0, "total": 0,
                                                     "sin_responder": 0, "por_nivel": {}})
        c["total"] += 1
        c["aciertos"] += int(ok)
        c["sin_responder"] += int(r is None)
        nv = c["por_nivel"].setdefault(p["nombre_nivel"], [0, 0])
        nv[0] += int(ok)
        nv[1] += 1
    for c in por_comp.values():
        c["porcentaje"] = round(c["aciertos"] * 100.0 / c["total"], 1)
    total = sum(c["aciertos"] for c in por_comp.values())
    n = len(preguntas)
    return {"puntaje_total": total, "total_preguntas": n,
            "porcentaje_global": round(total * 100.0 / n, 1) if n else 0.0,
            "componentes": list(por_comp.values()), "detalle": detalle}


def consolidar_para_ia(resultado: dict, tiempo_segundos: int, estudiante: str = "") -> dict:
    return {
        "materia": "Matemáticas",
        "estudiante": estudiante.split(" ")[0] if estudiante else "Estudiante",
        "puntaje_global": f"{resultado['puntaje_total']}/{resultado['total_preguntas']}",
        "porcentaje_global": resultado["porcentaje_global"],
        "tiempo_empleado_min": round(tiempo_segundos / 60, 1),
        "tiempo_promedio_por_pregunta_s": round(tiempo_segundos / max(resultado["total_preguntas"], 1), 1),
        "componentes": [
            {"componente": c["nombre"], "aciertos": f"{c['aciertos']}/{c['total']}", "porcentaje": c["porcentaje"],
             "sin_responder": c["sin_responder"],
             "aciertos_por_nivel": {k: f"{v[0]}/{v[1]}" for k, v in c["por_nivel"].items()}}
            for c in resultado["componentes"]
        ],
    }


def finalizar_examen(id_examen: int, preguntas: list[dict], respuestas: dict[int, str | None],
                     inicio: float, estudiante: str = "", usar_ia: bool = True) -> dict:
    tiempo = max(int(time.time() - inicio), 0)
    resultado = calificar(preguntas, respuestas)
    with db.conexion() as con:
        db.guardar_calificacion(con, id_examen, resultado, preguntas, tiempo)
    resumen = consolidar_para_ia(resultado, tiempo, estudiante)
    diag = generar_diagnostico(resumen, usar_ia=usar_ia)
    with db.conexion() as con:
        db.guardar_diagnostico(con, id_examen, diag, resumen)
    return {"resultado": resultado, "diagnostico": diag, "tiempo": tiempo, "resumen": resumen}
