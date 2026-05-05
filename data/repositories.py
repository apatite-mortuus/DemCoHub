import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

repositories_to_users = sqlalchemy.Table(
    "repositories_to_users",
    SqlAlchemyBase.metadata,
    sqlalchemy.Column("coauthors_id", sqlalchemy.Integer,
                      sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("repositories_id", sqlalchemy.Integer,
                      sqlalchemy.ForeignKey("repositories.id"))
)


class Repositories(SqlAlchemyBase):
    __tablename__ = "repositories"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    branches = orm.relationship("Branches", back_populates="repository")
    user = orm.relationship("User")
    coauthors = orm.relationship("User",
                                  secondary="repositories_to_users",
                                  back_populates="coauthorship")
