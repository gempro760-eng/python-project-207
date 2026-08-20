### Hexlet tests and linter status:
[![Actions Status](https://github.com/gempro760-eng/python-project-207/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/gempro760-eng/python-project-207/actions)

# Analizador de Páginas

Una aplicación web desarrollada con Flask que analiza páginas web y muestra información sobre su nivel de optimización para SEO y marketing.

🌐 **Aplicación en vivo:** [Haz clic aquí para ver la app](https://python-project-207-24ja.onrender.com)

## Requisitos
* Python >= 3.10
* uv
* PostgreSQL
* Make (opcional, para comandos rápidos)

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <repo-url>
   cd python-project-207
   ```

2. Crea y activa el entorno virtual con uv:
   ```bash
   uv venv
   . .venv/bin/activate   # Linux/macOS
   # o .\.venv\Scripts\activate  # Windows PowerShell
   ```

3. Instala las dependencias del proyecto:
   ```bash
   uv sync
   ```

4. Copia el archivo de ejemplo de entorno:
   ```bash
   cp .env.example .env
   ```
   Luego ajusta los valores dentro de `.env`.

## Variables de entorno

Crea un archivo `.env` con valores como estos:

```env
SECRET_KEY=change-me
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/page_analyzer
```

## Base de datos

Crea la base de datos y ejecuta el script SQL:

```bash
createdb page_analyzer
psql -d page_analyzer -f database.sql
```

Si prefieres usar Docker o un servidor PostgreSQL ya configurado, asegúrate de que `DATABASE_URL` apunte a una base disponible antes de ejecutar la app.

## Ejecución local

```bash
uv run flask --app page_analyzer:app run --debug
```

La aplicación quedará disponible en `http://127.0.0.1:5000`.

También puedes usar el atajo del proyecto:

```bash
make dev
```

## Comprobaciones

```bash
uv run ruff check .
uv run --with pytest pytest -q
```

## Stack

- Flask
- PostgreSQL
- psycopg2
- BeautifulSoup
- requests
- Gunicorn
- uv