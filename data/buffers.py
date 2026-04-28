import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Buffers(SqlAlchemyBase):
    __tablename__ = "buffers"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("users.id"), nullable=True)
    branch_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("branches.id"), nullable=True)
    user = orm.relationship("User")
    branch = orm.relationship("Branches")
