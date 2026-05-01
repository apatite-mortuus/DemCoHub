import datetime
import io
import secrets
import pathlib
import os
import hashlib
import shutil
import tempfile

from flask import Flask, render_template, redirect, request, url_for, abort, jsonify, send_from_directory, send_file
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

from data.users import User
from data.audiofiles import Audiofile
from data.likes import Likes
from data.dislikes import Dislikes
from data.repositories import Repositories
from data.branches import Branches
from data.commits import Commits
from data.buffers import Buffers
from data import db_session
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.post_audio_form import PostAudioForm
from forms.repo_form import RepoForm
from forms.branch_form import BranchForm

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_urlsafe(32)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as db_sess:
        return db_sess.get(User, user_id)


@app.route("/")
@app.route("/index")
def index():
    with db_session.create_session() as db_sess:
        files = db_sess.query(Audiofile).all()
        return render_template("index.html", files=files, title="Главная | DemCoHub")


@app.route("/like", methods=["POST"])
def like():
    with db_session.create_session() as db_sess:
        file = db_sess.query(Likes).filter(Likes.author_id == current_user.id,
                                           Likes.audiofile == request.form["id"]).first()
        if file:
            db_sess.delete(file)
            db_sess.commit()
            return jsonify({"status": "OK", "response": "deleted"})
        lk = Likes(
            audiofile=request.form["id"],
            author_id=current_user.id
        )
        db_sess.add(lk)
        db_sess.commit()
        return jsonify({"status": "OK", "response": "created"})


