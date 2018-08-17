from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link

from the_wheel.handlers import wheel_of_shame

app = Flask(__name__)
Bootstrap(app)

nav = Nav()
nav.register_element('top', Navbar(
    View('The Wheel', '.home'),
))
nav.init_app(app)

the_wheel = wheel_of_shame.WheelOfShame()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/wheel")
def wheel():
    return render_template('wheel_of_shame.html')

@app.route('/wheels_will')
def wheels_will():
    return the_wheel.spin_wheel()

if __name__ == "__main__":
    app.run()
