import os
from flask import Flask, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
from dotenv import load_dotenv
import contentful

db = SQLAlchemy()
login_manager = LoginManager()

# Load dotenv in the base root
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Create a Flask WSGI app and configure it using values from the module.
app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

# Initialize plugins
db.init_app(app)
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

# Initialize contentful client
contentfulClient = contentful.Client(os.getenv('CONTENTFUL_SPACE_ID'), os.getenv('CONTENTFUL_ACCESS_TOKEN'))

from app import views, models
from . models import User

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)



if os.getenv('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('website startup')
