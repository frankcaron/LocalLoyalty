import os

from flask import Flask
from flask import request
from flask import json
from flask.ext.sqlalchemy import SQLAlchemy
from flask.helpers import url_for
from flask.templating import render_template
import foursquare
from pylcp.api import Client
from werkzeug.utils import redirect

from forms import SignupForm
from models import db
from models import User


app = Flask(__name__)
config = os.environ.get('CONFIG', None)
if config is None:
    raise ValueError('You need to set CONFIG in your environment variable to point to a file')
app.config.from_envvar('CONFIG')
db.app = app
db.init_app(app)
db.create_all()


lcp_client = Client(
    app.config['LCP_URL'],
    app.config['LCP_MAC_KEY_IDENTIFIER'],
    app.config['LCP_MAC_KEY_SECRET']
)

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

        mv_response = _validate_member(user)
        user.mv_url = mv_response['links']['self']['href']
        db.session.add(user)
        db.session.commit()

        return _auth_with_foursquare()

    return render_template('signup.html', form=form)


@app.route('/foursquare/oauth', methods=['GET'])
def foursquare_oauth_redirect():
    foursquare_code = request.args.get('code')
    access_token = foursquare_client.oauth.get_token(foursquare_code)
    foursquare_client.set_access_token(access_token)
    foursquare_user = foursquare_client.users()

    app_user = User.query.filter_by(email=foursquare_user['user']['contact']['email']).first()
    app_user.foursquare_id = foursquare_user['user']['id']
    db.session.add(app_user)
    db.session.commit()
    return redirect(url_for('thanks'))


@app.route('/foursquare/push', methods=['POST'])
def handle_foursquare_push():

    # Capture the request body raw
    # and grab the check in information
    checkin_info = request.form.getlist('checkin')
    checkin_json_raw = checkin_info[0]
    checkin_json = json.loads(checkin_json_raw)

    user = User.query.filter_by(foursquare_id=checkin_json['user']['id']).first()
    if user:
        if user.credit_url is None:
            response = _do_credit(user)
            user.credit_url = response['links']['self']['href']
            db.session.add(user)
            db.session.commit()

    # Return junk HTML just in case someone finds the URL.
    return redirect(url_for('thanks'))


@app.route('/thanks', methods=['GET'])
def thanks():
    return render_template('thanks.html')


def _auth_with_foursquare():
    auth_uri = foursquare_client.oauth.auth_url()
    return redirect(auth_uri)


def _validate_member(user):
    lcp_response = lcp_client.post(
        app.config['LCP_MV_URL'], data=_create_mv_data(user))
    lcp_response.raise_for_status()
    return lcp_response.json()


def _do_credit(user):
    lcp_response = lcp_client.post(
        app.config['LCP_CREDIT_URL'], data=_create_mv_data(user))
    lcp_response.raise_for_status()
    return lcp_response.json()


def _create_mv_data(user):
    return json.dumps({
        'firstName': user.first_name,
        'lastName': user.last_name,
        'memberId': user.membership_number
    })

def _create_credit_data(user):
    return json.dumps({
        'amount': app.config['LCP_CREDIT_AMOUNT'],
        'memberValidation': user.mv_url,
        'firstName': user.first_name,
        'lastName': user.last_name,
        'email': user.email
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0')
