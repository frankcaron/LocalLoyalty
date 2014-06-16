import foursquare
import logging
import os

from flask import Flask
from flask import json
from flask import request
from flask import redirect
from flask import url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.templating import render_template
import sendgrid

from forms import SignupForm
from lcp_client import LCPClient
from models import User
from models import db
from sqlalchemy.sql.expression import desc


app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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
        except Exception as ex:
            logger.exception(ex)
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
    email = foursquare_user['user']['contact']['email']
    user = User.query.filter_by(email=email).order_by(desc(User.id)).first()
    if user is None:
        logger.info("User with email {} has not signed up".format(email))
        render_template('error.html')
    user.foursquare_id = foursquare_user['user']['id']
    user.save()
    return redirect(url_for('thanks'))


@app.route('/foursquare/push', methods=['POST'])
def handle_foursquare_push():
    checkin_info = request.form.getlist('checkin')[0]
    checkin_json = json.loads(checkin_info)
    logger.info('Recieved Push', checkin_json)
    venue_id = checkin_json['venue']['id']
    logger.info("Venue ID {}".format(venue_id))
    foursquare_user_id = checkin_json['user']['id']
    logger.info("User Checkin with id [{}]".format(foursquare_user_id))

    if venue_id not in app.config['ALLOWED_VENUES']:
        logger.info("Venue {} is not registered for this program".format(
            venue_id))
        return render_template('error.html')

    user = User.query.filter_by(
        foursquare_id=foursquare_user_id).order_by(desc(User.id)).first()
    # user = User.query.filter_by(foursquare_id=76462465).first()
    if not user:
        logger.info("User {} with id {} does not exist".format(
            user, foursquare_user_id))
        return render_template('error.html')
    if user.credit_url:
        logger.info("User {} with id {} has already redeemed".format(
            user.email, foursquare_user_id))
        return render_template('error.html')

    response = app.lcp_client.do_credit(user)
    user.credit_url = response['links']['self']['href']
    user.save()
    _send_email(user.email, response['amount'])
    return redirect(url_for('thanks'))


def _send_email(email, amount):
    sg = sendgrid.SendGridClient(
        app.config['SENDGRID_USERNAME'],
        app.config['SENDGRID_PASSWORD']
    )

    message = sendgrid.Mail()
    message.add_to(email)
    message.set_subject('You just received {} points!'.format(amount))
    message.set_html(
        render_template(
            'checkin_email.html',
            email=email,
            amount=amount
        )
    )
    message.set_text(
        render_template(
            'checkin_email.txt',
            email=email,
            amount=amount
        )
    )
    message.set_from(app.config['MAIL_DEFAULT_SENDER'])
    sg.send(message)

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

if __name__ == '__main__':
    _init_config(app)
    _init_db(app)
    _init_lcp_client(app)
    _init_foursquare_client(app)
    app.run(host='0.0.0.0')
