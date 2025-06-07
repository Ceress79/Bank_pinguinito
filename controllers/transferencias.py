from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import mysql
from controllers.cuentas import obtener_cuentas

transferencias_bp = Blueprint('transferencias', __name__)

@transferencias_bp.route('/crear_transferencia', methods=['GET', 'POST'])
def crear_transferencia():
    if request.method == 'POST':
        cuenta_origen = request.form['cuenta_origen']
        cuenta_destino = request.form['cuenta_destino']
        monto = float(request.form['monto'])
        cursor = mysql.connection.cursor()
        cursor.execute("Select saldo from cuentas_bancarias where numero_cuenta=%s", [cuenta_origen])
        saldo = float(cursor.fetchone()[0])
        cuenta = obtener_cuentas()
        mis_cuentas = [x for x in cuenta if x['id_usuario'] == session.get('id_usuario')]
        numeros_cuenta = []
        for c in cuenta:
            numeros_cuenta.append(c['numero_cuenta'])
        if cuenta_destino not in numeros_cuenta:
            flash("Asegurese de que la cuenta de destino exista")
            return render_template('crear_transferencia.html', cuentas = mis_cuentas)
        elif(saldo-monto <0):
            flash("Asegurese de que el monto no sea mayor que el saldo disponible de la cuenta")
            return render_template('crear_transferencia.html', cuentas = mis_cuentas)
        cursor.execute("INSERT INTO transferencia (num_cuenta_origen, num_cuenta_destino, monto) VALUES (%s, %s, %s)", (cuenta_origen, cuenta_destino, monto))
        cursor.execute("UPDATE cuentas_bancarias set saldo=saldo-%s where numero_cuenta=%s",(monto, cuenta_origen))
        cursor.execute("UPDATE cuentas_bancarias set saldo=saldo+%s where numero_cuenta=%s",(monto, cuenta_destino))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('transferencias.lista_transferencias'))
    cuenta = obtener_cuentas()
    mis_cuentas = [x for x in cuenta if x['id_usuario'] == session.get('id_usuario')]
    return render_template('crear_transferencia.html', cuentas = mis_cuentas)


@transferencias_bp.route('/transferencias')
def lista_transferencias():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM transferencia where (num_cuenta_origen in (select numero_cuenta from cuentas_bancarias where id_usuario = %s)) or (num_cuenta_destino in (select numero_cuenta from cuentas_bancarias where id_usuario = %s)) ", (session['id_usuario'], session['id_usuario']))
    transferencias = cursor.fetchall()
    cursor.close()
    return render_template('transferencias.html', transferencias=transferencias)
