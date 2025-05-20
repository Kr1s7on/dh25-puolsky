import os

from flask import Flask
from flask_assets import Environment
from flask_bootstrap import Bootstrap5
from flask_compress import Compress
from flask_login import LoginManager
from flask_mail import Mail
from flask_rq import RQ
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from app.assets import app_css, app_js, vendor_css, vendor_js
from config import config as Config

basedir = os.path.abspath(os.path.dirname(__file__))

mail = Mail()
db = SQLAlchemy()
csrf = CSRFProtect()
compress = Compress()
bootstrap = Bootstrap5()

# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'account.login'


def create_app(config):
    app = Flask(__name__)
    config_name = config

    if not isinstance(config, str):
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app.config.from_object(Config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # not using sqlalchemy event system, hence disabling it

    Config[config_name].init_app(app)

    # Set up extensions
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    bootstrap.init_app(app)
    RQ(app)

    # Register Jinja template functions
    from .utils import register_template_utils
    register_template_utils(app)
    
    # Additional template utils for path resolution
    from .template_utils import init_template_utils
    init_template_utils(app)

    # Set up asset pipeline
    assets_env = Environment(app)
    dirs = ['assets/styles', 'assets/scripts']
    for path in dirs:
        assets_env.append_path(os.path.join(basedir, path))
    assets_env.url_expire = True

    assets_env.register('app_css', app_css)
    assets_env.register('app_js', app_js)
    assets_env.register('vendor_css', vendor_css)
    assets_env.register('vendor_js', vendor_js)

    # Configure SSL if platform supports it
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        SSLify(app)

    # Initialize tasks module
    from .tasks import init_app as init_tasks
    init_tasks(app)
    
    # Create app blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from .inventory import inventory as inventory_blueprint
    app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
    
    from .usage import usage as usage_blueprint
    app.register_blueprint(usage_blueprint, url_prefix='/usage')
    
    from .notifications import notifications as notifications_blueprint
    app.register_blueprint(notifications_blueprint, url_prefix='/notifications')
    
    from .chatbot import chatbot as chatbot_blueprint
    app.register_blueprint(chatbot_blueprint, url_prefix='/chatbot')
    
    from .quick_actions import quick_actions as quick_actions_blueprint
    app.register_blueprint(quick_actions_blueprint, url_prefix='/quick-actions')
    
    from .reports import reports as reports_blueprint
    app.register_blueprint(reports_blueprint, url_prefix='/reports')
    
    from .main.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
