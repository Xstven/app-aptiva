from __future__ import annotations

import hmac
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import db, ui
from src.config import DATABASE_URL, DOCENTE_PASSWORD, GEMINI_API_KEY, GEMINI_MODEL, ID_MATERIA_MATEMATICAS
from src.examen import finalizar_examen, iniciar_examen

st.set_page_config(page_title="EvalIA · Evaluación Diagnóstica con IA", page_icon="📐", layout="wide", initial_sidebar_state="expanded")
ui.aplicar_estilos()

FUENTE = dict(family="Plus Jakarta Sans, sans-serif", color="#334155")


def bd_lista_cache() -> bool:
    if not st.session_state.get("bd_ok"):
        with st.spinner("Conectando con la base de datos…"):
            st.session_state.bd_ok = db.bd_lista()
    return st.session_state.bd_ok


def init_estado():
    for k, v in {"rol": None, "estudiante": None, "examen": None, "ultimo_examen": None, "pagina": "Inicio"}.items():
        st.session_state.setdefault(k, v)


def ir(pagina: str):
    st.session_state.pagina = pagina
    st.rerun()


PAGINAS_POR_ROL = {
    None: ["Inicio"],
    "estudiante": ["Inicio", "Presentar prueba", "Dashboard"],
    "docente": ["Inicio", "Dashboard", "Banco de preguntas"],
}


def cambiar_pagina(clave_menu: str):
    st.session_state.pagina = st.session_state[clave_menu]


def cerrar_sesion():
    for k in ("rol", "estudiante", "examen", "ultimo_examen"):
        st.session_state[k] = None
    ir("Inicio")


def acceso_denegado(texto: str):
    ui.hero("Acceso restringido", "No tienes permiso para ver esta página", texto)
    if st.button("Ir a Inicio", type="primary"):
        ir("Inicio")


def fmt_tiempo(seg: int | None) -> str:
    if seg is None:
        return "—"
    return f"{seg // 60}:{seg % 60:02d} min"


def estilo_figura(fig: go.Figure, titulo: str, alto: int = 360) -> go.Figure:
    fig.update_layout(title=dict(text=f"<b>{titulo}</b>", font=dict(size=15, color="#0F172A"), x=0.02),
                      font=FUENTE, height=alto, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=56, b=20, l=20, r=20))
    return fig


def grafico_gauge(pct: float) -> go.Figure:
    _, color = ui.nivel_desempeno(pct)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=pct, number=dict(suffix="%", font=dict(size=44, color="#0F172A", family="Plus Jakarta Sans, sans-serif")),
        gauge=dict(axis=dict(range=[0, 100], tickvals=[0, 40, 60, 80, 100], ticksuffix="%", tickfont=dict(size=10, color="#94A3B8")), bar=dict(color=color, thickness=0.75),
                   bgcolor="#EEF2F7", borderwidth=0,
                   steps=[dict(range=[0, 40], color="#FEE2E2"), dict(range=[40, 60], color="#FEF3C7"),
                          dict(range=[60, 80], color="#DBEAFE"), dict(range=[80, 100], color="#D1FAE5")],
                   threshold=dict(line=dict(color="#0F172A", width=3), thickness=0.8, value=60))))
    return estilo_figura(fig, "Resultado global", 300)


def grafico_barras(resultados: list[dict]) -> go.Figure:
    nombres = [r["nombre_componente"] for r in resultados]
    fig = go.Figure(go.Bar(
        x=nombres, y=[r["porcentaje"] for r in resultados], width=0.55,
        marker=dict(color=[ui.color_componente(n) for n in nombres], cornerradius=10),
        text=[f"<b>{r['porcentaje']:.0f}%</b>" for r in resultados], textposition="outside",
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.add_hline(y=60, line_dash="dot", line_color="#94A3B8", annotation_text="Meta 60 %",
                  annotation_font_color="#64748B")
    fig.update_yaxes(range=[0, 112], gridcolor="#EEF2F7", ticksuffix="%", zeroline=False)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(showlegend=False)
    return estilo_figura(fig, "Acierto por componente")


def grafico_radar(resultados: list[dict], promedio: list[dict] | None = None) -> go.Figure:
    cats = [r["nombre_componente"] for r in resultados]
    fig = go.Figure()
    if promedio:
        mp = {p["nombre_componente"]: p["promedio"] for p in promedio}
        vals = [mp.get(c, 0) for c in cats]
        fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=cats + [cats[0]], name="Promedio general",
                                      line=dict(color="#94A3B8", dash="dash", width=2)))
    fig.add_trace(go.Scatterpolar(r=[r["porcentaje"] for r in resultados] + [resultados[0]["porcentaje"]],
                                  theta=cats + [cats[0]], fill="toself", name="Estudiante",
                                  line=dict(color=ui.AZUL, width=3), fillcolor="rgba(59,91,253,.22)"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], ticksuffix="%", gridcolor="#E2E8F0", tickfont=dict(size=10)),
                                 angularaxis=dict(gridcolor="#E2E8F0")),
                      legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"))
    return estilo_figura(fig, "Perfil de competencias")


