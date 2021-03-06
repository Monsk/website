import os
import cloudinary
basedir = os.path.abspath(os.path.dirname(__file__))

# This is used by micawber, which will attempt to generate rich media
# embedded objects with maxwidth=800.
SITE_WIDTH = 800

if os.getenv('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = ('sqlite:///' + os.path.join(basedir, 'app.db') +
                               '?check_same_thread=False')
else:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

cloudinary.config(
    cloud_name = "monsk",
    api_key = "551158294957374",
    api_secret = "_cQkUqesUzbKWM7b26LJUpp1mlc"
)

# OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
