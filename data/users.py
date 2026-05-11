import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm

from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin):
    # Название таблицы
    __tablename__ = "users"

    # Поля таблицы
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    nickname = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # Отношения между таблицами "один ко многим"
    audiofile = orm.relationship("Audiofile", back_populates='user')
    likes = orm.relationship("Likes", back_populates="user")
    dislikes = orm.relationship("Dislikes", back_populates="user")
    repositories = orm.relationship("Repositories", back_populates="user")
    buffer = orm.relationship("Buffers", back_populates="user")
    # Связь с промежуточной таблицей
    # для создания отношения "многие ко многим"
    coauthorship = orm.relationship("Repositories",
                                    secondary="repositories_to_users",
                                    back_populates="coauthors")

    # Сохраняет хэшированный пароль
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    # Проверяет пароль
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