def pagina_inicio():
    ui.hero("Uniagustiniana · Departamento de Ciencias Básicas",
            "Evaluación diagnóstica de Matemáticas con Inteligencia Artificial",
            "Presenta la prueba, conoce tu nivel en cada componente y recibe un plan de estudio personalizado.",
            ["30 preguntas", "3 componentes", "Calificación inmediata", "Diagnóstico con Gemini AI"])
    ui.pasos([
        ("Selección aleatoria", "10 preguntas de Estadística, 10 de Geometría y 10 de Cálculo y Álgebra, distintas en cada intento.", ui.AZUL),
        ("Calificación automática", "Puntaje global sobre 30 y porcentaje de acierto en cada componente.", ui.VERDE),
        ("Diagnóstico con IA", "Gemini analiza tu desempeño y te entrega fortalezas, debilidades y un plan de 4 semanas.", "#8B5CF6"),
    ])
    if st.session_state.rol:
        quien = "docente" if st.session_state.rol == "docente" else st.session_state.estudiante["nombres"].split()[0].title()
        ui.titulo_seccion(f"Sesión iniciada como {quien}", "Usa el menú de la izquierda para continuar.")
        if st.button("Cerrar sesión"):
            cerrar_sesion()
        return

    ui.titulo_seccion("Ingresar", "Elige cómo vas a entrar al sistema.")
    tab_e, tab_d = st.tabs(["🎓  Soy estudiante", "👩‍🏫  Soy docente"])
    with tab_e:
        with st.form("form_registro"):
            a, b = st.columns(2)
            documento = a.text_input("Documento de identidad *", max_chars=20, placeholder="Solo números")
            correo = b.text_input("Correo institucional", placeholder="nombre@uniagustiniana.edu.co")
            nombres = a.text_input("Nombres *", max_chars=80)
            apellidos = b.text_input("Apellidos *", max_chars=80)
            programa = a.text_input("Programa", value="Tecnología en Desarrollo de Software")
            semestre = b.number_input("Semestre", min_value=1, max_value=12, value=5)
            enviar = st.form_submit_button("Continuar a la prueba  →", type="primary", width="stretch")
        if enviar:
            if not (documento.strip() and nombres.strip() and apellidos.strip()):
                st.error("Documento, nombres y apellidos son obligatorios.")
                return
            if not documento.strip().isdigit() or len(documento.strip()) < 5:
                st.error("El documento debe tener solo números (mínimo 5 dígitos).")
                return
            try:
                with db.conexion() as con:
                    db.obtener_o_crear_estudiante(con, documento, nombres, apellidos, correo or None, programa, int(semestre))
                    st.session_state.estudiante = db.buscar_estudiante(con, documento)
            except Exception as e:
                st.error(f"No fue posible registrar al estudiante: {e}")
                return
            st.session_state.rol = "estudiante"
            ir("Presentar prueba")
    with tab_d:
        with st.form("form_docente"):
            st.caption("Acceso para el docente: banco de preguntas y resultados de todos los estudiantes.")
            clave = st.text_input("Contraseña de docente", type="password")
            entrar = st.form_submit_button("Ingresar como docente", type="primary", width="stretch")
        if entrar:
            if not DOCENTE_PASSWORD:
                st.error("El acceso de docente no está configurado (falta DOCENTE_PASSWORD en .env o en Secrets).")
            elif hmac.compare_digest(clave.encode(), DOCENTE_PASSWORD.encode()):
                st.session_state.rol = "docente"
                st.session_state.estudiante = None
                ir("Dashboard")
            else:
                st.error("Contraseña incorrecta.")


