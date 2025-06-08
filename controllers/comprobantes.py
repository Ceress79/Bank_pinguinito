from flask import Blueprint, render_template, session
from extensions import mysql

comprobantes_bp = Blueprint('comprobantes', __name__)

@comprobantes_bp.route('/comprobantes')
def historial_transferencias():
    usuario_id = session['id_usuario']
    cursor = mysql.connection.cursor()

    # Obtener todas las cuentas del usuario
    cursor.execute("SELECT numero_cuenta FROM cuentas_bancarias WHERE id_usuario = %s", (usuario_id,))
    cuentas_usuario = [cuenta[0] for cuenta in cursor.fetchall()]

    transferencias = []

    # ===============================
    # TRANSFERENCIAS (envíos/recepciones)
    # ===============================
    cursor.execute("""
        SELECT 
            t.num_cuenta_origen,
            u_origen.nombre_completo AS nombre_origen,
            t.num_cuenta_destino,
            u_destino.nombre_completo AS nombre_destino,
            t.monto,
            t.fecha,
            t.mensaje
        FROM transferencia t
        JOIN cuentas_bancarias c_origen ON t.num_cuenta_origen = c_origen.numero_cuenta
        JOIN cuentas_bancarias c_destino ON t.num_cuenta_destino = c_destino.numero_cuenta
        JOIN user u_origen ON c_origen.id_usuario = u_origen.cedula
        JOIN user u_destino ON c_destino.id_usuario = u_destino.cedula
        ORDER BY t.fecha DESC
    """)
    for row in cursor.fetchall():
        cuenta_origen, nombre_origen, cuenta_destino, nombre_destino, monto, fecha, mensaje = row

        # Saldo de la cuenta origen después de la transferencia
        cursor.execute("SELECT saldo FROM cuentas_bancarias WHERE numero_cuenta = %s", (cuenta_origen,))
        saldo_origen_despues = cursor.fetchone()[0]
        saldo_origen_antes = saldo_origen_despues + monto

        # Saldo de la cuenta destino después de la transferencia
        cursor.execute("SELECT saldo FROM cuentas_bancarias WHERE numero_cuenta = %s", (cuenta_destino,))
        saldo_destino_despues = cursor.fetchone()[0]
        saldo_destino_antes = saldo_destino_despues - monto

        if cuenta_origen in cuentas_usuario:
            transferencias.append({
                'tipo': 'envio',
                'cuenta_origen': cuenta_origen,
                'nombre_origen': nombre_origen,
                'cuenta_destino': cuenta_destino,
                'nombre_destino': nombre_destino,
                'saldo_antes': saldo_origen_antes,
                'monto': -monto,
                'saldo_despues': saldo_origen_despues,
                'fecha': fecha,
                'mensaje': mensaje
            })

        if cuenta_destino in cuentas_usuario:
            transferencias.append({
                'tipo': 'recepcion',
                'cuenta_origen': cuenta_origen,
                'nombre_origen': nombre_origen,
                'cuenta_destino': cuenta_destino,
                'nombre_destino': nombre_destino,
                'saldo_antes': saldo_destino_antes,
                'monto': +monto,
                'saldo_despues': saldo_destino_despues,
                'fecha': fecha,
                'mensaje': mensaje
            })

    # ===============================
    # DEPÓSITOS (solo recepciones)
    # ===============================
    cursor.execute("""
        SELECT d.num_cuenta_destino, d.monto, d.fecha, u.nombre_completo
        FROM deposito d
        JOIN cuentas_bancarias c ON d.num_cuenta_destino = c.numero_cuenta
        JOIN user u ON c.id_usuario = u.cedula
        ORDER BY d.fecha DESC
    """)
    for cuenta_destino, monto, fecha, nombre_destino in cursor.fetchall():
        if cuenta_destino in cuentas_usuario:
            # Saldo actual
            cursor.execute("SELECT saldo FROM cuentas_bancarias WHERE numero_cuenta = %s", (cuenta_destino,))
            saldo_despues = cursor.fetchone()[0]
            saldo_antes = saldo_despues - monto

            transferencias.append({
                'tipo': 'deposito',
                'cuenta_origen': 'Banco Pingüino',
                'nombre_origen': 'Sistema',
                'cuenta_destino': cuenta_destino,
                'nombre_destino': nombre_destino,
                'saldo_antes': saldo_antes,
                'monto': +monto,
                'saldo_despues': saldo_despues,
                'fecha': fecha,
                'mensaje': ''
            })

    cursor.close()

    # Ordenar por fecha descendente
    transferencias.sort(key=lambda x: x['fecha'], reverse=True)
    return render_template("comprobantes.html", transferencias=transferencias)
