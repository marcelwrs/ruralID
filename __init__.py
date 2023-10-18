# init.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
from flask_qrcode import QRcode
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from oauthlib.oauth2 import WebApplicationClient

# Configuration
RURALID_SECRET_KEY = os.environ.get("RURALID_SECRET_KEY", None) # Need to set this environment var to work
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None) # Need to set this environment var to work
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None) # Need to set this environment var to work
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")
# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    qrcode = QRcode(app)

    app.config['SECRET_KEY'] = RURALID_SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['REMEMBER_COOKIE_DURATION'] = 60
    app.config['PERMANENT_SESSION_LIFETIME'] = 60

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    print(client)

    from .models import User

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/ruralid')

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/ruralid')

    return app
