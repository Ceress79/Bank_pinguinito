from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import mysql, mail
from flask_mail import Message
from datetime import datetime
import random
import string

auth_bp = Blueprint('auth', __name__)

# Diccionario temporal para almacenar códigos de recuperación (email: código)
recovery_codes = {}

# LOGIN
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE correo = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['usuario'] = email
            session['nombre_completo'] = user[1]
            session['id_usuario']=user[0]
            session['rol']=user[6]
            flash("Has iniciado sesión correctamente", "usuario")
            if session['rol']=='u':
                return redirect(url_for('cuentas.index'))
            else:
                return redirect(url_for('depositos.lista_depositos'))
        else:
            flash("Correo o contraseña incorrectos", "usuario")

    return render_template('login.html')

# LOGOUT
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# REGISTRO USUARIO
@auth_bp.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        cedula = request.form['cedula']
        nombre_completo = request.form['nombre_completo']
        correo = request.form['correo'].lower()
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        fecha_nacimiento = request.form['fecha_nacimiento']
        tipo_cuenta = 'u'
        confirmar_password = request.form['confirmar_password']
        password = request.form['password']

        try:
            fecha_formateada = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        except ValueError:
            return 'Formato de fecha inválido', 400

        # Ideal: validar que password y confirmar_password coincidan antes de insertar
        if password != confirmar_password:
            flash("Las contraseñas no coinciden", "usuario")
            return redirect(url_for('auth.login'))

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO user (cedula, nombre_completo, correo, telefono, direccion, 
            fecha_nacimiento, rol, password) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (cedula, nombre_completo, correo, telefono, direccion, fecha_formateada, tipo_cuenta,
             password))
        mysql.connection.commit()
        cur.close()

        flash("Cuenta de usuario creada correctamente", "usuario")
        return redirect(url_for('auth.login'))


# ENVIAR CÓDIGO DE RECUPERACIÓN POR CORREO
@auth_bp.route('/enviar_codigo', methods=['POST'])
def enviar_codigo():
    data = request.json  # porque vas a enviar JSON desde JS
    correo = data.get('correo')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE correo = %s", (correo,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify({'error': 'Correo no registrado'}), 400

    # Generar código aleatorio de 6 dígitos
    codigo = ''.join(random.choices(string.digits, k=6))
    session['codigo_recuperacion'] = codigo
    session['correo_recuperacion'] = correo

    # Enviar email (ejemplo básico)
    msg = Message('Código de recuperación', sender='tuemail@dominio.com', recipients=[correo])
    msg.body = f'Tu código de recuperación es: {codigo}'
    mail.send(msg)

    return jsonify({'message': 'Código enviado correctamente'})



# VERIFICAR CÓDIGO DE RECUPERACIÓN
@auth_bp.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    data = request.get_json()
    email = data.get('email', '').lower()
    codigo = data.get('codigo', '')

    if recovery_codes.get(email) == codigo:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Código incorrecto'})


# CAMBIAR CONTRASEÑA
@auth_bp.route('/cambiar_contrasena', methods=['POST'])
def cambiar_contrasena():
    data = request.get_json()
    email = data.get('email', '').lower()
    nueva_contrasena = data.get('nueva_contrasena', '')
    confirmar_contrasena = data.get('confirmar_contrasena', '')

    if nueva_contrasena != confirmar_contrasena:
        return jsonify({'success': False, 'message': 'Las contraseñas no coinciden'})

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE correo = %s", (email,))
    user = cur.fetchone()

    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'})

    try:
        cur.execute("UPDATE user SET password = %s, confirmar_password = %s WHERE correo = %s",
                    (nueva_contrasena, confirmar_contrasena, email))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Error actualizando contraseña:", e)
        return jsonify({'success': False, 'message': 'Error al cambiar la contraseña'})

    # Quitar código usado
    recovery_codes.pop(email, None)

    return jsonify({'success': True, 'message': 'Contraseña cambiada correctamente'})
