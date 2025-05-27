# controllers/cuentas.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mysql
import random

cuentas_bp = Blueprint('cuentas', __name__)

@cuentas_bp.route('/')
def index():
    if 'usuario' not in session:
        flash("Debes iniciar sesión primero", "usuario")
        return redirect(url_for('auth.login'))

    cuentas = obtener_cuentas()
    user = {'nombre_completo': session.get('nombre_completo')}
    return render_template('index.html', cuentas=cuentas, user=user)

def obtener_cuentas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id_usuario FROM cuentas_bancarias")
    resultados = cur.fetchall()
    cur.close()

    cuentas = []
    for row in resultados:
        cuentas.append({
            'id': row[0],
            'numero_cuenta': row[1],
            'tipo_cuenta': row[2],
            'apodo': row[3],
            'limite_retiro': row[4],
            'max_retiros_diarios': row[5],
            'id_usuario': row[6]
        })
    return cuentas

@cuentas_bp.route('/crear_cuenta')
def crear_cuenta():
    return render_template('crear_cuenta.html')

@cuentas_bp.route('/crear_cuenta_bancaria', methods=['POST'])
def crear_cuenta_bancaria():
    tipo_cuenta = request.form['tipo_cuenta']
    apodo = request.form['apodo']
    limite_retiro = request.form['limite_retiro']
    max_retiros_diarios = request.form['max_retiros_diarios']
    id_usuario = request.form['id_usuario']

    while True:
        numero_cuenta = '2206' + ''.join([str(random.randint(0, 9)) for _ in range(6)])
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM cuentas_bancarias WHERE numero_cuenta = %s", (numero_cuenta,))
        if not cur.fetchone():
            break

    cur.execute("""
        INSERT INTO cuentas_bancarias 
        (numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id_usuario, saldo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id_usuario, 10))
    mysql.connection.commit()
    return redirect(url_for('cuentas.index'))

@cuentas_bp.route('/eliminar_cuenta/<int:id>')
def eliminar_cuenta(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cuentas_bancarias WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Cuenta eliminada")
    return redirect(url_for('cuentas.index'))

@cuentas_bp.route('/editar_cuenta/<int:id>', methods=['POST'])
def editar_cuenta(id):
    tipo_cuenta = request.form['tipo_cuenta']
    apodo = request.form['apodo']
    limite_retiro = request.form['limite_retiro']
    max_retiros_diarios = request.form['max_retiros_diarios']
    id_usuario = request.form['id_usuario']

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE cuentas_bancarias
        SET tipo_cuenta = %s, apodo = %s, limite_retiro = %s, max_retiros_diarios = %s, id_usuario = %s
        WHERE id = %s
    """, (tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id_usuario, id))
    mysql.connection.commit()
    flash("Cuenta actualizada correctamente", "usuario")
    return redirect(url_for('cuentas.index'))
