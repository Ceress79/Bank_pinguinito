# controllers/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import mysql
from datetime import datetime


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE correo = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['usuario'] = email
            session['nombre_completo'] = user[1]
            session['id_usuario']=user[0]
            flash("Has iniciado sesión correctamente", "usuario")
            return redirect(url_for('cuentas.index'))
        else:
            flash("Correo o contraseña incorrectos", "usuario")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        cedula = request.form['cedula']
        nombre_completo = request.form['nombre_completo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        fecha_nacimiento = request.form['fecha_nacimiento']
        tipo_cuenta = request.form['tipo_cuenta']
        confirmar_password = request.form['confirmar_password']
        password = request.form['password']

        try:
            fecha_formateada = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        except ValueError:
            return 'Formato de fecha inválido', 400

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO user (cedula, nombre_completo, correo, telefono, direccion, 
            fecha_nacimiento, tipo_cuenta, password) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (cedula, nombre_completo, correo, telefono, direccion, fecha_formateada, tipo_cuenta,
             password))
        mysql.connection.commit()

        flash("Cuenta de usuario creada correctamente", "usuario")
        return redirect(url_for('auth.login'))
