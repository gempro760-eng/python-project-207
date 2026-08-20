import os

from dotenv import load_dotenv
from flask import Flask

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')

@app.route('/')
def index():
    return '¡Hola Flask!'