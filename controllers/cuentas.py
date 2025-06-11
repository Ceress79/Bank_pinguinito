# controllers/cuentas.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session,  make_response
from extensions import mysql
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import render_template_string
import random
from datetime import datetime
from xhtml2pdf import pisa

cuentas_bp = Blueprint('cuentas', __name__)

@cuentas_bp.route('/')
def index():
    if 'usuario' not in session:
        flash("Debes iniciar sesión primero", "usuario")
        return redirect(url_for('auth.login'))

    cuentas = obtener_cuentas()
    cuentas = [x for x in cuentas if x['id_usuario'] == session.get('id_usuario')]
    user = {'nombre_completo': session.get('nombre_completo')}
    return render_template('index.html', cuentas=cuentas, user=user)

@cuentas_bp.route('/crear_cuenta')
def crear_cuenta():
    return render_template('crear_cuenta.html')


@cuentas_bp.route('/cuenta_bancaria')
def cuenta_bancaria():
    if 'usuario' not in session:
        flash("Debes iniciar sesión primero", "usuario")
        return redirect(url_for('auth.login'))

    cuentas = obtener_cuentas()
    user = {'nombre_completo': session.get('nombre_completo')}
    cuentas = [x for x in cuentas if x['id_usuario'] == session.get('id_usuario')]
    return render_template('cuenta_bancaria.html', cuentas=cuentas, user=user)


def obtener_cuentas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id_usuario, saldo FROM cuentas_bancarias")
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
            'id_usuario': row[6],
            'saldo': row[7]
        })
    return cuentas

@cuentas_bp.route('/crear_cuenta_bancaria', methods=['POST'])
def crear_cuenta_bancaria():
    tipo_cuenta = request.form['tipo_cuenta']
    apodo = request.form['apodo']
    limite_retiro = request.form['limite_retiro']
    max_retiros_diarios = request.form['max_retiros_diarios']
    id_usuario = session['id_usuario']

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
    return redirect(url_for('cuentas.cuenta_bancaria'))

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

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE cuentas_bancarias
        SET tipo_cuenta = %s, apodo = %s, limite_retiro = %s, max_retiros_diarios = %s
        WHERE id = %s
    """, (tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, id))
    mysql.connection.commit()
    flash("Cuenta actualizada correctamente", "usuario")
    return redirect(url_for('cuentas.index'))





@cuentas_bp.route('/descargar_certificado')
def descargar_certificado():
    if 'usuario' not in session:
        flash("Debes iniciar sesión primero", "usuario")
        return redirect(url_for('auth.login'))

    cuentas = obtener_cuentas()
    cuentas_usuario = [c for c in cuentas if c['id_usuario'] == session.get('id_usuario')]

    usuario = {
        "nombre_completo": session.get("nombre_completo"),
        "cedula": session.get("id_usuario"),
    }

    fecha = datetime.now().strftime("%d/%m/%Y")
    html_content = render_template("certificado.html", usuario=usuario, cuentas=cuentas_usuario, fecha=fecha)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)

    if pisa_status.err:
        return "Error al generar PDF", 500

    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=certificado_cuentas.pdf'

    return response