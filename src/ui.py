from __future__ import annotations

import html

import streamlit as st

AZUL = "#3B5BFD"
AZUL_OSCURO = "#0B1B3F"
VERDE = "#10B981"
AMBAR = "#F59E0B"
ROJO = "#EF4444"
GRIS = "#64748B"

COLORES_COMPONENTE = {"Estadística": "#3B5BFD", "Geometría": "#10B981", "Cálculo y Álgebra": "#F59E0B"}
ICONOS_COMPONENTE = {"Estadística": "📊", "Geometría": "📐", "Cálculo y Álgebra": "∑"}


def color_componente(nombre: str) -> str:
    return COLORES_COMPONENTE.get(nombre, AZUL)


def nivel_desempeno(pct: float) -> tuple[str, str]:
    if pct >= 80:
        return "Superior", VERDE
    if pct >= 60:
        return "Alto", AZUL
    if pct >= 40:
        return "Básico", AMBAR
    return "Bajo", ROJO


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, textarea, select, label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
}
.stApp { background: #F4F6FB; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1200px; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {
    visibility: visible !important; display: flex !important; opacity: 1 !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {
    background: #0B1B3F !important; color: #fff !important; border-radius: 10px !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] * { color: #fff !important; fill: #fff !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {
    width: 42px !important; height: 42px !important; box-shadow: 0 6px 16px rgba(11,27,63,.3); }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1B3F 0%, #13265C 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E2E8F0; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 10px 14px; border-radius: 10px; width: 100%;
    transition: background .15s ease; cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.08); }
[data-testid="stSidebar"] .stRadio, [data-testid="stSidebar"] .stRadio > div,
[data-testid="stSidebar"] [role="radiogroup"] { width: 100%; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"],
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(59,91,253,.95); box-shadow: 0 6px 18px rgba(59,91,253,.35);
}
[data-testid="stSidebar"] [role="radiogroup"] label p { font-weight: 600; font-size: .95rem; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); color: #fff; border-radius: 10px;
}
[data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.16); border-color: rgba(255,255,255,.3); }

