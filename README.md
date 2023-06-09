# ruralID

In any linux machine with python3 support:

    python3 -m venv ruralid
    source ruralid/bin/activate
    pip install flask, flask_sqlalchemy, flask_login, flask_qrcode, gunicorn, bs4, requests

    git clone https://github.com/marcelwrs/ruralID.git

    gunicorn -w 4 -b 0.0.0.0:8080 "ruralID:create_app()"
