import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import db
from src.examen import finalizar_examen, iniciar_examen

ESTUDIANTES = [
    ("1001001001", "Laura", "Gómez Ríos", {1: 0.8, 2: 0.6, 3: 0.4}),
    ("1001001002", "Andrés", "Martínez Cruz", {1: 0.5, 2: 0.9, 3: 0.7}),
    ("1001001003", "Valentina", "Rojas Díaz", {1: 0.7, 2: 0.4, 3: 0.3}),
    ("1001001004", "Santiago", "López Peña", {1: 0.9, 2: 0.8, 3: 0.85}),
    ("1001001005", "Camila", "Herrera Soto", {1: 0.4, 2: 0.5, 3: 0.6}),
]


def main(usar_ia: bool = False):
    rng = random.Random(7)
    for doc, nom, ape, prob in ESTUDIANTES:
        with db.conexion() as con:
            id_est = db.obtener_o_crear_estudiante(con, doc, nom, ape, programa="Tecnología en Desarrollo de Software", semestre=5)
        intentos = 2 if doc.endswith(("1", "3")) else 1
        for k in range(intentos):
            ex = iniciar_examen(id_est, 1)
            mejora = 0.15 * k
            resp = {}
            for p in ex["preguntas"]:
                if rng.random() < min(prob[p["id_componente"]] + mejora, 1):
                    resp[p["id_pregunta"]] = p["respuesta_correcta"]
                else:
                    resp[p["id_pregunta"]] = rng.choice([l for l in "ABCD" if l != p["respuesta_correcta"]])
            out = finalizar_examen(ex["id_examen"], ex["preguntas"], resp, time.time() - rng.randint(900, 2400),
                                   nom, usar_ia=usar_ia)
            print(f"{nom:<10} examen {ex['id_examen']:>2}: {out['resultado']['puntaje_total']}/30")


if __name__ == "__main__":
    main(usar_ia="--ia" in sys.argv)
