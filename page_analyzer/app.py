import os
from dotenv import load_dotenv
from flask import Flask, render_template

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')

@app.route('/')
def index():
    return render_template('index.html')