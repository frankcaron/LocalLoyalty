import os
import logging

from flask import Flask
from flask import request
from flask import json
from flask.ext.sqlalchemy import SQLAlchemy
from flask.helpers import url_for
from flask.templating import render_template
import foursquare
from werkzeug.utils import redirect

from forms import SignupForm
from models import db
from models import User
from lcp_client import LCPClient
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

logger = logging.getLogger(__name__)

config = os.environ.get('CONFIG', None)
if config is None:
    raise ValueError('You need to set CONFIG in your environment variable to point to a file')
app.config.from_envvar('CONFIG')

db.app = app
db.init_app(app)
db.create_all()

lcp_client = LCPClient(app)

foursquare_client = foursquare.Foursquare(
    client_id=app.config['FOURSQUARE_MAC_KEY_IDENTIFIER'],
    client_secret=app.config['FOURSQUARE_MAC_KEY_SECRET'],
    redirect_uri=app.config['FOURSQUARE_REDIRECT_ACCEPT_URL']
)


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
        mv_response = lcp_client.validate_member(user)
        user.mv_url = mv_response['links']['self']['href']
        try:
            user.save()
        except IntegrityError as ex:
            logger.info('User already registered', ex)
            return render_template('error.html')
        return redirect(foursquare_client.oauth.auth_url())

    return render_template('signup.html', form=form)


@app.route('/foursquare/oauth', methods=['GET'])
def foursquare_oauth_redirect():
    foursquare_code = request.args.get('code')
    access_token = foursquare_client.oauth.get_token(foursquare_code)
    foursquare_client.set_access_token(access_token)
    foursquare_user = foursquare_client.users()
    user = User.query.filter_by(email=foursquare_user['user']['contact']['email']).first()
    if user is None:
        logger.info("emails are different!")
        render_template('error.html')
    user.foursquare_id = foursquare_user['user']['id']
    user.save()
    return render_template('thanks.html')


@app.route('/foursquare/push', methods=['POST'])
def handle_foursquare_push():
    checkin_info = request.form.getlist('checkin')
    checkin_json_raw = checkin_info[0]
    checkin_json = json.loads(checkin_json_raw)
    user = User.query.filter_by(foursquare_id=checkin_json['user']['id']).first()
    if user and user.credit_url is None:
        response = lcp_client.do_credit(user)
        user.credit_url = response['links']['self']['href']
        user.save()
        return render_template('thanks.html')

    return render_template('error.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
