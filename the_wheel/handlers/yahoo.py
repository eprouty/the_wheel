import json
from flask import session, redirect, request, url_for
from flask.json import jsonify
from requests_oauthlib import OAuth2Session

with open('auth.json') as cred_file:
    credentials = json.load(cred_file)

def setup_yahoo(app):
    def get_session(state=None, token=None):
        return OAuth2Session(credentials['consumer_key'], response_type="id_token", redirect_uri="https://the-wheel-staging.herokuapp.com/callback", state=state, token=token)

    @app.route('/yahoo_auth')
    def yahoo_auth():
        yahoo = get_session()
        authorization_url, state = yahoo.authorization_url("https://api.login.yahoo.com/oauth/v2/request_auth")

        # State is used to prevent CSRF, keep this for later.
        session['oauth_state'] = state
        return redirect(authorization_url)

    @app.route('/callback', methods=["GET"])
    def yahoo_callback():
        yahoo = get_session(state=session['oauth_state'])
        token = yahoo.fetch_token("https://api.login.yahoo.com/oauth/v2/get_token",
                                  client_secret=credentials['consumer_secret'],
                                  authorization_response=request.url)

        session['oauth_token'] = token
        return redirect(url_for('home'))

    @app.route('/api_test')
    def api_trial():
        """Fetching a protected resource using an OAuth 2 token.
        """
        yahoo = get_session(token=session['oauth_token'])
        return jsonify(yahoo.get('https://fantasysports.yahooapis.com/fantasy/v2/game/nfl').json())
