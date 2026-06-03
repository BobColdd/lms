from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from models import db, User
from config import config

login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.student import student_bp
    from routes.main import main_bp
    from routes.certificates import cert_bp
    from routes.instructor import instructor_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(cert_bp, url_prefix='/admin')
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(main_bp)

    # Inject config into templates
    @app.context_processor
    def inject_site_info():
        return {
            'SCHOOL_NAME': app.config['SCHOOL_NAME'],
            'SCHOOL_LOCATION': app.config['SCHOOL_LOCATION'],
            'SCHOOL_EMAIL': app.config['SCHOOL_EMAIL'],
            'SCHOOL_PHONE': app.config['SCHOOL_PHONE'],
        }

    return app
