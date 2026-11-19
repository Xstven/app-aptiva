import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ImportError:
    pass


def _leer(nombre: str, defecto: str = "") -> str:
    valor = os.getenv(nombre)
    if valor:
        return valor.strip()
    try:
        import streamlit as st
        if nombre in st.secrets:
            return str(st.secrets[nombre]).strip()
    except Exception:
        pass
    return defecto


DATABASE_URL = _leer("DATABASE_URL")

GEMINI_API_KEY = _leer("GEMINI_API_KEY")
GEMINI_MODEL = _leer("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_MODELOS_RESPALDO = [m.strip() for m in _leer("GEMINI_MODELOS_RESPALDO", "").split(",") if m.strip()]
GEMINI_TIMEOUT_S = float(_leer("GEMINI_TIMEOUT_S", "30"))

DOCENTE_PASSWORD = _leer("DOCENTE_PASSWORD")

ZONA_HORARIA = "America/Bogota"
ID_MATERIA_MATEMATICAS = 1
PREGUNTAS_POR_COMPONENTE = 10
LETRAS = ("A", "B", "C", "D")