def pagina_prueba():
    if st.session_state.rol != "estudiante":
        acceso_denegado("Solo los estudiantes pueden presentar la prueba.")
        return
    est = st.session_state.estudiante
    if not est:
        ui.hero("Prueba diagnóstica", "Primero identifícate", "Ingresa tus datos en la página de Inicio para comenzar.")
        if st.button("Ir a Inicio", type="primary"):
            ir("Inicio")
        return

    ex = st.session_state.examen
    if ex is None:
        ui.hero("Prueba diagnóstica de Matemáticas", f"¡Hola, {est['nombres'].split()[0].title()}!",
                "Lee las instrucciones y comienza cuando estés listo. El tiempo empieza a contar al iniciar.",
                ["30 preguntas", "Opción múltiple A–D", "Sin límite de tiempo", "Puedes cambiar respuestas"])
        ui.pasos([
            ("Responde por componente", "Las preguntas están organizadas en tres pestañas. Muévete entre ellas libremente.", ui.AZUL),
            ("Revisa antes de enviar", "Las preguntas sin responder cuentan como incorrectas.", ui.AMBAR),
            ("Recibe tu diagnóstico", "Al enviar verás tu puntaje, tus gráficas y el análisis de la IA.", ui.VERDE),
        ])
        st.write("")
        if st.button("🚀  Iniciar prueba", type="primary", width="stretch"):
            try:
                st.session_state.examen = iniciar_examen(est["id_estudiante"], ID_MATERIA_MATEMATICAS)
            except db.ErrorBancoPreguntas as e:
                st.error(str(e))
                return
            st.rerun()
        return

    preguntas = ex["preguntas"]
    ui.kpis([
        ("📝", "Examen", f"N.º {ex['id_examen']}", "Intento registrado", ui.AZUL),
        ("❓", "Preguntas", str(len(preguntas)), "10 por componente", "#8B5CF6"),
        ("🧩", "Componentes", "3", "Estadística · Geometría · Cálculo", ui.VERDE),
        ("⏱️", "Inicio", time.strftime("%I:%M %p", time.localtime(ex["inicio"])), "Hora de inicio", ui.AMBAR),
    ])
    st.write("")

    grupos: dict[str, list[dict]] = {}
    for p in preguntas:
        grupos.setdefault(p["nombre_componente"], []).append(p)

    with st.form("form_examen", border=False):
        tabs = st.tabs([f"{ui.ICONOS_COMPONENTE.get(n, '')}  {n}" for n in grupos])
        numero = 0
        for tab, (nombre, ps) in zip(tabs, grupos.items()):
            with tab:
                for p in ps:
                    numero += 1
                    with st.container(key=f"preg_{p['id_pregunta']}"):
                        ui.cabecera_pregunta(numero, p)
                        st.radio("Respuesta", options=["A", "B", "C", "D"], index=None, key=f"p_{p['id_pregunta']}",
                                 format_func=lambda l, p=p: f"{l})  {p['opcion_' + l.lower()]}",
                                 label_visibility="collapsed", width="stretch")
        st.write("")
        confirmar = st.checkbox("Confirmo que deseo enviar mis respuestas (las preguntas sin responder cuentan como incorrectas).")
        enviar = st.form_submit_button("✅  Enviar y calificar", type="primary", width="stretch")

    if enviar:
        if not confirmar:
            st.warning("Marca la casilla de confirmación para enviar la prueba.")
            return
        respuestas = {p["id_pregunta"]: st.session_state.get(f"p_{p['id_pregunta']}") for p in preguntas}
        with st.spinner("Calificando y generando tu diagnóstico con Gemini AI…"):
            salida = finalizar_examen(ex["id_examen"], preguntas, respuestas, ex["inicio"],
                                      estudiante=est["nombres"])
        for p in preguntas:
            st.session_state.pop(f"p_{p['id_pregunta']}", None)
        st.session_state.examen = None
        st.session_state.ultimo_examen = ex["id_examen"]
        if salida["diagnostico"].get("origen") == "local":
            st.session_state.aviso_ia = salida["diagnostico"].get("aviso", "")
        ir("Dashboard")

    if st.button("Cancelar prueba", help="Anula este intento"):
        with db.conexion() as con:
            db.anular_examen(con, ex["id_examen"])
        st.session_state.examen = None
        st.rerun()


