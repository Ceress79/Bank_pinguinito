from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import mysql
from datetime import datetime

prestamos_bp = Blueprint('prestamos', __name__)

@prestamos_bp.route('/ver_prestamos')
def listar_prestamos():
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT p.id, p.id_usuario, u.nombre_completo, p.cantidad, p.fecha_inicio, p.fecha_limite_pago, p.cuotas, p.garante FROM prestamos p JOIN user u ON p.id_usuario = u.cedula")
    prestamos = cursor.fetchall()
    cursor.close()

    # prestamos es lista de tuplas, pasar a lista de dict para el template
    prestamos_list = []
    for p in prestamos:
        prestamos_list.append({
            "id": p[0],
            "id_usuario": p[1],
            "nombre_usuario": p[2],
            "cantidad": float(p[3]),
            "fecha_inicio": p[4].strftime('%Y-%m-%d'),
            "fecha_limite": p[5].strftime('%Y-%m-%d'),
            "cuotas": p[6],
            "garante": p[7]
        })
    return render_template('prestamo_ver.html', prestamos=prestamos_list)

@prestamos_bp.route('/crear_prestamo', methods=['GET', 'POST'])
def crear_prestamo():
    conn = mysql.connection
    cursor = conn.cursor()
    # Obtener lista de usuarios para el select
    cursor.execute("SELECT cedula, nombre_completo FROM user")
    usuarios = cursor.fetchall()

    if request.method == 'POST':
        id_usuario = request.form.get('id_usuario')
        cantidad = request.form.get('cantidad')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_limite = request.form.get('fecha_limite')
        cuotas = request.form.get('cuotas')
        garante = request.form.get('garante')

        # Validar que todos los campos existan
        if not all([id_usuario, cantidad, fecha_inicio, fecha_limite, cuotas, garante]):
            flash("Todos los campos son obligatorios", "error")
            return render_template('prestamos_crear.html', usuarios=usuarios)

        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_limite_dt = datetime.strptime(fecha_limite, '%Y-%m-%d')
        except ValueError:
            flash("Formato de fecha inválido. Use YYYY-MM-DD", "error")
            return render_template('prestamos_crear.html', usuarios=usuarios)

        try:
            cursor.execute("""
                INSERT INTO prestamos (id_usuario, cantidad, fecha_inicio, fecha_limite_pago, cuotas, garante)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_usuario, cantidad, fecha_inicio_dt, fecha_limite_dt, cuotas, garante))
            conn.commit()
            flash("Préstamo creado correctamente", "success")
            return redirect(url_for('prestamos.listar_prestamos'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al crear préstamo: {str(e)}", "error")
            return render_template('prestamos_crear.html', usuarios=usuarios)
        finally:
            cursor.close()

    # GET
    cursor.close()
    return render_template('prestamos_crear.html', usuarios=usuarios)
