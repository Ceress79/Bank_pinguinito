from flask import Blueprint, render_template, request, redirect, url_for
from extensions import mysql

factura_bp = Blueprint('factura', __name__)

@factura_bp.route('/crear_factura', methods=['GET', 'POST'])
def crear_factura():
    if request.method == 'POST':
        id_usuario = request.form['id_usuario']
        monto = request.form['monto']
        concepto = request.form['concepto']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO factura (id_usuario, monto, concepto) VALUES (%s, %s, %s)",
                       (id_usuario, monto, concepto))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('factura.lista_facturas'))
    return render_template('crear_factura.html')


@factura_bp.route('/facturas')
def lista_facturas():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM factura")
    facturas = cursor.fetchall()
    cursor.close()
    return render_template('facturas.html', facturas=facturas)
