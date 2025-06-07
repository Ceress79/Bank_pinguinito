from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import mysql
from controllers.cuentas import obtener_cuentas

depositos_bp = Blueprint('depositos', __name__)

@depositos_bp.route('/crear_deposito', methods=['GET', 'POST'])
def crear_deposito():
    if request.method == 'POST':
        cuenta_destino = request.form['cuenta_destino']
        monto = float(request.form['monto'])
        cursor = mysql.connection.cursor()
        cuenta = obtener_cuentas()
        numeros_cuenta = []
        for c in cuenta:
            numeros_cuenta.append(c['numero_cuenta'])
        print(numeros_cuenta)
        if cuenta_destino not in numeros_cuenta:
            flash("Asegurese de que la cuenta de destino exista")
            return render_template('crear_deposito.html', cuentas = cuenta)
        cursor.execute("INSERT INTO deposito (num_cuenta_destino, monto) VALUES (%s, %s)", (cuenta_destino, monto))
        cursor.execute("UPDATE cuentas_bancarias set saldo=saldo+%s where numero_cuenta=%s",(monto, cuenta_destino))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('depositos.lista_depositos'))
    cuenta = obtener_cuentas()
    return render_template('crear_deposito.html', cuentas = cuenta)


@depositos_bp.route('/depositos')
def lista_depositos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM deposito")
    depositos = cursor.fetchall()
    cursor.close()
    return render_template('depositos.html', depositos=depositos)