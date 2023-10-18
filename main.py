# main.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from .models import User
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    if current_user.key == "" or (datetime.now() - current_user.timestamp).total_seconds() >= 10:
        key = generate_password_hash(current_user.register+current_user.name+current_user.relationship+str(datetime.now()))
        user = User.query.filter_by(register=current_user.register).update(dict(key=key, timestamp=datetime.now()))
        db.session.commit()
        print(key)
    return render_template('profile.html', name=current_user.name.split(' ')[0], qrdata=current_user.key)
    
@main.route('/validateqr', methods=['POST'])
#@login_required
def validateqr():
    qrdata = request.form.get('qrdata')
    user = User.query.filter(User.key == qrdata, User.timestamp >= (datetime.now() - timedelta(seconds=10))).first()
    if user == None:
        return jsonify({"register": -1,
            "name": '',
            "function": '',
            "relationship": ''})
    else:
        return jsonify({"register": user.register,
            "name": user.name,
            "function": user.function,
            "relationship": user.relationship})
