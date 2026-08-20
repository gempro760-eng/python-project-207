import os
import re
import psycopg2
import validators
import requests 
from bs4 import BeautifulSoup
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


def get_text_content(node):
    if node is None:
        return ''
    return node.get_text(' ', strip=True) or ''


def truncate_text(value, max_length=200):
    if value is None:
        return ''
    text = str(value).strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def post_url():
    url_input = request.form.get('url', '')

    if not validators.url(url_input) or len(url_input) > 255:
        flash('URL no válido', 'danger')
        return render_template('index.html'), 422

    parsed = urlparse(url_input)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}"

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash('La página ya existe', 'info')
            url_id = existing_url[0]
        else:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (normalized_url,)
            )
            url_id = cur.fetchone()[0]
            conn.commit()
            flash('La página se agregó correctamente', 'success')

    except Exception:
        conn.rollback()
        flash('Ocurrió un error en la base de datos', 'danger')
        return render_template('index.html'), 500
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('show_url', id=url_id))


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT urls.id,
               urls.name,
               urls.created_at,
               last_check.created_at AS last_check,
               last_check.status_code AS last_status_code
        FROM urls
        LEFT JOIN LATERAL (
            SELECT created_at, status_code
            FROM url_checks
            WHERE url_id = urls.id
            ORDER BY created_at DESC
            LIMIT 1
        ) AS last_check ON true
        ORDER BY urls.id DESC
    """)
    urls_data = cur.fetchall()
    cur.close()
    conn.close()

    urls_list = [
        {
            'id': row[0],
            'name': row[1],
            'created_at': row[2],
            'last_check': row[3],
            'status_code': row[4]
        }
        for row in urls_data
    ]
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
    url_data = cur.fetchone()
    
    if not url_data:
        cur.close()
        conn.close()
        return "Página no encontrada", 404

    url_dict = {'id': url_data[0], 'name': url_data[1], 'created_at': url_data[2]}

    cur.execute("""
        SELECT id, status_code, h1, title, description, created_at 
        FROM url_checks WHERE url_id = %s ORDER BY id DESC
    """, (id,))
    checks_data = cur.fetchall()
    
    cur.close()
    conn.close()

    checks_list = [
        {
            'id': row[0], 'status_code': row[1], 'h1': row[2], 
            'title': row[3], 'description': row[4], 'created_at': row[5]
        } for row in checks_data
    ]
    
    return render_template('show.html', url=url_dict, checks=checks_list)

 
@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
    url_data = cur.fetchone()
    
    if not url_data:
        cur.close()
        conn.close()
        return "Página no encontrada", 404

    url_name = url_data[0]

    try:
        response = requests.get(url_name, timeout=5)
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')

        title = truncate_text(get_text_content(soup.find('title')))
        h1 = truncate_text(get_text_content(soup.find('h1')))

        meta_desc = soup.find(
            'meta',
            attrs={'name': re.compile(r'description', re.IGNORECASE)}
        )
        description = truncate_text(meta_desc.get('content', '').strip()) if meta_desc else ''

        cur.execute(
            """
            INSERT INTO url_checks (url_id, status_code, h1, title, description) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id, status_code, h1, title, description)
        )
        conn.commit()
        flash('La página fue verificada correctamente', 'success')

    except requests.RequestException:
        conn.rollback()
        flash('Ocurrió un error durante la verificación', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('show_url', id=id))