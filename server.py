import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from flask_caching import Cache
from flask_login import login_required, current_user
from flask_mongoengine import MongoEngine

from the_wheel.handlers import login, stats, wheel_of_shame, yahoo

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

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

db = MongoEngine(app)
Bootstrap(app)

the_wheel = wheel_of_shame.WheelOfShame()

the_stats = stats.Stats()
the_stats.setup_stats(app)

login.setup_login(app)
yahoo.setup_yahoo(app)

@app.route("/")
@login_required
def home():
    # Revalidate the token if it's expired
    if datetime.now() > current_user.token_expiry:
        return redirect(url_for('refresh_token'))

    history = the_wheel.check_spins()
    can_spin = True
    if current_user.name in history:
        can_spin = False

    chopping_block = the_wheel.chopping_block()
    chopping_block['the_block'] = sorted(chopping_block['the_block'].items(), key=lambda x: x[1]['overall'])

    return render_template("index.html", history=history, name=current_user.name, can_spin=can_spin, chopping_block=chopping_block, page='home')

@app.route('/visitor')
@cache.cached(timeout=500)
def visitor():
    history = the_wheel.check_spins()
    chopping_block = the_wheel.chopping_block()
    chopping_block['the_block'] = sorted(chopping_block['the_block'].items(), key=lambda x: x[1]['overall'])

    return render_template("index.html", can_spin=False, history=history, chopping_block=chopping_block, page='visitor')

@app.route('/history')
@cache.cached(timeout=500)
def history():
    weeks = the_wheel.get_weeks()
    last_week = the_wheel.get_history('last')
    last_week['the_block'] = sorted(last_week['the_block'].items(), key=lambda x: x[1]['overall'])

    return render_template('history.html', weeks=weeks, results=last_week, page='history')

@app.route('/wheels_will')
@login_required
def wheels_will():
    history = the_wheel.check_spins()
    if current_user.name not in history:
        return the_wheel.spin_wheel(current_user.name)

@app.route('/horrible_wheel')
@login_required
def horrible_wheel():
    pass

@app.route('/update')
def update():
    system_user = login.User.objects(name='system').first()
    if datetime.now() > system_user.token_expiry:
        return redirect(url_for('refresh_system_token'))

    return the_wheel.update_losers(user_override=system_user)

@app.route('/css/<path:path>')
def static_css(path):
    return send_from_directory('css', path)

@app.route('/images/<path:path>')
def static_images(path):
    return send_from_directory('images', path)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run()