.brand { display:flex; align-items:center; gap:12px; margin: 4px 0 22px 0; }
.brand-logo { width:42px; height:42px; border-radius:12px; display:grid; place-items:center;
    background: linear-gradient(135deg,#3B5BFD,#8B5CF6); font-weight:800; font-size:1.2rem; color:#fff; }
.brand-name { font-weight:800; font-size:1.15rem; color:#fff; line-height:1.1; }
.brand-sub { font-size:.75rem; color:#94A3B8; }
.side-user { background: rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1);
    border-radius:14px; padding:12px 14px; margin: 6px 0 10px 0; }
.side-user .lbl { font-size:.72rem; color:#94A3B8; text-transform:uppercase; letter-spacing:.06em; }
.side-user .nom { font-weight:700; color:#fff; margin-top:2px; }
.side-status { font-size:.78rem; color:#CBD5E1; display:flex; align-items:center; gap:8px; margin:6px 0; }
.dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

.hero { background: radial-gradient(1200px 300px at 85% -40%, rgba(139,92,246,.55), transparent),
                    linear-gradient(120deg, #0B1B3F 0%, #1E3A8A 55%, #3B5BFD 100%);
    border-radius: 22px; padding: 34px 38px; color: #fff; margin-bottom: 26px;
    box-shadow: 0 18px 40px rgba(11,27,63,.25); position: relative; overflow: hidden; }
.hero h1 { color:#fff !important; font-size: 2.05rem; font-weight: 800; margin: 0 0 6px 0; line-height:1.15; }
.hero p { color: #C7D2FE; margin: 0; font-size: 1rem; }
.hero .eyebrow { text-transform: uppercase; letter-spacing: .12em; font-size: .74rem; color:#A5B4FC; font-weight:700; margin-bottom:10px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }
.chip { background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.2); color:#fff;
    padding: 6px 12px; border-radius: 999px; font-size: .8rem; font-weight: 600; }

.card { background:#fff; border-radius:18px; padding:22px; border:1px solid #E7EAF3;
    box-shadow: 0 4px 18px rgba(15,23,42,.05); }
.grid { display:grid; gap:16px; }
.grid-3 { grid-template-columns: repeat(3, minmax(0,1fr)); }
.grid-4 { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 900px) { .grid-3, .grid-4 { grid-template-columns: 1fr 1fr; } }

.step-num { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; font-weight:800;
    color:#fff; margin-bottom:14px; font-size:1rem; }
.step h4 { margin:0 0 6px 0; font-weight:700; color:#0F172A; font-size:1.02rem; }
.step p { margin:0; color:#64748B; font-size:.9rem; line-height:1.5; }

.kpi { position:relative; overflow:hidden; }
.kpi .lbl { color:#64748B; font-size:.8rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
.kpi .val { font-size:2rem; font-weight:800; color:#0F172A; margin-top:6px; line-height:1.1; }
.kpi .sub { color:#94A3B8; font-size:.82rem; margin-top:4px; }
.kpi .bar { position:absolute; left:0; top:0; bottom:0; width:5px; }
.kpi .ico { position:absolute; right:18px; top:18px; width:40px; height:40px; border-radius:12px;
    display:grid; place-items:center; font-size:1.15rem; }

.section-title { margin: 30px 0 14px 0; }
.section-title h3 { margin:0; font-weight:800; color:#0F172A; font-size:1.25rem; }
.section-title p { margin:4px 0 0 0; color:#64748B; font-size:.9rem; }

.comp-row { display:flex; align-items:center; gap:14px; padding:14px 0; border-bottom:1px solid #F1F5F9; }
.comp-row:last-child { border-bottom:none; }
.comp-ico { width:42px; height:42px; border-radius:12px; display:grid; place-items:center; font-size:1.1rem; flex:none; }
.comp-name { font-weight:700; color:#0F172A; }
.comp-meta { color:#64748B; font-size:.82rem; }
.track { flex:1; height:10px; background:#EEF2F7; border-radius:999px; overflow:hidden; min-width:120px; }
.fill { height:100%; border-radius:999px; }
.badge { padding:4px 10px; border-radius:999px; font-size:.75rem; font-weight:700; white-space:nowrap; }
.pct { font-weight:800; color:#0F172A; width:54px; text-align:right; }

.diag { border-radius:18px; padding:22px 22px 12px 22px; height:100%; border:1px solid; }
.diag h4 { margin:0 0 12px 0; font-weight:800; font-size:1.02rem; display:flex; gap:10px; align-items:center; }
.diag ul { margin:0; padding-left:18px; }
.diag li { margin-bottom:10px; line-height:1.55; font-size:.92rem; }
.diag-f { background:#ECFDF5; border-color:#A7F3D0; color:#065F46; }
.diag-d { background:#FEF2F2; border-color:#FECACA; color:#991B1B; }
.diag-p { background:#EEF2FF; border-color:#C7D2FE; color:#3730A3; }
.ai-tag { display:inline-flex; align-items:center; gap:8px; background:#fff; border:1px solid #E7EAF3;
    border-radius:999px; padding:6px 12px; font-size:.8rem; color:#475569; font-weight:600; }

.q-head { display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap; }
.q-num { width:34px; height:34px; border-radius:10px; display:grid; place-items:center; font-weight:800; color:#fff; }
.q-tag { font-size:.74rem; font-weight:700; padding:4px 10px; border-radius:999px; }
.q-text { font-size:1.02rem; color:#0F172A; font-weight:600; line-height:1.55; margin: 2px 0 6px 0; }
[class*="st-key-preg_"] { background:#fff; border:1px solid #E7EAF3 !important; border-radius:18px !important;
    padding: 18px 20px !important; box-shadow: 0 4px 14px rgba(15,23,42,.04); margin-bottom: 14px; }
[class*="st-key-preg_"] .stRadio, [class*="st-key-preg_"] .stRadio > div { width:100%; }
[class*="st-key-preg_"] [role="radiogroup"] { display:grid !important; grid-template-columns: 1fr 1fr; gap:10px; width:100%; }
[class*="st-key-preg_"] [role="radiogroup"] label {
    border:1.5px solid #E2E8F0; border-radius:12px; padding:12px 14px; margin:0; width:100%; max-width:none;
    transition: all .12s ease; background:#FAFBFF; }
[class*="st-key-preg_"] [role="radiogroup"] label:hover { border-color:#A5B4FC; background:#F5F7FF; }
[class*="st-key-preg_"] [role="radiogroup"] label[data-selected="true"],
[class*="st-key-preg_"] [role="radiogroup"] label:has(input:checked) {
    border-color:#3B5BFD; background:#EEF2FF; box-shadow: 0 0 0 3px rgba(59,91,253,.12); }
[class*="st-key-preg_"] [role="radiogroup"] label p { font-weight:600; color:#1E293B; }

[data-testid="stForm"] { background:#fff; border:1px solid #E7EAF3; border-radius:18px; padding: 22px 24px;
    box-shadow: 0 4px 18px rgba(15,23,42,.05); }
.stTextInput input, .stNumberInput input, .stTextArea textarea, [data-baseweb="select"] > div {
    border-radius: 12px !important; }
.stButton button, [data-testid="stFormSubmitButton"] button { border-radius: 12px; font-weight: 700; padding: .6rem 1.2rem; }
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"], .stButton button[kind="primary"] {
    background: linear-gradient(120deg, #3B5BFD, #6366F1); border: none; box-shadow: 0 8px 20px rgba(59,91,253,.3); }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background:#fff; padding:6px; border-radius:14px; border:1px solid #E7EAF3; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; font-weight:700; }
.stTabs [aria-selected="true"] { background:#EEF2FF; color:#3B5BFD !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
[data-testid="stPlotlyChart"] { background:#fff; border:1px solid #E7EAF3; border-radius:18px; padding:8px; overflow:hidden;
    box-shadow: 0 4px 18px rgba(15,23,42,.05); }
[data-testid="stExpander"] { background:#fff; border-radius:14px; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _h(texto) -> str:
    return html.escape(str(texto))


def hero(eyebrow: str, titulo: str, subtitulo: str, chips: list[str] | None = None) -> None:
    chips_html = "".join(f'<span class="chip">{_h(c)}</span>' for c in (chips or []))
    st.markdown(f"""<div class="hero"><div class="eyebrow">{_h(eyebrow)}</div><h1>{_h(titulo)}</h1>
        <p>{_h(subtitulo)}</p>{f'<div class="chips">{chips_html}</div>' if chips else ''}</div>""",
                unsafe_allow_html=True)


def titulo_seccion(titulo: str, subtitulo: str = "") -> None:
    st.markdown(f'<div class="section-title"><h3>{_h(titulo)}</h3>'
                f'{f"<p>{_h(subtitulo)}</p>" if subtitulo else ""}</div>', unsafe_allow_html=True)


def pasos(items: list[tuple[str, str, str]]) -> None:
    tarjetas = "".join(
        f'<div class="card step"><div class="step-num" style="background:{c}">{i}</div>'
        f'<h4>{_h(t)}</h4><p>{_h(d)}</p></div>' for i, (t, d, c) in enumerate(items, start=1))
    st.markdown(f'<div class="grid grid-3">{tarjetas}</div>', unsafe_allow_html=True)


def kpis(items: list[tuple[str, str, str, str, str]]) -> None:
    tarjetas = "".join(
        f'<div class="card kpi"><div class="bar" style="background:{c}"></div>'
        f'<div class="ico" style="background:{c}1A;color:{c}">{ico}</div>'
        f'<div class="lbl">{_h(lbl)}</div><div class="val">{_h(val)}</div><div class="sub">{_h(sub)}</div></div>'
        for ico, lbl, val, sub, c in items)
    st.markdown(f'<div class="grid grid-4">{tarjetas}</div>', unsafe_allow_html=True)


def barras_componentes(resultados: list[dict]) -> None:
    filas = ""
    for r in resultados:
        nombre, pct = r["nombre_componente"], float(r["porcentaje"])
        col = color_componente(nombre)
        etiqueta, col_niv = nivel_desempeno(pct)
        filas += (f'<div class="comp-row"><div class="comp-ico" style="background:{col}1A;color:{col}">'
                  f'{ICONOS_COMPONENTE.get(nombre, "•")}</div>'
                  f'<div style="width:190px"><div class="comp-name">{_h(nombre)}</div>'
                  f'<div class="comp-meta">{r["aciertos"]} de {r["total_preguntas"]} correctas</div></div>'
                  f'<div class="track"><div class="fill" style="width:{pct}%;background:{col}"></div></div>'
                  f'<div class="pct">{pct:.0f}%</div>'
                  f'<span class="badge" style="background:{col_niv}1A;color:{col_niv}">{etiqueta}</span></div>')
    st.markdown(f'<div class="card" style="padding:8px 22px">{filas}</div>', unsafe_allow_html=True)


def _lista(texto: str) -> str:
    items = [l.strip().lstrip("-•* ").strip() for l in (texto or "").splitlines() if l.strip()]
    return "<ul>" + "".join(f"<li>{_h(i)}</li>" for i in items) + "</ul>"


def tarjetas_diagnostico(diag: dict) -> None:
    st.markdown(f"""<div class="grid grid-3">
        <div class="diag diag-f"><h4>💪 Fortalezas</h4>{_lista(diag["fortalezas"])}</div>
        <div class="diag diag-d"><h4>⚠️ Debilidades detectadas</h4>{_lista(diag["debilidades"])}</div>
        <div class="diag diag-p"><h4>📚 Plan de estudio</h4>{_lista(diag["plan_estudio"])}</div>
    </div>""", unsafe_allow_html=True)


def etiqueta_ia(diag: dict) -> None:
    es_gemini = diag["modelo_ia"] != "local-respaldo"
    color = VERDE if es_gemini else AMBAR
    origen = f"Gemini AI · {diag['modelo_ia']}" if es_gemini else "Motor local de respaldo"
    t = diag.get("tiempo_respuesta_s")
    st.markdown(f'<span class="ai-tag"><span class="dot" style="background:{color}"></span>{_h(origen)}'
                f'{f" · {t:.2f} s" if t is not None else ""} · {_h(diag["fecha_generacion"])}</span>',
                unsafe_allow_html=True)


def cabecera_pregunta(numero: int, p: dict) -> None:
    col = color_componente(p["nombre_componente"])
    nivel_col = {"Básico": VERDE, "Intermedio": AMBAR, "Avanzado": ROJO}.get(p["nombre_nivel"], GRIS)
    st.markdown(f"""<div class="q-head"><div class="q-num" style="background:{col}">{numero}</div>
        <span class="q-tag" style="background:{col}1A;color:{col}">{_h(p["nombre_componente"])}</span>
        <span class="q-tag" style="background:{nivel_col}1A;color:{nivel_col}">{_h(p["nombre_nivel"])}</span></div>
        <div class="q-text">{_h(p["enunciado"])}</div>""", unsafe_allow_html=True)


def marca_sidebar() -> None:
    st.markdown("""<div class="brand"><div class="brand-logo">E</div><div>
        <div class="brand-name">EvalIA</div><div class="brand-sub">Uniagustiniana · Ciencias Básicas</div></div></div>""",
                unsafe_allow_html=True)


def usuario_sidebar(rol: str, nombre: str, detalle: str) -> None:
    st.markdown(f'<div class="side-user"><div class="lbl">{_h(rol)}</div><div class="nom">{_h(nombre)}</div>'
                f'<div style="font-size:.78rem;color:#94A3B8">{_h(detalle)}</div></div>',
                unsafe_allow_html=True)


def estado_sidebar(texto: str, ok: bool) -> None:
    st.markdown(f'<div class="side-status"><span class="dot" style="background:{VERDE if ok else AMBAR}"></span>'
                f'{_h(texto)}</div>', unsafe_allow_html=True)
