# Sistema Adaptativo de Evaluación Diagnóstica y Analítica con IA

Uniagustiniana · Tecnología en Desarrollo de Software · Gestión de Bases de Datos (Semestre V)
Docente: Ing. Leonel Lugo Mendoza · Equipo: Yeison Fabian Maceto Huertas, Brayan

Banco de 150 preguntas de Matemáticas (Estadística, Geometría, Cálculo y Álgebra). El sistema genera
exámenes aleatorios de 30 preguntas (10 por componente), los califica automáticamente, guarda el
historial en **PostgreSQL (Neon)**, pide un diagnóstico pedagógico a **Gemini AI** y lo muestra en un
**dashboard** hecho con **Streamlit**.

```
Navegador ──► app.py (Streamlit: frontend) ──► src/ (lógica + SQL) ──► Neon (PostgreSQL)
                                                     └──────────────► API de Gemini
```

---

## Roles de acceso

| Rol | Cómo entra | Qué puede hacer |
| --- | --- | --- |
| **Estudiante** | Con su documento, nombres y apellidos | Presentar la prueba y ver **solo sus** resultados |
| **Docente** | Con la contraseña `DOCENTE_PASSWORD` | Ver el banco de preguntas (con las claves), agregar preguntas y ver los resultados de todos |

Sin iniciar sesión solo se ve la página de Inicio. La contraseña del docente va en `.env`
(local) o en *Secrets* (Streamlit Cloud), nunca en el código.

## 1. Crear la base de datos en Neon (una sola vez)

1. Crear una cuenta en <https://neon.tech> y un proyecto (región: la más cercana, p. ej. *AWS US East*).
2. En el panel del proyecto: **Connect** → copiar la **Connection string** (la versión *pooled*).
   Tiene la forma `postgresql://usuario:clave@ep-xxxx-pooler....neon.tech/neondb?sslmode=require`.
3. Crear las tablas y cargar el banco. Hay dos opciones:
   - **Desde el SQL Editor de Neon:** pegar y ejecutar, en orden, `database/01_schema.sql`,
     `database/02_insert_catalogos.sql` y `database/03_insert_preguntas.sql`.
   - **Desde el computador:** configurar el `.env` (paso 2.4) y ejecutar `python scripts/init_db.py`.
4. Verificar: `python scripts/init_db.py --verificar` → 10 tablas, 50 preguntas por componente,
   todas con 4 opciones y 1 correcta.

> `01_schema.sql` solo **crea** las tablas (se ejecuta una vez sobre la base vacía). Si algún día necesitan
> empezar de cero, ejecuten antes `database/00_reiniciar.sql`, que borra todo. `init_db.py` hace ambas cosas
> (reinicia y crea), así que úselo solo para crear la base o reiniciarla.

## 2. Ejecutar en el computador (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # pegar DATABASE_URL, GEMINI_API_KEY y DOCENTE_PASSWORD
python scripts/datos_demo.py    # (opcional) exámenes de demostración para el dashboard
streamlit run app.py            # abre http://localhost:8501
```

En Linux o macOS: `python3`, `source .venv/bin/activate` y `cp .env.example .env`.
Sin `GEMINI_API_KEY` el sistema funciona con un diagnóstico local de respaldo.

## 3. Subir a GitHub

```bash
git init
git add .
git commit -m "Sistema de evaluación diagnóstica con IA"
git branch -M main
git remote add origin https://github.com/yeiso222/evaluacion-diagnostica-ia.git
git push -u origin main
```

(Primero crear el repositorio vacío `evaluacion-diagnostica-ia` en github.com y agregar a Brayan
como colaborador en *Settings → Collaborators*.) El `.gitignore` evita que se suban `.env` y
`secrets.toml`, que contienen las claves.

## 4. Publicar en Streamlit Community Cloud (link público)

1. Entrar a <https://share.streamlit.io> con la cuenta de GitHub.
2. **Create app** → elegir el repositorio, rama `main` y archivo principal `app.py`.
3. En **Advanced settings → Secrets** pegar el contenido de `.streamlit/secrets.toml.example`
   con los valores reales (`DATABASE_URL` y `GEMINI_API_KEY`).
4. **Deploy**. La app queda en un link del tipo `https://<nombre>.streamlit.app`.

Los datos quedan en Neon, así que no se pierden aunque la app se reinicie.

## 5. Pruebas automáticas

Las pruebas **borran y recrean las tablas**, así que se ejecutan contra una base aparte:
en Neon, **Branches → New branch** (p. ej. `pruebas`) y copiar su cadena de conexión en
`TEST_DATABASE_URL` del `.env`.

```bash
python -m pytest -v        # 10 pruebas del Definition of Done
```

## Estructura

| Ruta | Contenido |
| --- | --- |
| `app.py` | **Frontend**: interfaz web en Streamlit (registro, examen, dashboard, banco) |
| `src/db.py` | **Conexión a Neon** y todas las consultas SQL (pool de conexiones psycopg) |
| `src/examen.py` | Lógica del examen: selección, calificación, resumen para la IA |
| `src/gemini_ai.py` | **Conexión con la API de Gemini** (salida estructurada + respaldo local) |
| `src/config.py` | Lee `.env` (local) o *Secrets* (Streamlit Cloud) |
| `database/00_reiniciar.sql` | Borra todas las tablas (solo para empezar de cero) |
| `database/01_schema.sql` | **Script SQL de creación**: 10 tablas, PK/FK, CHECK, UNIQUE, índices, vistas |
| `database/02_insert_catalogos.sql` | Materias, componentes y niveles de dificultad |
| `database/03_insert_preguntas.sql` | Inserción masiva: 150 preguntas y 600 opciones |
| `database/04_consultas_utiles.sql` | Consultas para la sustentación |
| `scripts/generar_banco_preguntas.py` | Genera el banco; las claves se calculan con código |
| `scripts/init_db.py` | Crea y verifica la base de datos en Neon |
| `scripts/datos_demo.py` | Simula exámenes de 5 estudiantes |
| `tests/test_sistema.py` | Pruebas automáticas del DoD |
| `docs/` | DER (png/svg) y capturas de pantalla |

## Base de datos (10 tablas)

`materias`, `componentes`, `nivel_dificultad`, `preguntas`, **`opciones_respuesta` (tabla adicional)**,
`estudiantes`, `examenes`, `detalle_examen`, `resultados_componente`, `diagnosticos_ia`.

Reglas garantizadas por la propia base de datos:
- 4 opciones por pregunta (`UNIQUE (id_pregunta, letra)` + `CHECK letra IN ('A','B','C','D')`).
- Una sola correcta por pregunta (índice único parcial `uq_una_correcta_por_pregunta`).
- La opción elegida pertenece a su pregunta (FK compuesta en `detalle_examen`).
- Sin preguntas repetidas en un examen y orden 1–30 (`UNIQUE` + `CHECK`).
- Un diagnóstico por examen (`UNIQUE id_examen`).

Para agregar una materia nueva (p. ej. Inglés) basta con insertar registros en `materias`,
`componentes`, `preguntas` y `opciones_respuesta`; no hay que cambiar tablas ni código.
