# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
#from flask_moment import Moment
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_log_request_id import RequestID, current_request_id
#from flask.ext.pagedown import PageDown
from config import app_release, IsBankperso, IsProvision, config

bootstrap = Bootstrap()
babel = Babel()
mail = Mail()
#moment = Moment()
db = SQLAlchemy()
#pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'basic' # 'strong'
login_manager.login_view = 'auth.login'

from .patches import *


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.register_error_handler(403, forbidden)

    bootstrap.init_app(app)
    babel.init_app(app)
    mail.init_app(app)
    #moment.init_app(app)
    db.init_app(app)

    login_manager.init_app(app)

    #pagedown.init_app(app)

    #if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #    from flask.ext.sslify import SSLify
    #    sslify = SSLify(app)

    RequestID(app)

    if IsBankperso:
        from .bankperso import bankperso as bankperso_blueprint
        app.register_blueprint(bankperso_blueprint)

        from .cards import cards as cards_blueprint
        app.register_blueprint(cards_blueprint)

        from .configurator import configurator as configurator_blueprint
        app.register_blueprint(configurator_blueprint)

        from .persostation import persostation as persostation_blueprint
        app.register_blueprint(persostation_blueprint)

    if IsProvision:
        from .calculator import calculator as calculator_blueprint
        app.register_blueprint(calculator_blueprint)

        from .catalog import catalog as catalog_blueprint
        app.register_blueprint(catalog_blueprint)

        from .provision import provision as provision_blueprint
        app.register_blueprint(provision_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .semaphore import semaphore as semaphore_blueprint
    app.register_blueprint(semaphore_blueprint, url_prefix='/semaphore')

    if IsProvision:
        from .api import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
