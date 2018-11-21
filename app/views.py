import functools
import re
from unidecode import unidecode
import cloudinary.uploader

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

def template_og_metadata(metadata):
    return {
        "og:type": "website",
        "og:url": metadata["url"],
        "og:title": metadata["title"],
        "og:description": metadata["description"],
        "og:image": metadata["img"]
    }

def template_twitter_metadata(metadata):
    return {
        "twitter:card": "summary_large_image",
        "twitter:url": metadata["url"],
        "twitter:title": metadata["title"],
        "twitter:description": metadata["description"]
    }

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
    metaconfig = {
        'title': "Simon Hunter | Photography",
        'url': "http://www.simonhunter.co/photography.html",
        'description': "I'm Simon Hunter, a product manager working to develop the future of healthcare, an amateur photographer and long-suffering Newcastle United fan. This is my site.",
        'img': "https://res.cloudinary.com/monsk/image/upload/c_scale,h_1600/v1542689051/Hawaii/20181003-DSC_7691.jpg"
    }
    return render_template(
        "photography.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

# @app.route('/projects/')
# def projects():
#     query = db.session.query(BlogEntry).filter(BlogEntry.published == True).order_by(BlogEntry.timestamp.desc())
#     return render_template('projects.html', object_list = query)

@app.route('/data/create/', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):

            # Upload cover photo
            cover_photo = request.files['cover_photo']
            uploaded_img = cloudinary.uploader.upload(
                cover_photo
            )
            image_filename = uploaded_img["public_id"]

            entry = BlogEntry(
                title=request.form['title'],
                subtitle=request.form['subtitle'],
                content=request.form['content'],
                published=request.form.get('published') or False,
                slug=slugify(request.form.get('title')),
                image_filename = image_filename
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
    query = db.session.query(BlogEntry).filter(BlogEntry.published == False).order_by(BlogEntry.timestamp.desc())
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

            # Upload cover photo
            if request.files.get('cover_photo'):
                cover_photo = request.files['cover_photo']
                uploaded_img = cloudinary.uploader.upload(cover_photo)
                image_filename = uploaded_img["public_id"]
                entry.image_filename = image_filename

            entry.title = request.form['title']
            entry.slug = slugify(request.form.get('title'))
            entry.subtitle = request.form['subtitle']
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

@app.route('/delete/<slug>', methods=['POST'])
@login_required
def delete_entry(slug):
    if request.method == 'POST':
        db.session.query(BlogEntry).filter(BlogEntry.slug == slug).delete()
        db.session.commit()
        flash('Entry was deleted')
    return redirect(url_for('drafts'))

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/photography/national_parks')
def national_parks():
    metaconfig = {
        'title': "Simon Hunter | US National Parks",
        'url': "http://www.simonhunter.co/photography/national_parks.html",
        'description': "Photos taken during a week spent on a National Parks tour of the American Southwest.",
        'img': "http://res.cloudinary.com/monsk/image/upload/c_scale,h_1600/v1513640291/DSC_5505_fuagnr.jpg"
    }
    return render_template(
        "nationalparks.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/photography/arctic')
def arctic():
    metaconfig = {
        'title': "Simon Hunter | Svalbard",
        'url': "http://www.simonhunter.co/photography/arctic.html",
        'description': "Photos taken on a circumnavigation of Svalbard in the arctic archipelago of Spitsbergen.",
        'img': "http://res.cloudinary.com/monsk/image/upload/v1470589280/Svalbard/DSC_2125.jpg"
    }
    return render_template(
        "arctic.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/photography/night_sky')
def night_sky():
  return render_template("night_sky.html")

@app.route('/photography/california')
def california():
    metaconfig = {
        'title': "Simon Hunter | California",
        'url': "http://www.simonhunter.co/photography.html",
        'description': "Photos taken out and about in The Golden State",
        'img': "https://res.cloudinary.com/monsk/image/upload/v1538024144/DSC_7526-2_elq4xn.jpg"
    }
    return render_template(
        "california.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/photography/hawaii')
def hawaii():
    metaconfig = {
        'title': "Simon Hunter | Hawaii",
        'url': "http://www.simonhunter.co/photography/hawaii.html",
        'description': "Photos taken on a 10 day vacation to Hawaii, Big Island",
        'img': "https://res.cloudinary.com/monsk/image/upload/c_scale,h_1600/v1542689051/Hawaii/20181003-DSC_7691.jpg"
    }
    return render_template(
        "hawaii.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/pmuk/privacy_policy')
def privacy_policy():
    return render_template("privacy_policy.html")
