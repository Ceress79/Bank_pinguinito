from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import random

#Cada vez que el usuario entre en la ruta principal. lo lleva directamente a esta ruta

app = Flask( __name__)

#Mysql connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'banco_pinguino'
mysql = MySQL(app)

#settings 
app.secret_key = 'mysecretkey'



@app.route('/')
def Index():
    if 'usuario' not in session:
        flash("Debes iniciar sesión primero", "usuario")
        return redirect(url_for('login'))

    cuentas = obtener_cuentas()
    user = {'nombre_completo': session.get('nombre_completo')}
    return render_template('index.html', cuentas=cuentas, user=user)



def obtener_cuentas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, nombre_usuario FROM cuentas_bancarias")
    resultados = cur.fetchall()
    cur.close()
    
    cuentas = []
    for row in resultados:
        cuenta = {
            'id': row[0],
            'numero_cuenta': row[1],
            'tipo_cuenta': row[2],
            'apodo': row[3],
            'limite_retiro': row[4],
            'max_retiros_diarios': row[5],
            'nombre_usuario': row[6]
        }
        cuentas.append(cuenta)
    return cuentas



# Validar que el usuairo este en la cuenta.
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
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
            session['nombre_completo'] = user[1]  # Solo nombre_completo
            flash("Haz Cerrado Sesion", "usuario")
            return redirect(url_for('Index'))
        else:
            flash("Correo o contraseña incorrectos", "usuario")
            return render_template('login.html')
    else:
        return render_template('login.html')




#Funcion para salir de la cuenta
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


@app.route('/crear_cuenta')
def crear_cuenta():
    return render_template('crear_cuenta.html')

@app.route('/crear_cuenta_bancaria', methods=['POST'])
def crear_cuenta_bancaria():
    if request.method == 'POST':
        tipo_cuenta = request.form['tipo_cuenta']
        apodo = request.form['apodo']
        limite_retiro = request.form['limite_retiro']
        max_retiros_diarios = request.form['max_retiros_diarios']
        nombre_usuario = request.form['nombre_usuario']

        # Generar número de cuenta único
        while True:
            numero_cuenta = '2206' + ''.join([str(random.randint(0, 9)) for _ in range(6)])
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM cuentas_bancarias WHERE numero_cuenta = %s", (numero_cuenta,))
            if not cur.fetchone():
                break

        cur.execute("""
            INSERT INTO cuentas_bancarias (numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, nombre_usuario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (numero_cuenta, tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, nombre_usuario))

        mysql.connection.commit()
        return redirect(url_for('Index'))


#Ruta para agregar al usuario
@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        cedula = request.form['cedula']
        nombre_completo = request.form['nombre_completo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        fecha_nacimiento = request.form['fecha_nacimiento']  # <-- CAPTURAMOS LA FECHA
        tipo_cuenta = request.form['tipo_cuenta']
        confirmar_password = request.form['confirmar_password']
        password = request.form['password']

        # Verifica si es una fecha válida
        try:
            fecha_formateada = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        except ValueError:
            return 'Formato de fecha inválido', 400

        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO user (
                cedula, nombre_completo, correo, telefono, direccion, fecha_nacimiento, tipo_cuenta,
                confirmar_password, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                (cedula, nombre_completo, correo, telefono, direccion, fecha_formateada, tipo_cuenta,
                 confirmar_password, password ))

        mysql.connection.commit()
        flash("Cuenta de usuario creada correctamente", "usuario")
        return redirect(url_for('login'))

        


#Ruta editar datos
@app.route('/eliminar_cuenta/<int:id>')
def eliminar_cuenta(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cuentas_bancarias WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Cuenta eliminada")
    return redirect(url_for('Index'))


@app.route('/editar_cuenta/<int:id>', methods=['POST'])
def editar_cuenta(id):
    tipo_cuenta = request.form['tipo_cuenta']
    apodo = request.form['apodo']
    limite_retiro = request.form['limite_retiro']
    max_retiros_diarios = request.form['max_retiros_diarios']
    nombre_usuario = request.form['nombre_usuario']

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE cuentas_bancarias
        SET tipo_cuenta = %s,
            apodo = %s,
            limite_retiro = %s,
            max_retiros_diarios = %s,
            nombre_usuario = %s
        WHERE id = %s
    """, (tipo_cuenta, apodo, limite_retiro, max_retiros_diarios, nombre_usuario, id))

    mysql.connection.commit()
    flash("Cuenta actualizada correctamente", "usuario")
    return redirect(url_for('Index'))

    


if __name__ == '__main__':
    app.run(port = 3000, debug= True)   