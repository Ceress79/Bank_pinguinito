from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mysql
from datetime import datetime

prestamos_bp = Blueprint('prestamos', __name__)


@prestamos_bp.route('/ver_prestamos')
def listar_prestamos():
    if 'usuario' not in session or 'rol' not in session:
        flash("Debe iniciar sesión para ver sus préstamos", "error")
        return redirect(url_for('auth.login'))

    rol = session['rol']
    conn = mysql.connection
    cursor = conn.cursor()

    if rol == 'a':  # Administrador ve todos los préstamos
        cursor.execute("""
            SELECT p.id, p.id_usuario, u.nombre_completo, p.cantidad, p.fecha_inicio, p.fecha_limite_pago, 
                   p.cuotas, p.garante, p.estatus_solicitud, p.estado, p.motivo
            FROM prestamos p 
            JOIN user u ON p.id_usuario = u.cedula
            ORDER BY p.creado_en DESC
        """)
    else:
        usuario_correo = session['usuario']  # asumimos que 'usuario' es el correo
        cursor.execute("""
            SELECT p.id, p.id_usuario, u.nombre_completo, p.cantidad, p.fecha_inicio, p.fecha_limite_pago, 
                   p.cuotas, p.garante, p.estatus_solicitud, p.estado, p.motivo
            FROM prestamos p 
            JOIN user u ON p.id_usuario = u.cedula
            WHERE u.correo = %s
            ORDER BY p.creado_en DESC
        """, (usuario_correo,))

    prestamos = cursor.fetchall()
    cursor.close()

    prestamos_list = []
    for p in prestamos:
        prestamos_list.append({
            "id": p[0],
            "id_usuario": p[1],
            "nombre_usuario": p[2],
            "cantidad": float(p[3]) if p[3] else 0,
            "fecha_inicio": p[4].strftime('%Y-%m-%d') if p[4] else '',
            "fecha_limite": p[5].strftime('%Y-%m-%d') if p[5] else '',
            "cuotas": p[6],
            "garante": p[7],
            "estatus_solicitud": p[8],
            "estado": p[9],
            "motivo": p[10] or ""
        })

    return render_template('prestamo_ver.html', prestamos=prestamos_list)





@prestamos_bp.route('/crear_prestamo', methods=['GET', 'POST'])
def crear_prestamo():
    if 'usuario' not in session:
        flash("Debe iniciar sesión para solicitar un préstamo.", "error")
        return redirect(url_for('auth.login'))  # Ajusta si tu ruta de login es diferente

    if request.method == 'POST':
        correo_usuario = session.get('usuario')
        if not correo_usuario:
            flash("Debe iniciar sesión para solicitar un préstamo.", "error")
            return redirect(url_for('auth.login'))

        cursor = mysql.connection.cursor()

        # Buscar la cedula del usuario usando el correo almacenado en sesión
        cursor.execute("SELECT cedula FROM user WHERE correo = %s", (correo_usuario,))
        result = cursor.fetchone()
        if not result:
            flash("Usuario no encontrado.", "error")
            cursor.close()
            return redirect(url_for('auth.login'))
        cedula_usuario = result[0]

        # Obtener datos del formulario
        id_admin = request.form.get('id_admin')
        cantidad = request.form.get('cantidad')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_limite = request.form.get('fecha_limite')
        cuotas = request.form.get('cuotas')
        garante = request.form.get('garante')
        motivo = request.form.get('motivo')

        # Validar campos obligatorios
        if not cantidad or not fecha_inicio or not fecha_limite or not cuotas:
            flash("Por favor, complete todos los campos obligatorios.", "error")
            cursor.close()
            return redirect(url_for('prestamos.crear_prestamo'))

        try:
            cursor.execute("""
                INSERT INTO prestamos 
                (id_usuario, cantidad, fecha_inicio, fecha_limite_pago, cuotas, garante, motivo, estado, estatus_solicitud, tasa_interes, monto_pagado, fecha_ultimo_pago, creado_en)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'activo', 'pendiente', 0, 0, NULL, NOW())
            """, (cedula_usuario, cantidad, fecha_inicio, fecha_limite, cuotas, garante, motivo))
            mysql.connection.commit()
            flash('Préstamo solicitado correctamente.', "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error al solicitar préstamo: {str(e)}", "error")
        finally:
            cursor.close()

        return redirect(url_for('prestamos.listar_prestamos'))

    # Método GET: mostrar admins para seleccionar en el formulario
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT cedula, nombre_completo, correo FROM user WHERE rol = 'a'")
    admins = cursor.fetchall()
    cursor.close()

    return render_template('prestamos_crear.html', admins=admins)




