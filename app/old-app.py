import datetime
import functools
import os
import re
import urllib

from flask import (Flask, flash, Markup, redirect, render_template, request,
                   Response, session, url_for)

from flask_heroku import Heroku

from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from BeautifulSoup import BeautifulSoup
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from peewee import *
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from playhouse.sqlite_ext import *

# Blog configuration values.


APP_DIR = os.path.dirname(os.path.realpath(__file__))


if 'HEROKU' in os.environ:
    import urlparse, psycopg2
    urlparse.uses_netloc.append('postgres')
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    DATABASE = {
        'engine': 'peewee.PostgresqlDatabase',
        'name': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port,
    }
else:
    # The playhouse.flask_utils.FlaskDB object accepts database URL configuration.
    DATABASE = 'sqliteext:///%s' % os.path.join(APP_DIR, 'blog.db')
    DEBUG = False

# # FlaskDB is a wrapper for a peewee database that sets up pre/post-request
# # hooks for managing database connections.
# flask_db = FlaskDB(app)
#
# # The `database` is the actual peewee database, as opposed to flask_db which is
# # the wrapper.
# database = flask_db.database

# Configure micawber with the default OEmbed providers (YouTube, Flickr, etc).
# We'll use a simple in-memory cache so that multiple requests for the same
# video don't require multiple network requests.
oembed_providers = bootstrap_basic(OEmbedCache())




def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner



# def main():
#     database.create_tables([BlogEntry, FTSEntry], safe=True)
#     app.run(debug=True)
#
# if __name__ == '__main__':
#     main()
