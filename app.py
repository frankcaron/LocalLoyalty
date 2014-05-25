import logging
import os

import foursquare
from flask import Flask
from flask import json
from flask import request
from flask import redirect
from flask import url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.templating import render_template
from lcp_client import LCPClient
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail

from forms import SignupForm
from models import User
from models import db
from flask_mail import Message


app = Flask(__name__)
mail = Mail()

logger = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(
            form.first_name.data,
            form.last_name.data,
            form.membership_number.data,
            form.email.data
        )
        mv_response = app.lcp_client.validate_member(user)
        user.mv_url = mv_response['links']['self']['href']
        try:
            user.save()
        except IntegrityError as ex:
            logger.info('User already registered', ex)
            return render_template('error.html')
        return redirect(app.foursquare_client.oauth.auth_url())

    return render_template('signup.html', form=form)


@app.route('/thanks', methods=['GET'])
def thanks():
    return render_template('thanks.html')


@app.route('/foursquare/oauth', methods=['GET'])
def foursquare_oauth_redirect():
    foursquare_code = request.args.get('code', None)
    if not foursquare_code:
        return render_template('error.html')
    access_token = app.foursquare_client.oauth.get_token(foursquare_code)
    app.foursquare_client.set_access_token(access_token)
    foursquare_user = app.foursquare_client.users()
    user = User.query.filter_by(email=foursquare_user['user']['contact']['email']).first()
    if user is None:
        logger.info("emails are different!")
        render_template('error.html')
    user.foursquare_id = foursquare_user['user']['id']
    user.save()
    return redirect(url_for('thanks'))


@app.route('/foursquare/push', methods=['POST'])
def handle_foursquare_push():
    checkin_info = request.form.getlist('checkin')
    checkin_json_raw = checkin_info[0]
    checkin_json = json.loads(checkin_json_raw)
    if checkin_json['venue']['id'] in app.config['ALLOWED_VENUES']:
        # user = User.query.filter_by(foursquare_id=76462465).first()
        user = User.query.filter_by(foursquare_id=checkin_json['user']['id']).first()
        if user and user.credit_url is None:
            response = app.lcp_client.do_credit(user)
            user.credit_url = response['links']['self']['href']
            user.save()
            _send_email(user.email, response['amount'])
            return redirect(url_for('thanks'))

    return render_template('error.html')


def _send_email(email, amount):
    message = Message()
    message.subject = 'You just received {} points!'.format(amount)
    message.recipients = [email]
    message.body = render_template(
        'checkin_email.txt',
        email=email,
        amount=amount)
    message.html = render_template(
        'checkin_email.html',
        email=email,
        amount=amount)
    mail.send(message)

#--- Initializations

def _init_foursquare_client(app):
    app.foursquare_client = foursquare.Foursquare(
        client_id=app.config['FOURSQUARE_MAC_KEY_IDENTIFIER'],
        client_secret=app.config['FOURSQUARE_MAC_KEY_SECRET'],
        redirect_uri=app.config['FOURSQUARE_REDIRECT_ACCEPT_URL'])

def _init_lcp_client(app):
    app.lcp_client = LCPClient(app)

def _init_db(app):
    db.app = app
    db.init_app(app)
    db.create_all()

def _init_ngrok_url_config(app):
    ngrok_url = os.environ.get('NGROK_URL', None)
    if ngrok_url is None:
        raise ValueError('You need to set the NGROK_URL as an environment variable')
    oauth_redirect_url = app.config['FOURSQUARE_REDIRECT_ACCEPT_URL']
    oauth_redirect_url = oauth_redirect_url.format(ngrok_url=ngrok_url)
    app.config['FOURSQUARE_REDIRECT_ACCEPT_URL'] = oauth_redirect_url

def _init_config(app):
    config = os.environ.get('CONFIG', None)
    if config is None:
        raise ValueError('You need to set CONFIG in your environment variable to point to a file')
    app.config.from_envvar('CONFIG')
    _init_ngrok_url_config(app)

def _init_mail(app):
    mail.init_app(app)

if __name__ == '__main__':
    _init_config(app)
    _init_db(app)
    _init_lcp_client(app)
    _init_foursquare_client(app)
    _init_mail(app)
    app.run(host='0.0.0.0')
