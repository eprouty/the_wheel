import json
import os
import requests
import requests_cache

from datetime import datetime, timedelta
from flask import session, redirect, request, url_for
from flask.json import jsonify
from flask_login import login_required, current_user
from requests_oauthlib import OAuth2Session

from the_wheel.handlers.login import User


with open('auth.json') as cred_file:
    credentials = json.load(cred_file)[os.environ.get('STAGE')]

def fantasy_request(query, user_override=None):
    baseUrl = 'https://fantasysports.yahooapis.com/fantasy/v2/'
    if user_override:
        token = str(user_override.oauth_token)
    else:
        token = str(current_user.oauth_token)

    r = requests.get(baseUrl + query + '?format=json',
                     headers={'Authorization': 'Bearer ' + token,
                              'Content-type': 'application/xml'})

    return r.json()

def get_scoreboard(league, user_override):
    output = []
    r = fantasy_request('league/{}/scoreboard'.format(league), user_override=user_override)
    matchups = r['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    for key in matchups:
        if key != 'count':
            match = matchups[key]['matchup']
            week_end = match['week_end']
            week_start = match['week_start']
            team0_name = match['0']['teams']['0']['team'][0][19]['managers'][0]['manager']['nickname']
            team0_score = float(match['0']['teams']['0']['team'][1]['team_points']['total'])
            team0_projected = float(match['0']['teams']['0']['team'][1]['team_projected_points']['total'])
            team1_name = match['0']['teams']['1']['team'][0][19]['managers'][0]['manager']['nickname']
            team1_score = float(match['0']['teams']['1']['team'][1]['team_points']['total'])
            team1_projected = float(match['0']['teams']['1']['team'][1]['team_projected_points']['total'])
            output.append({'week_end': week_end,
                           'week_start': week_start,
                           'team0_name': team0_name,
                           'team1_name': team1_name,
                           'team0_score': team0_score,
                           'team1_score': team1_score,
                           'team0_projected': team0_projected,
                           'team1_projected': team1_projected})

    return (output, output[0]['week_start'], output[0]['week_end'])



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

    @app.route('/refresh_system_token')
    def refresh_system_token():
        system_user = User.objects(name='system').first()
        code = system_user.refresh_token
        r = requests.post("https://api.login.yahoo.com/oauth2/get_token",
                        auth=(credentials['consumer_key'], credentials['consumer_secret']),
                        data={'refresh_token': code,
                                'grant_type': 'refresh_token',
                                'redirect_uri': credentials['callback']})

        token = r.json()
        system_user.oauth_token = token['access_token']
        system_user.refresh_token = token['refresh_token']
        system_user.token_expiry = datetime.now() + timedelta(seconds=token['expires_in'])
        system_user.save()
        return redirect(url_for('update'))
