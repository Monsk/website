import functools
import re
from unidecode import unidecode

from sqlalchemy.orm import exc
from werkzeug.exceptions import abort

from flask import (Flask, flash, Markup, redirect, render_template, request,
                   Response, session, url_for)

from app import app, db
from .models import BlogEntry


def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner

def get_object_or_404(model, *criterion):
    try:
        return db.session.query(model).filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))

@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    # We'll use this template filter in the pagination include. This filter
    # will take the current URL and allow us to preserve the arguments in the
    # querystring while replacing any that we need to overwrite. For instance
    # if your URL is /?q=search+query&page=2 and we want to preserve the search
    # term but make a link to page 3, this filter will allow us to do that.
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)

@app.errorhandler(404)
def not_found(exc):
    return render_template('404.html'), 404


@app.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        # TODO: If using a one-way hash, you would also hash the user-submitted
        # password and do the comparison on the hashed versions.
        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            flash('You are now logged in.', 'success')
            return redirect(next_url or url_for('index'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)

@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')

@app.route('/')
def index():
  return render_template("index.html")

@app.route('/data/')
def data():
    query = db.session.query(BlogEntry).filter(BlogEntry.published == 1).order_by(BlogEntry.timestamp.desc())
    return render_template('data.html', object_list = query)


@app.route('/data/create/', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry = BlogEntry(
                title=request.form['title'],
                subtitle=request.form['subtitle'],
                content=request.form['content'],
                published=request.form.get('published') or False,
                slug=slugify(request.form.get('title'))
                )

            print(slugify(request.form.get('title')))

            db.session.add(entry)
            db.session.commit()

            flash('Entry created successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.', 'danger')
    return render_template('create.html')

@app.route('/data/drafts/')
@login_required
def drafts():
    query = db.session.query(BlogEntry).filter(BlogEntry.published != 1).order_by(BlogEntry.timestamp.desc())
    return render_template('data.html', object_list=query)

@app.route('/<slug>/')
def detail(slug):
    print(slug)
    if session.get('logged_in'):
        query = db.session.query(BlogEntry)
    else:
        query = db.session.query(BlogEntry.published)
    entry = get_object_or_404(BlogEntry, BlogEntry.slug == slug)
    return render_template('detail.html', entry=entry)

@app.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(BlogEntry, BlogEntry.slug == slug)
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry.title = request.form['title']
            entry.content = request.form['content']
            entry.published = request.form.get('published') or False

            db.session.add(entry)
            db.session.commit()

            flash('Entry saved successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.', 'danger')

    return render_template('edit.html', entry=entry)


@app.route('/photography/')
def photography():
  return render_template("photography.html")
