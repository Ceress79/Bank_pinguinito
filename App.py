from flask import Flask
from config import Config
from extensions import mysql
from controllers.auth import auth_bp
from controllers.cuentas import cuentas_bp
from controllers.factura import factura_bp
from controllers.transferencias import transferencias_bp
 
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(cuentas_bp)
    app.register_blueprint(factura_bp)
    app.register_blueprint(transferencias_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=3000, debug=True)
