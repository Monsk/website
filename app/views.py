import functools
import re
import json
from unidecode import unidecode
import cloudinary.uploader
from flask import (
    Flask, 
    flash, 
    Markup, 
    redirect, 
    render_template, 
    request,
    Response, 
    session, 
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import requests
# from sqlalchemy.orm import exc
from sqlalchemy.orm import exc
from werkzeug.exceptions import abort
from rich_text_renderer import RichTextRenderer

from app import app, db, client, contentfulClient
from .models import BlogEntry, User

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

def get_object_or_404(model, *criterion):
    try:
        return db.session.query(model).filter(*criterion).one()
    except (exc.NoResultFound, exc.MultipleResultsFound):
        abort(404)

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

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
        "twitter:description": metadata["description"],
        "twitter:img": metadata["img"]
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

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    print(code)

        # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database. Commented to prevent sign-ups
    # if not User.get(unique_id):
    #     try:
    #         db.session.add(user)
    #         db.session.commit()
    #     except exc.IntegrityError as e:
    #         db.session().rollback()
    #         print(e)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

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

@app.route('/blog/')
def blog():
    entries = contentfulClient.entries()
    return render_template('blog.html', entries = entries)

@app.route('/blog/<slug>/')
def detail(slug):
    renderer = RichTextRenderer()
    searchResult = contentfulClient.entries({'content_type': 'blogPost','fields.slug': slug})
    entry = searchResult[0] if len(searchResult) > 0 else abort(404)
    
    return render_template('detail.html', renderer=renderer, entry=entry)

@app.route('/about/')
def about():
    metaconfig = {
        'title': "Simon Hunter | About",
        'url': "http://www.simonhunter.co/about.html",
        'description': "Director of Product at Hinge Health where we develop the future of healthcare delivery.",
        'img': "/static/img/me.jpg"
    }
    return render_template(
        "about.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/photography/national_parks')
def national_parks():
    metaconfig = {
        'title': "Simon Hunter | US National Parks",
        'url': "http://www.simonhunter.co/photography/national_parks.html",
        'description': "Photos taken during a week spent on a National Parks tour of the American Southwest.",
        'img': "http://res.cloudinary.com/monsk/image/upload/c_scale,h_400/v1513640291/DSC_5505_fuagnr.jpg"
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
        'img': "https://res.cloudinary.com/monsk/image/upload/c_scale,h_400/v1542689051/Hawaii/20181003-DSC_7691.jpg"
    }
    return render_template(
        "hawaii.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/photography/vancouver_island')
def vancouver_island():
    metaconfig = {
        'title': "Simon Hunter | Vancouver Island",
        'url': "http://www.simonhunter.co/photography/vancouver_island.html",
        'description': "Photos taken on a 10 day vacation to Vancouver Island",
        'img': "https://res.cloudinary.com/monsk/image/upload/c_scale,h_400/v1564355825/Vancouver%20Island/DSC_9171.jpg"
    }
    return render_template(
        "vancouver.html",
        og=template_og_metadata(metaconfig),
        twitter=template_twitter_metadata(metaconfig)
        )

@app.route('/pmuk/privacy_policy')
def privacy_policy():
    return render_template("privacy_policy.html")

