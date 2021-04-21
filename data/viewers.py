import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Viewer(SqlAlchemyBase):
    __tablename__ = 'viewers'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    channel_id = sqlalchemy.Column(sqlalchemy.String)
    bantype = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    repeated_msg = sqlalchemy.Column(sqlalchemy.Integer)
    points = sqlalchemy.Column(sqlalchemy.Integer)

    streamer_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("users.id"))
    streamer = orm.relation('User')