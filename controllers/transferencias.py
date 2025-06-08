from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import mysql
from datetime import datetime

from controllers.cuentas import obtener_cuentas  # Asumo que esta función está bien y devuelve todas las cuentas

transferencias_bp = Blueprint('transferencias', __name__)

@transferencias_bp.route('/crear_transferencia', methods=['GET', 'POST'])
def crear_transferencia():
    if request.method == 'POST':
        cuenta_origen = request.form['cuenta_origen']
        cuenta_destino = request.form['cuenta_destino']
        monto = float(request.form['monto'])
        mensaje = request.form.get('mensaje', '').strip()  # Obtener mensaje, si no hay, cadena vacía

        cursor = mysql.connection.cursor()

        # Obtener saldo actual de la cuenta origen
        cursor.execute("SELECT saldo FROM cuentas_bancarias WHERE numero_cuenta = %s", (cuenta_origen,))
        saldo_result = cursor.fetchone()
        if saldo_result is None:
            flash("La cuenta origen no existe.")
            cursor.close()
            return redirect(url_for('transferencias.crear_transferencia'))

        saldo = float(saldo_result[0])

        # Obtener todas las cuentas para validación
        cuentas = obtener_cuentas()
        mis_cuentas = [c for c in cuentas if c['id_usuario'] == session.get('id_usuario')]
        numeros_cuenta = [c['numero_cuenta'] for c in cuentas]

        # Validar cuenta destino
        if cuenta_destino not in numeros_cuenta:
            flash("Asegúrese de que la cuenta de destino exista.")
            cursor.close()
            return render_template('crear_transferencia.html', cuentas=mis_cuentas)

        # Validar saldo suficiente
        if saldo < monto:
            flash("Asegúrese de que el monto no sea mayor que el saldo disponible de la cuenta.")
            cursor.close()
            return render_template('crear_transferencia.html', cuentas=mis_cuentas)

        # Registrar transferencia y actualizar saldos
        try:
            cursor.execute("""
                INSERT INTO transferencia (num_cuenta_origen, num_cuenta_destino, monto, mensaje, fecha)
                VALUES (%s, %s, %s, %s, %s)
            """, (cuenta_origen, cuenta_destino, monto, mensaje, datetime.now()))

            cursor.execute("UPDATE cuentas_bancarias SET saldo = saldo - %s WHERE numero_cuenta = %s", (monto, cuenta_origen))
            cursor.execute("UPDATE cuentas_bancarias SET saldo = saldo + %s WHERE numero_cuenta = %s", (monto, cuenta_destino))

            mysql.connection.commit()
            flash("Transferencia realizada con éxito.")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Ocurrió un error al realizar la transferencia: {str(e)}")
        finally:
            cursor.close()

        return redirect(url_for('transferencias.lista_transferencias'))

    # GET - mostrar formulario con las cuentas del usuario
    cuentas = obtener_cuentas()
    mis_cuentas = [c for c in cuentas if c['id_usuario'] == session.get('id_usuario')]
    return render_template('crear_transferencia.html', cuentas=mis_cuentas)


@transferencias_bp.route('/transferencias')
def lista_transferencias():
    cursor = mysql.connection.cursor()
    id_usuario = session.get('id_usuario')
    if not id_usuario:
        flash("Debe iniciar sesión para ver sus transferencias.")
        return redirect(url_for('auth.login'))  # Ajusta según tu blueprint de login

    query = """
        SELECT t.id, t.num_cuenta_origen, t.num_cuenta_destino, t.monto, t.fecha
        FROM transferencia t
        WHERE t.num_cuenta_origen IN (SELECT numero_cuenta FROM cuentas_bancarias WHERE id_usuario = %s)
           OR t.num_cuenta_destino IN (SELECT numero_cuenta FROM cuentas_bancarias WHERE id_usuario = %s)
        ORDER BY t.fecha DESC
    """
    cursor.execute(query, (id_usuario, id_usuario))
    transferencias = cursor.fetchall()
    cursor.close()

    return render_template('transferencias.html', transferencias=transferencias)


@transferencias_bp.route('/api/validar_cuenta', methods=['POST'])
def validar_cuenta():
    data = request.get_json()
    num_cuenta = data.get('num_cuenta') if data else None

    if not num_cuenta:
        return jsonify({'error': 'No se recibió número de cuenta'}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT u.nombre_completo, u.cedula, u.correo
        FROM cuentas_bancarias cb
        JOIN user u ON cb.id_usuario = u.cedula
        WHERE cb.numero_cuenta = %s
    """, (num_cuenta,))
    resultado = cursor.fetchone()
    cursor.close()

    if resultado:
        nombre, cedula, correo = resultado
        return jsonify({
            'nombre': nombre,
            'cedula': cedula,
            'correo': correo
        })
    else:
        return jsonify({'error': 'Cuenta no existe'}), 404