def mostrar_resultado(id_examen: int):
    with db.conexion() as con:
        ex = db.examen(con, id_examen)
        res = db.resultados_componente(con, id_examen)
        diag = db.diagnostico(con, id_examen)
        det = db.detalle_respuestas(con, id_examen)
        prom = db.promedios_globales(con)
    if not ex or not res:
        st.info("Este examen no tiene resultados.")
        return

    pct = round(ex["puntaje_total"] * 100 / ex["total_preguntas"], 1)
    nivel, color_nivel = ui.nivel_desempeno(pct)
    mejor = max(res, key=lambda r: r["porcentaje"])
    ui.kpis([
        ("🎯", "Puntaje global", f"{ex['puntaje_total']} / {ex['total_preguntas']}", f"{pct} % de acierto", ui.AZUL),
        ("🏅", "Nivel de desempeño", nivel, "Meta: 60 % o más", color_nivel),
        ("⭐", "Mejor componente", mejor["nombre_componente"], f"{mejor['porcentaje']:.0f} % de acierto",
         ui.color_componente(mejor["nombre_componente"])),
        ("⏱️", "Tiempo empleado", fmt_tiempo(ex["tiempo_segundos"]), ex["fecha_inicio"], "#8B5CF6"),
    ])

    ui.titulo_seccion("Resultados por componente", "Aciertos sobre 10 en cada área evaluada.")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(grafico_gauge(pct), width="stretch", config={"displayModeBar": False})
    with c2:
        ui.barras_componentes(res)
    g1, g2 = st.columns(2)
    g1.plotly_chart(grafico_barras(res), width="stretch", config={"displayModeBar": False})
    g2.plotly_chart(grafico_radar(res, prom), width="stretch", config={"displayModeBar": False})

    ui.titulo_seccion("🤖 Diagnóstico pedagógico", "Análisis personalizado de tu desempeño.")
    if diag:
        ui.etiqueta_ia(diag)
        st.write("")
        ui.tarjetas_diagnostico(diag)
    else:
        st.info("Sin diagnóstico registrado.")

    st.write("")
    with st.expander("📋  Ver detalle de respuestas"):
        df = pd.DataFrame(det)
        df["Resultado"] = df["es_correcta"].map({True: "✅", False: "❌"})
        df = df.rename(columns={"orden": "#", "nombre_componente": "Componente", "nombre_nivel": "Nivel",
                                "enunciado": "Pregunta", "respuesta_estudiante": "Tu respuesta",
                                "respuesta_correcta": "Clave"}).drop(columns=["es_correcta"])
        st.dataframe(df, hide_index=True, width="stretch")


