from flask import Flask
from config import Config
from extensions import mysql, mail
from controllers.auth import auth_bp
from controllers.cuentas import cuentas_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuración manual si no está en Config (opcional)
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = '12345'
    app.config['MYSQL_DB'] = 'banco_pinguino'

    app.secret_key = 'mysecretkey'

    # Inicializar extensiones
    mysql.init_app(app)
    mail.init_app(app)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(cuentas_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=3000, debug=True)
