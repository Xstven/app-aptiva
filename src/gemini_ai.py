from __future__ import annotations

import json
import re
import time

from pydantic import BaseModel

from .config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODELOS_RESPALDO, GEMINI_TIMEOUT_S


class DiagnosticoIA(BaseModel):
    fortalezas: list[str]
    debilidades: list[str]
    plan_estudio: list[str]

PROMPT = """Eres un docente experto en evaluación de Matemáticas de educación superior en Colombia.
Analiza el siguiente resumen del desempeño de un estudiante en una prueba diagnóstica de 30 preguntas
(10 por componente: Estadística, Geometría, Cálculo y Álgebra) y devuelve ÚNICAMENTE un objeto JSON
con esta estructura exacta:

{{
  "fortalezas": ["...", "..."],
  "debilidades": ["...", "..."],
  "plan_estudio": ["Semana 1: ...", "Semana 2: ...", "Semana 3: ...", "Semana 4: ..."]
}}

Reglas:
- Escribe en español, en segunda persona (tú), con un tono motivador y concreto.
- Basa cada afirmación en los porcentajes, los aciertos por nivel de dificultad y el tiempo empleado.
- Considera fortaleza un componente >= 70 % y debilidad uno < 60 %.
- El plan de estudio debe priorizar los componentes más débiles y proponer temas y actividades específicas.
- Entre 2 y 4 elementos por lista; cada elemento de máximo 40 palabras.

Resumen del desempeño:
{resumen}
"""


def _lista_a_texto(valor) -> str:
    if isinstance(valor, list):
        return "\n".join(f"- {str(v).strip()}" for v in valor if str(v).strip())
    return str(valor).strip()


def _parsear(texto: str) -> dict:
    texto = texto.strip()
    m = re.search(r"\{.*\}", texto, re.S)
    data = json.loads(m.group(0) if m else texto)
    faltan = {"fortalezas", "debilidades", "plan_estudio"} - set(data)
    if faltan:
        raise ValueError(f"Respuesta de la IA incompleta, faltan: {faltan}")
    return {k: _lista_a_texto(data[k]) for k in ("fortalezas", "debilidades", "plan_estudio")}


def _modelos_flash_disponibles(cliente) -> list[str]:
    try:
        nombres = []
        for m in cliente.models.list():
            nombre = (m.name or "").removeprefix("models/")
            acciones = getattr(m, "supported_actions", None) or []
            excluir = ("image", "tts", "audio", "live", "embedding", "thinking", "preview", "exp")
            if "flash" in nombre and "generateContent" in acciones and not any(x in nombre for x in excluir):
                nombres.append(nombre)
        return sorted(set(nombres), reverse=True)
    except Exception:
        return []


def _es(texto: str, *claves: str) -> bool:
    return any(c in texto for c in claves)


def consultar_gemini(resumen: dict) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("No se configuró GEMINI_API_KEY en el archivo .env")
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=GEMINI_API_KEY,
                           http_options=types.HttpOptions(timeout=int(GEMINI_TIMEOUT_S * 1000)))
    prompt = PROMPT.format(resumen=json.dumps(resumen, ensure_ascii=False, indent=2))
    con_esquema = types.GenerateContentConfig(response_mime_type="application/json",
                                              response_schema=DiagnosticoIA, temperature=0.4)
    solo_json = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4)

    errores: list[str] = []
    probados: set[str] = set()

    def intentar(modelo: str):
        probados.add(modelo)
        config = con_esquema
        for intento in range(3):
            try:
                t0 = time.perf_counter()
                resp = cliente.models.generate_content(model=modelo, contents=prompt, config=config)
                if getattr(resp, "parsed", None) is not None and isinstance(resp.parsed, DiagnosticoIA):
                    d = resp.parsed
                    datos = {k: _lista_a_texto(getattr(d, k)) for k in ("fortalezas", "debilidades", "plan_estudio")}
                else:
                    datos = _parsear(resp.text or "")
                datos.update(modelo=modelo, tiempo_s=round(time.perf_counter() - t0, 2), origen="gemini")
                return datos
            except Exception as e:
                texto = str(e)
                errores.append(f"[{modelo}] {texto[:160]}")
                if _es(texto, "API_KEY_INVALID", "API key not valid", "PERMISSION_DENIED"):
                    raise RuntimeError("La API key de Gemini no es válida: " + texto[:200])
                if _es(texto, "503", "UNAVAILABLE", "overloaded") and intento < 2:
                    time.sleep(2 * (intento + 1))
                    continue
                if _es(texto, "INVALID_ARGUMENT", "response_schema", "schema") and config is con_esquema:
                    config = solo_json
                    continue
                return None
        return None

    candidatos = [GEMINI_MODEL] + [m for m in GEMINI_MODELOS_RESPALDO if m]
    for modelo in candidatos:
        if modelo not in probados and (datos := intentar(modelo)):
            return datos
    for modelo in _modelos_flash_disponibles(cliente)[:4]:
        if modelo not in probados and (datos := intentar(modelo)):
            return datos
    raise RuntimeError("Gemini no respondió. " + " | ".join(errores))


def diagnostico_local(resumen: dict) -> dict:
    t0 = time.perf_counter()
    comps = sorted(resumen["componentes"], key=lambda c: c["porcentaje"], reverse=True)
    temas = {
        "Estadística": "medidas de tendencia central y dispersión, probabilidad clásica y técnicas de conteo",
        "Geometría": "áreas, volúmenes, teorema de Pitágoras, ángulos y geometría analítica (distancia, pendiente)",
        "Cálculo y Álgebra": "ecuaciones e inecuaciones, funciones, límites, derivadas e integrales básicas",
    }
    fuertes = [c for c in comps if c["porcentaje"] >= 70]
    debiles = [c for c in comps if c["porcentaje"] < 60]
    fort = [f"Buen dominio de {c['componente']} ({c['aciertos']}, {c['porcentaje']} %)." for c in fuertes] or \
           [f"Tu mejor resultado fue en {comps[0]['componente']} ({comps[0]['porcentaje']} %); es una base para seguir avanzando."]
    deb = [f"{c['componente']} requiere refuerzo ({c['aciertos']}, {c['porcentaje']} %): repasa {temas.get(c['componente'], 'los temas del componente')}."
           for c in reversed(debiles)] or ["No se detectan debilidades críticas; mantén la práctica para consolidar."]
    sin_resp = sum(c["sin_responder"] for c in comps)
    if sin_resp:
        deb.append(f"Dejaste {sin_resp} pregunta(s) sin responder; trabaja la gestión del tiempo durante la prueba.")
    orden = list(reversed(comps))
    plan = [f"Semana {i + 1}: estudia {c['componente']} — {temas.get(c['componente'], 'temas del componente')}; "
            f"resuelve 15 ejercicios y corrige tus errores." for i, c in enumerate(orden)]
    plan.append(f"Semana {len(orden) + 1}: presenta de nuevo la prueba diagnóstica y compara tu evolución en el dashboard.")
    return {"fortalezas": _lista_a_texto(fort), "debilidades": _lista_a_texto(deb), "plan_estudio": _lista_a_texto(plan),
            "modelo": "local-respaldo", "tiempo_s": round(time.perf_counter() - t0, 3), "origen": "local"}


def generar_diagnostico(resumen: dict, usar_ia: bool = True) -> dict:
    if usar_ia:
        try:
            return consultar_gemini(resumen)
        except Exception as e:
            diag = diagnostico_local(resumen)
            diag["aviso"] = str(e)[:1500]
            return diag
    return diagnostico_local(resumen)