@app.route("/dislike", methods=["POST"])
def dislike():
    db_sess = db_session.create_session()
    file = db_sess.query(Dislikes).filter(Dislikes.author_id == current_user.id,
                                          Dislikes.audiofile == request.form["id"]).first()
    if file:
        db_sess.delete(file)
        db_sess.commit()
        return jsonify({"status": "OK", "response": "deleted"})
    dlk = Dislikes(
        audiofile=request.form["id"],
        author_id=current_user.id
    )
    db_sess.add(dlk)
    db_sess.commit()
    return jsonify({"status": "OK", "response": "created"})


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.repeat_password.data:
            return render_template("register_form.html", title="Регистрация | DemCoHub",
                                   form=form, message="Пароли не совпадают")
        with db_session.create_session() as db_sess:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template("register_form.html", title="Регистрация | DemCoHub",
                                       form=form, message="Такой пользователь уже есть")
            if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
                return render_template("register_form.html", title="Регистрация | DemCoHub",
                                       form=form, message="Пользователь с таким никнеймом уже есть")
            user = User(
                nickname=form.nickname.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            return redirect("/login")
    return render_template("register_form.html", title="Регистрация | DemCoHub", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            user = db_sess.query(User).filter(
                (User.email == form.login.data) | (User.nickname == form.login.data)).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login_form.html', message="Неправильный логин или пароль", form=form,
                                   title='Авторизация | DemCoHub')
    return render_template('login_form.html', title='Авторизация | DemCoHub', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/post_audio", methods=["GET", "POST"])
@login_required
def post_audio():
    form = PostAudioForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            audiofile = Audiofile(
                author=form.author.data,
                title=form.title.data,
                posted=current_user.id,
                date_time=datetime.datetime.now()
            )
            if request.method == "POST":
                url = ""
                img = request.files["file"]
                try:
                    with open(f"static/upload/public_audio/{img.filename}", "xb") as f:
                        f.write(img.read())
                        url = f"upload/public_audio/{img.filename}"
                except FileExistsError:
                    i = 1
                    while True:
                        try:
                            print(i)
                            with open(
                                    f"static/upload/public_audio/{img.filename.rsplit(".", 1)[0]} ({i}).{img.filename.rsplit(".", 1)[1]}",
                                    "xb") as f:
                                f.write(img.read())
                                url = f"upload/public_audio/{img.filename}"
                                break
                        except FileExistsError:
                            i += 1
            audiofile.path_to_file = url_for("static", filename=url)
            db_sess.add(audiofile)
            db_sess.commit()
            return redirect("/")
    return render_template("post_audio_form.html", title="Публикация | DemCoHub", form=form)


@app.route('/audio_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def audio_delete(id):
    with db_session.create_session() as db_sess:
        audio = db_sess.query(Audiofile).filter(Audiofile.id == id, current_user.id == Audiofile.posted).first()
        if audio:
            db_sess.delete(audio)
            db_sess.commit()
        else:
            abort(404)
        return redirect('/')


@app.route("/<nickname>")
def profile(nickname):
    with db_session.create_session() as db_sess:
        files = db_sess.query(User).filter(User.nickname == nickname).first().audiofile
        if not current_user.is_authenticated or current_user.nickname != nickname:
            return render_template("profile.html", files=files, title=f"{nickname} | DemCoHub", user=nickname)
        return render_template("profile.html", files=files, title=f"{current_user.nickname} | DemCoHub")


@app.route("/create_repository", methods=["GET", "POST"])
@login_required
def create_repository():
    form = RepoForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            if db_sess.query(Repositories).join(Repositories.user).filter(Repositories.title == form.title.data,
                                                                          User.id == current_user.id).first():
                return render_template("repository_form.html", title="Создание репозитория | DemCoHub",
                                       form=form, message="Репозиторий с таким именем уже существует")
            repo = Repositories(
                title=form.title.data,
                description=form.description.data,
                author_id=current_user.id
            )
            db_sess.add(repo)
            branch = Branches(
                title="master",
                repository_id=db_sess.query(Repositories).join(Repositories.user).filter(
                    Repositories.title == form.title.data,
                    User.id == current_user.id).first().id
            )
            commit = Commits(
                description="initial commit",
                path=f"static/upload/users/{current_user.nickname}/repositories/{form.title.data}/commits/",
                date_time=datetime.datetime.now()
            )
            commit.sha1 = hashlib.sha1((str(commit.date_time) + commit.path + commit.description).encode()).hexdigest()
            commit.path += commit.sha1[:7]
            branch.commits.append(commit)
            db_sess.add(branch)
            db_sess.add(commit)
            db_sess.commit()
            pathlib.Path(commit.path).mkdir(exist_ok=True, parents=True)
            return redirect(f"/{current_user.nickname}/repositories")
    return render_template("repository_form.html", title="Создание репозитория | DemCoHub", form=form)


@app.route("/<nickname>/repositories")
def repositories_list(nickname):
    with db_session.create_session() as db_sess:
        repos = db_sess.query(Repositories).join(Repositories.user).filter(User.nickname == nickname).all()
        if not current_user.is_authenticated or current_user.nickname != nickname:
            return abort(403)
        return render_template("repositories_list.html", repos=repos, title=f"Ваши репозитории | DemCoHub")


@app.route("/<nickname>/repositories/<repository>")
def show_repository(nickname, repository):
    with db_session.create_session() as db_sess:
        branches = db_sess.query(Branches).join(Branches.repository).filter(Repositories.title == repository).all()
        if not current_user.is_authenticated or current_user.nickname != nickname:
            return abort(403)
        return render_template("repository.html", branches=branches, title=f"{repository} | DemCoHub")


@app.route("/<nickname>/repositories/<repository>/<branch>")
def show_branch(nickname, repository, branch):
    with db_session.create_session() as db_sess:
        br = db_sess.query(Branches).join(Repositories).filter(Branches.title == branch,
                                                               Repositories.title == repository).first()
        commits = br.commits
        if not current_user.is_authenticated or current_user.nickname != nickname:
            return abort(403)
        return render_template("branch.html", nickname=nickname, repository=repository, branch=branch, commits=commits,
                               title=f"{repository} | DemCoHub")


@app.route("/<repository>/create_branch", methods=["GET", "POST"])
@login_required
def create_branch(repository):
    with db_session.create_session() as db_sess:
        form = BranchForm()
        form.parent.choices = [b.title for b in
                               db_sess.query(Branches).join(Branches.repository).join(Repositories.user).filter(
                                   User.id == current_user.id, Repositories.title == repository).all()]
        if form.validate_on_submit():
            if db_sess.query(Branches).join(Branches.repository).join(Repositories.user).filter(
                    Branches.title == form.title.data,
                    User.id == current_user.id).first():
                return render_template("branch_form.html", title="Создание ветки | DemCoHub",
                                       form=form, message="Ветка с таким именем уже существует")
            branch = Branches(
                title=form.title.data,
                repository_id=db_sess.query(Repositories.id).filter(Repositories.id == repository).first(),
                commits=db_sess.query(Branches.commits).filter(Branches.title == form.parent.data).first()
            )
            db_sess.add(branch)
            db_sess.commit()
            return redirect(f"/{current_user.nickname}/repositories/{repository}")
        return render_template("branch_form.html", title="Создание ветки | DemCoHub", form=form)


@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/<path:folders>")
@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>", defaults={"folders": None})
def show_commit(nickname, repository, branch, sha1, folders):
    # if not current_user.is_authenticated or current_user.nickname != nickname:
    #     return abort(403)
    with db_session.create_session() as db_sess:
        folders = folders.split("/") if folders else []
        commit = db_sess.query(Commits).filter(Commits.sha1 == sha1).first()
        dr = [(i, os.path.isfile(commit.path + "/" + "/".join(folders + [i]))) for i in
              os.listdir(commit.path + "/" + "/".join(folders))]
        return render_template("commit.html", nickname=nickname, repository=repository, branch=branch,
                               commit=commit.sha1, dr=dr, folders=folders,
                               title=f"{commit.sha1[:7]} | DemCoHub")


@app.route("/buffer/<path:folders>")
@app.route("/buffer", defaults={"folders": None})
def show_buffer(folders):
    with db_session.create_session() as db_sess:
        buffer = db_sess.query(Buffers).join(Buffers.user).filter(User.id == current_user.id).first()
        nickname = buffer.user.nickname
        branch = buffer.branch.title
        repository = buffer.branch.repository.title
        folders = folders.split("/") if folders else []
        path = f"static/upload/users/{nickname}/buffer/"
        dr = [(i, os.path.isfile(path + "/" + "/".join(folders + [i]))) for i in
              os.listdir(path + "/".join(folders))]
        return render_template("commit.html", nickname=nickname, repository=repository, branch=branch,
                               commit="buffer", dr=dr, folders=folders,
                               title="buffer | DemCoHub")


@app.route("/<path:folders>/post_file", methods=["POST"])
@app.route("/post_file", defaults={"folders": None}, methods=["POST"])
def post_file(folders):
    folders = folders.split("/") if folders else []
    path = f"static/upload/users/{current_user.nickname}/buffer/"
    request.files["file"].save(path + "/".join(folders + [request.form["name"]]))
    return redirect(url_for("show_buffer", folders='/'.join(folders)))


@app.route("/<path:folders>/delete_file", methods=["DELETE"])
@app.route("/delete_file", defaults={"folders": None}, methods=["DELETE"])
def delete_file(folders):
    folders = folders.split("/") if folders else []
    path = f"static/upload/users/{current_user.nickname}/buffer/"
    os.remove(path + "/".join(folders + [request.form["name"]]))
    return redirect(url_for("show_buffer", folders='/'.join(folders)))


@app.route("/<path:folders>/delete_folder", methods=["DELETE"])
@app.route("/delete_folder", defaults={"folders": None}, methods=["DELETE"])
def delete_folder(folders):
    folders = folders.split("/") if folders else []
    path = f"static/upload/users/{current_user.nickname}/buffer/"
    shutil.rmtree(path + "/".join(folders + [request.form["name"]]))
    return redirect(url_for("show_buffer", folders='/'.join(folders)))


@app.route("/<path:folders>/create_folder", methods=["POST"])
@app.route("/create_folder", defaults={"folders": None}, methods=["POST"])
def create_folder(folders):
    folders = folders.split("/") if folders else []
    path = f"static/upload/users/{current_user.nickname}/buffer/"
    pathlib.Path(path + "/".join(folders + [request.form["folderName"]])).mkdir(parents=True, exist_ok=True)
    return redirect(url_for("show_buffer", folders='/'.join(folders)))


@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/create_buffer", methods=["POST"])
def create_buffer(nickname, repository, branch, sha1):
    path = f"static/upload/users/{nickname}/buffer/"
    if not os.path.exists(path):
        with db_session.create_session() as db_sess:
            pathlib.Path(path).mkdir(exist_ok=True, parents=True)
            commit = db_sess.query(Commits).filter(Commits.sha1 == sha1).first()
            shutil.copytree(commit.path, path, dirs_exist_ok=True)
            buffer = Buffers(
                user_id=db_sess.query(User).filter(User.nickname == nickname).first().id,
                branch_id=db_sess.query(Branches).filter(Branches.title == branch).first().id
            )
            db_sess.add(buffer)
            db_sess.commit()
    return jsonify({"status": "OK"})


@app.route("/create_commit", methods=["POST"])
def create_commit():
    # if not current_user.is_authenticated or current_user.nickname != nickname:
    #     return abort(403)
    with db_session.create_session() as db_sess:
        buffer = db_sess.query(Buffers).join(Buffers.user).filter(User.id == current_user.id).first()
        nickname = buffer.user.nickname
        repository = buffer.branch.repository.title
        path = f"static/upload/users/{nickname}/buffer"
        commit = Commits(
            description=request.form["message"],
            path=f"static/upload/users/{nickname}/repositories/{repository}/commits/",
            date_time=datetime.datetime.now()
        )
        commit.sha1 = hashlib.sha1((str(commit.date_time) + commit.path + commit.description).encode()).hexdigest()
        commit.path += commit.sha1[:7]
        shutil.copytree(path, commit.path)
        db_sess.add(commit)
        buffer.branch.commits.append(commit)
        db_sess.delete(buffer)
        db_sess.commit()
        shutil.rmtree(path)
        return jsonify({"status": "OK"})


@app.route("/delete_buffer", methods=["DELETE"])
def delete_buffer():
    with db_session.create_session() as db_sess:
        buffer = db_sess.query(Buffers).join(Buffers.user).filter(User.id == current_user.id).first()
        nickname = buffer.user.nickname
        path = f"static/upload/users/{nickname}/buffer"
        db_sess.delete(buffer)
        db_sess.commit()
        shutil.rmtree(path)
        return jsonify({"status": "OK"})


@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/<path:folders>/download_file/<filename>")
@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/download_file/<filename>", defaults={"folders": None})
def download_file(nickname, repository, branch, sha1, folders, filename):
    if sha1 == "buffer":
        return send_file(
            f"static/upload/users/{nickname}/buffer{("/" + folders) if folders else ''}/{filename}",
            as_attachment=True)
    return send_file(
        f"static/upload/users/{nickname}/repositories/{repository}/{sha1[:7]}{("/" + folders) if folders else ''}/{filename}",
        as_attachment=True)


@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/<path:folders>/download_folder/<filename>")
@app.route("/<nickname>/repositories/<repository>/<branch>/<sha1>/download_folder/<filename>",
           defaults={"folders": None})
def download_folder(nickname, repository, branch, sha1, folders, filename):
    if sha1 == "buffer":
        path = f"static/upload/users/{nickname}/buffer{("/" + folders) if folders else ''}/{filename}"
    else:
        path = f"static/upload/users/{nickname}/repositories/{repository}/{sha1[:7]}{("/" + folders) if folders else ''}/{filename}"
    try:
        shutil.make_archive(filename, 'zip', path)
        zip_buffer = io.BytesIO()
        with open(filename + ".zip", 'rb') as f:
            zip_buffer.write(f.read())
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name=(filename + ".zip"))
    finally:
        os.remove(filename + ".zip")


if __name__ == "__main__":
    db_session.global_init("database/users.db")
    app.run(host="127.0.0.1", port=8000, debug=True)
