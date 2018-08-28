import json
import os
import requests
import requests_cache

from flask import session, redirect, request, url_for
from requests_oauthlib import OAuth2Session
from flask.json import jsonify
from the_wheel.handlers.login import User
from flask_login import login_required, current_user
from datetime import datetime, timedelta


with open('auth.json') as cred_file:
    credentials = json.load(cred_file)[os.environ.get('STAGE')]

def fantasy_request(query):
    baseUrl = 'https://fantasysports.yahooapis.com/fantasy/v2/'
    r = requests.get(baseUrl + query + '?format=json',
                        headers={'Authorization': 'Bearer ' + str(current_user.oauth_token),
                                'Content-type': 'application/xml'})

    return r.json()

def setup_yahoo(app):
    requests_cache.install_cache(cache_name='yahoo_cache', expire_after=600)

    @app.route('/yahoo_auth')
    @login_required
    def yahoo_auth():
        yahoo = OAuth2Session(credentials['consumer_key'], redirect_uri=credentials['callback'])
        authorization_url, state = yahoo.authorization_url("https://api.login.yahoo.com/oauth2/request_auth")
        # State is used to prevent CSRF, keep this for later.
        session['oauth_state'] = state
        return redirect(authorization_url)

    @app.route('/callback', methods=["GET"])
    @login_required
    def yahoo_callback():
        code = request.args.get('code')
        r = requests.post("https://api.login.yahoo.com/oauth2/get_token",
                          auth=(credentials['consumer_key'], credentials['consumer_secret']),
                          data={'code': code,
                                'grant_type': 'authorization_code',
                                'redirect_uri': credentials['callback']})

        token = r.json()
        print(token)
        current_user.oauth_token = token['access_token']
        current_user.refresh_token = token['refresh_token']
        current_user.token_expiry = datetime.now() + timedelta(seconds=token['expires_in'])
        current_user.save()
        return redirect(url_for('home'))

    @app.route('/api_test')
    @login_required
    def api_trial():
        return jsonify(fantasy_request(request.args.get('q')))

    @app.route('/refresh')
    @login_required
    def refresh_token():
        code = current_user.refresh_token
        r = requests.post("https://api.login.yahoo.com/oauth2/get_token",
                        auth=(credentials['consumer_key'], credentials['consumer_secret']),
                        data={'refresh_token': code,
                                'grant_type': 'refresh_token',
                                'redirect_uri': credentials['callback']})

        token = r.json()
        current_user.oauth_token = token['access_token']
        current_user.refresh_token = token['refresh_token']
        current_user.token_expiry = datetime.now() + timedelta(seconds=token['expires_in'])
        current_user.save()
        print("{} has refreshed their token".format(current_user.name))
        return redirect(url_for('home'))
