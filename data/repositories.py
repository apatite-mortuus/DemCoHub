import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

# Промежуточная таблица для создания отношения "многие ко многим"
repositories_to_users = sqlalchemy.Table(
    "repositories_to_users",
    SqlAlchemyBase.metadata,
    sqlalchemy.Column("coauthors_id", sqlalchemy.Integer,
                      sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("repositories_id", sqlalchemy.Integer,
                      sqlalchemy.ForeignKey("repositories.id"))
)


class Repositories(SqlAlchemyBase):
    # Название таблицы
    __tablename__ = "repositories"

    # Поля таблицы
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    # Связь с id таблицы users через Foreign Key
    author_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey("users.id"), nullable=True)
    user = orm.relationship("User")
    # Отношения между таблицами "один ко многим"
    branches = orm.relationship("Branches", back_populates="repository")
    # Связь с промежуточной таблицей
    # для создания отношения "многие ко многим"
    coauthors = orm.relationship("User",
                                 secondary="repositories_to_users",
                                 back_populates="coauthorship")
