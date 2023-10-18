# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, user_logged_out
from .models import User
from . import db, client, GOOGLE_DISCOVERY_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from .sigaa import sigaa_lookup
from datetime import datetime, timedelta
import json
import requests

auth = Blueprint('auth', __name__)

# helper to retrieve google auth uri
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@auth.route("/glogin")
def glogin():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri='https://www.dcc.ufrrj.br' + url_for('auth.callback'),
        #redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@auth.route("/glogin/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    print(request.url, request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url='https://www.dcc.ufrrj.br' + url_for('auth.callback'),
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    print(json.dumps(token_response.json()))
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    print(unique_id, users_name, users_email)
    print(userinfo_response.json())
    # Create a user in your db with the information provided
    # by Google
    #user = User(
    #    id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    #)

    # Doesn't exist? Add it to the database.
    #if not User.get(unique_id):
    #    User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    #login_user(user)

    # Send user back to homepage
    return redirect(url_for("main.index"))

@auth.route('/login')
def login():
    # include relationship options if needed
    if 'reloptions' in session:
        reloptions = list(session['reloptions'].keys())
        #del session['reloptions']
        return render_template('login.html', reloptions=reloptions)

    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    option = request.form.get('reloption')
    if option != None:
        reloption = session['reloptions'][option]
    else:
        reloption = None

    # sigaa login and user info extraction
    status, userinfo = sigaa_lookup(username, password, reloption)

    # verify login
    if status == None:
        flash('Usuário/senha inválidos. Verifique as credenciais e tente novamente.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page
    # verify userinfo
    if status == 'error':
        flash("Problema na extração de dados do sigaa. Precisa da intervenção do desenvolvedor.")
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page
    # user need to select relationship first
    if status == 'relationship':
        #print("userinfo: ", userinfo)
        reloptions = {}
        for option in userinfo:
            reloptions[option[0]] = option[1]
        session['reloptions'] = reloptions
        return redirect(url_for('auth.login'))#, relations=json.dumps(userinfo)))

    # get user from db and insert if not there yet
    user = User.query.filter_by(register=userinfo['register']).first()
    if user == None:
        new_user = User(register=userinfo['register'], name=userinfo['name'], relationship=userinfo['relationship'], function=userinfo['function'], key="", timestamp=datetime.now())
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(register=userinfo['register']).first()

    # if the above checks pass, then we know the user has the right credentials
    login_user(user, remember=remember, duration=timedelta(minutes=1))
    session.permanent = remember
    return redirect(url_for('main.profile'))

@auth.route('/logout')
@login_required
def logout():
    User.query.filter_by(register=current_user.register).delete()
    logout_user()
    return redirect(url_for('main.index'))
