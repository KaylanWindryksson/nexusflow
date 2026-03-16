from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.clientes import clientes_bp
    from app.routes.servicos import servicos_bp
    from app.routes.orcamentos import orcamentos_bp
    from app.routes.agenda import agenda_bp
    from app.routes.relatorios import relatorios_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(orcamentos_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _seed_default_user()

    return app

def _seed_default_user():
    from app.models import Usuario
    from werkzeug.security import generate_password_hash
    if not Usuario.query.filter_by(email='admin@anima.com').first():
        u = Usuario(nome='Admin', email='admin@anima.com',
                    senha=generate_password_hash('anima123'), is_admin=True)
        db.session.add(u)
        db.session.commit()