def pagina_dashboard():
    if st.session_state.rol == "docente":
        ui.hero("Panel del docente", "Resultados de los estudiantes",
                "Consulta el desempeño de cada estudiante y los promedios del grupo.")
    else:
        ui.hero("Mis resultados", "Dashboard de desempeño",
                "Consulta tus resultados, tu evolución y el diagnóstico generado por la IA.")
    aviso = st.session_state.pop("aviso_ia", None)
    if aviso is not None:
        st.warning("Gemini AI no estaba disponible en este momento. Se generó el diagnóstico con el motor local de respaldo.")
        if aviso:
            with st.expander("Ver detalle del error de Gemini"):
                st.code(aviso, language=None)

    rol = st.session_state.rol
    if rol not in ("estudiante", "docente"):
        acceso_denegado("Ingresa como estudiante o docente para ver resultados.")
        return
    if rol == "docente":
        tab_est, tab_glob = st.tabs(["👤  Por estudiante", "🏫  Vista general"])
    else:
        tab_est, tab_glob = st.container(), None

    with tab_est:
        if rol == "docente":
            with db.conexion() as con:
                estudiantes = [e for e in db.listar_estudiantes(con) if e["examenes"] > 0]
            if not estudiantes:
                st.info("Aún no hay pruebas finalizadas.")
                return
            a, b = st.columns(2)
            est = a.selectbox("Estudiante", estudiantes,
                              format_func=lambda e: f"{e['nombres'].title()} {e['apellidos'].title()} · {e['documento']} ({e['examenes']} pruebas)")
        else:
            est = st.session_state.estudiante
            b = st.columns(2)[0]
        with db.conexion() as con:
            hist = db.historial(con, est["id_estudiante"])
        if not hist:
            st.info("Todavía no has finalizado ninguna prueba. Ve a «Presentar prueba» para comenzar.")
            return
        ids_ex = [h["id_examen"] for h in hist]
        pre = ids_ex.index(st.session_state.ultimo_examen) if st.session_state.ultimo_examen in ids_ex else 0
        sel = b.selectbox("Prueba", hist, index=pre,
                          format_func=lambda h: f"Examen N.º {h['id_examen']} · {h['fecha_inicio']} · {h['puntaje_total']}/30")
        st.write("")
        mostrar_resultado(sel["id_examen"])
        if len(hist) > 1:
            ui.titulo_seccion("📈 Evolución", "Puntaje obtenido en cada intento.")
            dfh = pd.DataFrame(list(reversed(hist)))
            dfh["intento"] = [f"Intento {i}<br><sub>{f[5:16]}</sub>" for i, f in enumerate(dfh["fecha_inicio"], start=1)]
            fig = go.Figure(go.Scatter(x=dfh["intento"], y=dfh["puntaje_total"], mode="lines+markers+text",
                                       text=dfh["puntaje_total"], textposition="top center",
                                       line=dict(color=ui.AZUL, width=3, shape="spline"),
                                       marker=dict(size=10, color="#fff", line=dict(color=ui.AZUL, width=3)),
                                       fill="tozeroy", fillcolor="rgba(59,91,253,.08)"))
            fig.update_traces(cliponaxis=False)
            fig.update_yaxes(range=[0, 33], gridcolor="#EEF2F7", title="Puntaje /30")
            fig.update_xaxes(showgrid=False, type="category", title=None)
            fig.update_layout(margin=dict(t=56, b=20, l=40, r=40))
            st.plotly_chart(estilo_figura(fig, "Evolución del puntaje", 320), width="stretch",
                            config={"displayModeBar": False})

    if tab_glob is None:
        return
    with tab_glob:
        with db.conexion() as con:
            rg = db.resumen_general(con)
            prom = db.promedios_globales(con)
        st.write("")
        ui.kpis([
            ("📝", "Pruebas finalizadas", str(rg["examenes"] or 0), "Total de intentos", ui.AZUL),
            ("👥", "Estudiantes", str(rg["estudiantes"] or 0), "Evaluados", "#8B5CF6"),
            ("🎯", "Puntaje promedio", f"{rg['promedio'] or 0} / 30", "Todos los intentos", ui.VERDE),
            ("⏱️", "Tiempo promedio", f"{rg['minutos'] or 0} min", "Por prueba", ui.AMBAR),
        ])
        if prom:
            st.write("")
            fig = go.Figure(go.Bar(x=[p["nombre_componente"] for p in prom], y=[p["promedio"] for p in prom], width=0.5,
                                   marker=dict(color=[ui.color_componente(p["nombre_componente"]) for p in prom], cornerradius=10),
                                   text=[f"<b>{p['promedio']}%</b>" for p in prom], textposition="outside"))
            fig.add_hline(y=60, line_dash="dot", line_color="#94A3B8", annotation_text="Meta 60 %")
            fig.update_yaxes(range=[0, 112], gridcolor="#EEF2F7", ticksuffix="%")
            st.plotly_chart(estilo_figura(fig, "Promedio institucional por componente"), width="stretch",
                            config={"displayModeBar": False})


