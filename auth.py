# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
from .sigaa import sigaa_lookup
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    #email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # sigaa login and user info extraction
    userinfo = sigaa_lookup(username, password)

    # verify login
    if userinfo == None:
        flash('Usuário/senha inválidos. Verifique as credenciais e tente novamente.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page
    # verify userinfo
    if not userinfo:
        flash("Problema na extração de dados do sigaa. Precisa da intervenção do desenvolvedor.")
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # get user from db and insert if not there yet
    user = User.query.filter_by(register=userinfo['register']).first()
    if user == None:
        new_user = User(register=userinfo['register'], name=userinfo['name'], association=userinfo['association'], function=userinfo['function'], key="", timestamp=datetime.now())
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
