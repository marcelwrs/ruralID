# main.py

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from . import current_keys

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    key = generate_password_hash(current_user.name+str(datetime.now()), method='sha256')
    current_keys[current_user.name] = key
    print(key)
    return render_template('profile.html', name=current_user.name, qrdata=key)
    
@main.route('/validateqr', methods=['POST'])
@login_required
def validateqr():
    qrdata = request.form.get('qrdata')
    print(qrdata)
    print(current_keys.values())
    if qrdata in current_keys.values():
        return "True"
    else:
        return "False"