def pagina_banco():
    if st.session_state.rol != "docente":
        acceso_denegado("El banco de preguntas (con las respuestas correctas) solo está disponible para el docente.")
        return
    with db.conexion() as con:
        resumen = db.banco_resumen(con)
        comps = db.componentes(con, ID_MATERIA_MATEMATICAS)
        nivs = db.niveles(con)
    df = pd.DataFrame(resumen)
    total = int(df["total"].sum()) if not df.empty else 0
    ui.hero("Administración", "Banco de preguntas",
            "Consulta las preguntas almacenadas en PostgreSQL (Neon) y agrega nuevas sin modificar la base de datos.",
            [f"{total} preguntas activas", f"{total * 4} opciones", "3 niveles de dificultad"])
    if not df.empty:
        por_comp = df.groupby("nombre_componente")["total"].sum()
        ui.kpis([(ui.ICONOS_COMPONENTE.get(c, "•"), c, str(int(por_comp.get(c, 0))), "preguntas",
                  ui.color_componente(c)) for c in [x["nombre_componente"] for x in comps]] +
                [("🗂️", "Total", str(total), "en el banco", "#8B5CF6")])
        ui.titulo_seccion("Distribución por nivel de dificultad")
        piv = df.pivot_table(index="nombre_componente", columns="nombre_nivel", values="total", aggfunc="sum", fill_value=0)
        piv["Total"] = piv.sum(axis=1)
        st.dataframe(piv.rename_axis("Componente"), width="stretch")

    ui.titulo_seccion("Explorar preguntas")
    comp = st.selectbox("Componente", comps, format_func=lambda c: c["nombre_componente"])
    with db.conexion() as con:
        st.dataframe(pd.DataFrame(db.preguntas_por_componente(con, comp["id_componente"])),
                     hide_index=True, width="stretch", height=320)

    st.write("")
    with st.expander("➕  Agregar una pregunta nueva"):
        with st.form("form_nueva", clear_on_submit=True, border=False):
            a, b = st.columns(2)
            c = a.selectbox("Componente", comps, format_func=lambda c: c["nombre_componente"])
            n = b.selectbox("Nivel de dificultad", nivs, format_func=lambda n: n["nombre_nivel"])
            enun = st.text_area("Enunciado")
            a, b = st.columns(2)
            ops = [a.text_input("Opción A"), b.text_input("Opción B"), a.text_input("Opción C"), b.text_input("Opción D")]
            clave = st.radio("Respuesta correcta", ["A", "B", "C", "D"], horizontal=True)
            if st.form_submit_button("Guardar pregunta", type="primary"):
                try:
                    with db.conexion() as con:
                        nid = db.agregar_pregunta(con, c["id_componente"], n["id_nivel"], enun, ops, clave)
                    st.success(f"Pregunta {nid} guardada.")
                except Exception as e:
                    st.error(f"No se pudo guardar: {e}")


def main():
    init_estado()
    if not DATABASE_URL:
        st.error("Falta la cadena de conexión `DATABASE_URL` de Neon (archivo `.env` en local o *Secrets* en Streamlit Cloud).")
        st.stop()
    if not bd_lista_cache():
        st.error("No fue posible conectarse a la base de datos o no existen las tablas. "
                 "Verifica `DATABASE_URL` y ejecuta `python scripts/init_db.py`.")
        st.stop()

    with st.sidebar:
        ui.marca_sidebar()
        etiquetas = {"Inicio": "🏠  Inicio", "Presentar prueba": "📝  Presentar prueba",
                     "Dashboard": "📊  Mis resultados" if st.session_state.rol == "estudiante" else "📊  Resultados",
                     "Banco de preguntas": "📚  Banco de preguntas"}
        claves = PAGINAS_POR_ROL[st.session_state.rol]
        if st.session_state.pagina not in claves:
            st.session_state.pagina = "Inicio"
        clave_menu = f"menu_{st.session_state.rol or 'invitado'}"
        st.session_state[clave_menu] = st.session_state.pagina
        st.radio("Navegación", claves, key=clave_menu, format_func=lambda k: etiquetas[k],
                 label_visibility="collapsed", on_change=cambiar_pagina, args=(clave_menu,))
        st.divider()
        est = st.session_state.estudiante
        if st.session_state.rol == "estudiante" and est:
            ui.usuario_sidebar("Estudiante", f"{est['nombres'].title()} {est['apellidos'].title()}", f"Doc. {est['documento']}")
        elif st.session_state.rol == "docente":
            ui.usuario_sidebar("Sesión iniciada", "Docente", "Acceso administrador")
        if st.session_state.rol:
            if st.button("Cerrar sesión", width="stretch"):
                cerrar_sesion()
            st.divider()
        ui.estado_sidebar("PostgreSQL · Neon conectado", True)
        ui.estado_sidebar(f"Gemini · {GEMINI_MODEL}" if GEMINI_API_KEY else "IA: motor local de respaldo",
                          bool(GEMINI_API_KEY))

    {"Inicio": pagina_inicio, "Presentar prueba": pagina_prueba,
     "Dashboard": pagina_dashboard, "Banco de preguntas": pagina_banco}[st.session_state.pagina]()


main()
