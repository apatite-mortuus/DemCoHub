import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Branches(SqlAlchemyBase):
    __tablename__ = "branches"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    repository_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("repositories.id"), nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    repository = orm.relationship("Repositories")
    buffers = orm.relationship("Buffers", back_populates="branch")
    commits = orm.relationship("Commits",
                                    secondary="commits_to_branches",
                                    backref="branches")
