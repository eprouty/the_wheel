from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link

from the_wheel import the_wheel

app = Flask(__name__)
Bootstrap(app)

nav = Nav()
nav.register_element('top', Navbar(
    View('The Wheel', '.home'),
))
nav.init_app(app)

the_wheel = the_wheel.TheWheel()

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
