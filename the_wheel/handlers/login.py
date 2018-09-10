import mongoengine as me

from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

class User(UserMixin, me.Document):
    meta = {'collection': 'users'}
    name = me.StringField(max_length=30)
    password = me.StringField()
    oauth_token = me.StringField()
    refresh_token = me.StringField()
    token_expiry = me.DateTimeField()

def setup_login(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'


    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(pk=user_id).first()

    class RegForm(FlaskForm):
        name = StringField('name', validators=[InputRequired(), Length(max=30)])
        password = PasswordField('password', validators=[InputRequired(), Length(min=3, max=20)])

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegForm()
        if request.method == 'POST':
            if form.validate():
                existing_user = User.objects(name=form.name.data).first()
                if existing_user is None:
                    hashpass = generate_password_hash(form.password.data, method='sha256')
                    hey = User(form.name.data, hashpass).save()
                    login_user(hey)
                    return redirect(url_for('home'))
        return render_template('register.html', form=form)


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))

        form = RegForm()
        if request.method == 'POST':
            if form.validate():
                check_user = User.objects(name=form.name.data).first()
                if check_user:
                    if check_password_hash(check_user['password'], form.password.data):
                        login_user(check_user, remember=True)

                        # if 'oauth_token' not in session:  # Need to validate not just look at it...
                        if not check_user['oauth_token']:
                            return redirect(url_for('yahoo_auth'))
                        else:
                            return redirect(url_for('home'))
        return render_template('login.html', form=form)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', name=current_user.name)

    @app.route('/logout', methods = ['GET'])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
