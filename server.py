from flask import Flask, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link
from flask_login import login_required, current_user
from flask_mongoengine import MongoEngine
import os

from the_wheel.handlers import wheel_of_shame, login

app = Flask(__name__)

mongoClient = None
mongoUri = None
wheel_db = None
if os.environ.get('MONGODB_URI'): # pragma: no cover
    # Production database
    mongoUri = os.environ['MONGODB_URI']

    app.config['MONGODB_SETTINGS'] = {
        'db': 'the_wheel',
        'host': mongoUri
    }
    print("Using production database!")
else:
    wheel_db = mongoClient.the_wheel

    app.config['MONGODB_SETTINGS'] = {
        'db': 'the_wheel',
    }


app.config['SECRET_KEY'] = 'thisisthewheelthatalwaysshames'

db = MongoEngine(app)
Bootstrap(app)

nav = Nav()
nav.register_element('top', Navbar(
    View('The Wheel', '.home'),
))
nav.init_app(app)

the_wheel = wheel_of_shame.WheelOfShame(db)
login.setup_login(app, db)

@app.route("/")
@login_required
def home():
    history = the_wheel.check_spins()
    print(history)
    can_spin = True
    if current_user.name in history:
        can_spin = False
    return render_template("index.html", history=history, name=current_user.name, can_spin=can_spin)

@app.route('/wheels_will')
@login_required
def wheels_will():
    return the_wheel.spin_wheel(current_user.name)

if __name__ == "__main__":
    app.run()
