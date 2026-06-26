from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["300 per minute"])


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    limiter.init_app(app)

    # Cabeceras de seguridad en todas las respuestas
    @app.after_request
    def set_security_headers(response: Response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Solo fuerza HTTPS si se despliega con certificado
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.odontologos import odontologos_bp
    from app.routes.trabajos import trabajos_bp
    from app.routes.pagos import pagos_bp
    from app.routes.inventario import inventario_bp
    from app.routes.reportes import reportes_bp
    from app.routes.portal import portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(odontologos_bp)
    app.register_blueprint(trabajos_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(portal_bp)

    return app
