import sys
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.config import DATABASE_URL

SCRIPTS = ["00_reiniciar.sql", "01_schema.sql", "02_insert_catalogos.sql", "03_insert_preguntas.sql"]


def crear_bd(url: str = DATABASE_URL, silencioso: bool = False) -> None:
    with psycopg.connect(url) as con:
        for nombre in SCRIPTS:
            con.execute((RAIZ / "database" / nombre).read_text(encoding="utf-8"))
            if not silencioso:
                print(f"  [OK] {nombre}")
    if not silencioso:
        verificar(url)


def verificar(url: str = DATABASE_URL) -> bool:
    ok = True
    with psycopg.connect(url) as con:
        print("\nVerificación:")
        tablas = [r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' "
            "AND table_type = 'BASE TABLE' ORDER BY table_name")]
        print(f"  Tablas ({len(tablas)}):", ", ".join(tablas))
        for comp, total in con.execute(
                "SELECT c.nombre_componente, COUNT(p.id_pregunta) FROM componentes c "
                "LEFT JOIN preguntas p ON p.id_componente = c.id_componente "
                "GROUP BY c.id_componente, c.nombre_componente ORDER BY c.id_componente"):
            estado = "OK" if total >= 50 else "FALTAN"
            ok &= total >= 50
            print(f"  {comp:<20} {total:>3} preguntas  [{estado}]")
        malas = con.execute(
            "SELECT COUNT(*) FROM (SELECT p.id_pregunta FROM preguntas p "
            "LEFT JOIN opciones_respuesta o ON o.id_pregunta = p.id_pregunta GROUP BY p.id_pregunta "
            "HAVING COUNT(o.id_opcion) <> 4 OR COUNT(*) FILTER (WHERE o.es_correcta) <> 1) x").fetchone()[0]
        ok &= malas == 0
        print("  Preguntas con 4 opciones y 1 correcta:", "OK" if malas == 0 else f"{malas} con errores")
    return ok


if __name__ == "__main__":
    if not DATABASE_URL:
        sys.exit("Falta DATABASE_URL en el archivo .env (cadena de conexión de Neon).")
    if "--verificar" in sys.argv:
        sys.exit(0 if verificar() else 1)
    destino = DATABASE_URL.split("@")[-1].split("/")[0]
    print(f"Creando la base de datos en {destino}")
    crear_bd()
