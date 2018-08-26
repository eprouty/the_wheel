from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


def setup_login(app, db):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    class User(UserMixin, db.Document):
        meta = {'collection': 'users'}
        name = db.StringField(max_length=30)
        password = db.StringField()

    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(pk=user_id).first()

    class RegForm(FlaskForm):
        name = StringField('name',  validators=[InputRequired(), Length(max=30)])
        password = PasswordField('password', validators=[InputRequired(), Length(min=3, max=20)])

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegForm()
        if request.method == 'POST':
            if form.validate():
                existing_user = User.objects(name=form.name.data).first()
                if existing_user is None:
                    hashpass = generate_password_hash(form.password.data, method='sha256')
                    hey = User(form.name.data,hashpass).save()
                    login_user(hey)
                    return redirect(url_for('home'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('/'))
        form = RegForm()
        if request.method == 'POST':
            if form.validate():
                check_user = User.objects(name=form.name.data).first()
                if check_user:
                    if check_password_hash(check_user['password'], form.password.data):
                        login_user(check_user)
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