@prestamos_bp.route('/solicitar_prestamo', methods=['POST'])
def solicitar_prestamo():
    if 'usuario' not in session or not session['usuario']:
        flash("Debe iniciar sesión para solicitar un préstamo", "error")
        return redirect(url_for('main.login'))

    cedula = session['usuario']

    cantidad = request.form.get('cantidad')
    motivo = request.form.get('motivo')

    if not cantidad or not motivo:
        flash("Cantidad y motivo son obligatorios", "error")
        return redirect(url_for('main.menu'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO prestamos (id_usuario, cantidad, motivo, estatus_solicitud)
            VALUES (%s, %s, %s, 'pendiente')
        """, (cedula, cantidad, motivo))
        mysql.connection.commit()
        flash("Solicitud enviada", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al enviar solicitud: {str(e)}", "error")
    finally:
        cursor.close()

    return redirect(url_for('main.menu'))


@prestamos_bp.route('/aceptar_prestamo/', methods=['POST'])
def aceptar_prestamo():
    id_prestamo = request.form.get('id_prestamo')
    if not id_prestamo:
        flash("ID de préstamo no proporcionado", "error")
        return redirect(url_for('prestamos.listar_prestamos'))

    conn = mysql.connection
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, cantidad FROM prestamos WHERE id = %s", (id_prestamo,))
        prestamo = cursor.fetchone()
        if prestamo:
            id_usuario, cantidad = prestamo
            cursor.execute("UPDATE prestamos SET estatus_solicitud = 'aceptado' WHERE id = %s", (id_prestamo,))

            cursor.execute("""
                SELECT numero_cuenta FROM cuentas_bancarias WHERE cedula_usuario = %s LIMIT 1
            """, (id_usuario,))
            cuenta = cursor.fetchone()

            if cuenta:
                numero_cuenta = cuenta[0]
                cursor.execute("""
                    INSERT INTO deposito (num_cuenta_destino, monto) VALUES (%s, %s)
                """, (numero_cuenta, cantidad))
                cursor.execute("""
                    UPDATE cuentas_bancarias SET saldo = saldo + %s WHERE numero_cuenta = %s
                """, (cantidad, numero_cuenta))
                conn.commit()
                flash("Préstamo aceptado y depósito realizado", "success")
            else:
                flash("Usuario no tiene cuenta bancaria registrada", "error")
                conn.rollback()
        else:
            flash("Préstamo no encontrado", "error")
            conn.rollback()
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
    return redirect(url_for('depositos.lista_depositos'))


@prestamos_bp.route('/rechazar_prestamo/', methods=['POST'])
def rechazar_prestamo():
    id_prestamo = request.form.get('id_prestamo')
    if not id_prestamo:
        flash("ID de préstamo no proporcionado", "error")
        return redirect(url_for('prestamos.listar_prestamos'))

    conn = mysql.connection
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE prestamos SET estatus_solicitud = 'rechazado' WHERE id = %s", (id_prestamo,))
        conn.commit()
        flash("Préstamo rechazado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al rechazar préstamo: {str(e)}", "error")
    finally:
        cursor.close()
    return redirect(url_for('depositos.lista_depositos'))
