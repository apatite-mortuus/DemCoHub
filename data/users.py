import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm

from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    nickname = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    audiofile = orm.relationship("Audiofile", back_populates='user')
    likes = orm.relationship("Likes", back_populates="user")
    dislikes = orm.relationship("Dislikes", back_populates="user")
    repositories = orm.relationship("Repositories", back_populates="user")
    buffer = orm.relationship("Buffers", back_populates="user")
    coauthorship = orm.relationship("Repositories",
                                  secondary="repositories_to_users",
                                  backref="users")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
