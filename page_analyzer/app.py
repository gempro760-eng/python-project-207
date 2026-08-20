import os
import psycopg2
import validators
from urllib.parse import urlparse
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(app.config['DATABASE_URL'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def post_url():
    # 1. Recibir la URL del formulario
    url_input = request.form.get('url', '')

    # 2. Validar formato y longitud
    if not validators.url(url_input) or len(url_input) > 255:
        flash('URL no válida', 'danger')
        return render_template('index.html'), 422

    # 3. Extraer y limpiar el nombre (ej: https://www.ejemplo.com)
    parsed = urlparse(url_input)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}"

    # 4. Guardar en la base de datos
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Revisar si la URL ya existía
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash('La página ya existe', 'info')
            url_id = existing_url[0]
        else:
            # Si es nueva, insertarla
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (normalized_url,)
            )
            url_id = cur.fetchone()[0]
            conn.commit()
            flash('Página agregada con éxito', 'success')

    except Exception:
        conn.rollback()
        flash('Ocurrió un error en la base de datos', 'danger')
        return render_template('index.html'), 500
    finally:
        cur.close()
        conn.close()

    # Redirigir a la página individual de la URL
    return redirect(url_for('show_url', id=url_id))


# Ruta temporal para la página individual
@app.route('/urls', methods=['GET'])
def get_urls():
    # Obtener todas las URLs, ordenadas desde la más reciente (DESC)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM urls ORDER BY id DESC")
    urls_data = cur.fetchall()
    cur.close()
    conn.close()

    # Convertimos las tuplas en diccionarios para que Jinja las lea fácil
    urls_list = [{'id': row[0], 'name': row[1], 'created_at': row[2]} for row in urls_data]
    
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def show_url(id):
    # Buscar una URL específica por su ID
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
    url_data = cur.fetchone()
    cur.close()
    conn.close()

    if not url_data:
        return "Página no encontrada", 404

    # Convertimos la tupla en diccionario
    url_dict = {'id': url_data[0], 'name': url_data[1], 'created_at': url_data[2]}
    
    return render_template('show.html', url=url_dict)