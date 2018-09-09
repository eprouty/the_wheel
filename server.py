import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import login_required, current_user
from flask_mongoengine import MongoEngine

from the_wheel.handlers import wheel_of_shame, login, yahoo

app = Flask(__name__)

mongoUri = None
wheel_db = None
if os.environ.get('MONGODB_URI'): # pragma: no cover
    # Production database
    mongoUri = os.environ['MONGODB_URI']

    app.config['MONGODB_SETTINGS'] = {
        'db': 'the_wheel',
        'host': mongoUri
    }
    print("Using {} database!".format(os.environ.get('STAGE')))
else:
    app.config['MONGODB_SETTINGS'] = {
        'db': 'the_wheel',
    }


app.config['SECRET_KEY'] = 'thisisthewheelthatalwaysshames'

db = MongoEngine(app)
Bootstrap(app)

the_wheel = wheel_of_shame.WheelOfShame()
login.setup_login(app)
yahoo.setup_yahoo(app)

@app.route("/")
@login_required
def home():
    # if 'oauth_token' not in session:  # Need to validate not just look at it...
    if not current_user.oauth_token:
        return redirect(url_for('yahoo_auth'))
    elif datetime.now() > current_user.token_expiry:
        return redirect(url_for('refresh_token'))

    history = the_wheel.check_spins()
    can_spin = True
    if current_user.name in history:
        can_spin = False

    chopping_block = the_wheel.chopping_block()
    chopping_block['the_block'] = sorted(chopping_block['the_block'].items(), key=lambda x: x[1])

    projected_loser = min(filter(lambda x: 'projected' in x[0], chopping_block['the_block']), key=lambda x: x[1])[0].split('_')[0]
    return render_template("index.html", history=history, name=current_user.name, can_spin=can_spin, chopping_block=chopping_block, p_loser=projected_loser)

@app.route('/wheels_will')
@login_required
def wheels_will():
    history = the_wheel.check_spins()
    if current_user.name not in history:
        return the_wheel.spin_wheel(current_user.name)

@app.route('/update')
def update():
    system_user = login.User.objects(name='system').first()
    if datetime.now() > system_user.token_expiry:
        return redirect(url_for('refresh_system_token'))
    return the_wheel.update_losers(user_override=system_user)

if __name__ == "__main__":
    app.run()
