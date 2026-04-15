import secrets

from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

from data.users import User
from data import db_session
from forms.login_form import LoginForm
from forms.register_form import RegisterForm

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_urlsafe(32)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.repeat_password.data:
            return render_template("register_form.html", title="Регистрация",
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("register_form.html", title="Регистрация",
                                   form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template("register_form.html", title="Регистрация",
                                   form=form,
                                   message="Пользователь с таким никнеймом уже есть")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect("/login")
    return render_template("register_form.html", title="Регистрация", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.email == form.login.data) | (User.nickname == form.login.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login_form.html', message="Неправильный логин или пароль", form=form)
    return render_template('login_form.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    db_session.global_init("database/users.db")
    app.run(host="127.0.0.1", port=8000, debug=True)
