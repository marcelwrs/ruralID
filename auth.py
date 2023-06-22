# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
from .sigaa import sigaa_lookup
from datetime import datetime
import json

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    # render relationship page
    #if 'relations' in request.args:
    #    relations = json.loads(request.args['relations'])
    if 'reloptions' in session:
        reloptions = list(session['reloptions'].keys())
        print(reloptions)
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
        #reloption = session['reloptions']
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
        print("userinfo: ", userinfo)
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
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    #admin = request.form.get('admin')
    
    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    #new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), admin=admin)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
