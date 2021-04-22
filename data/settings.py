import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Settings(SqlAlchemyBase):
    __tablename__ = 'settings'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    banwords = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    tempban_len = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    is_activated = sqlalchemy.Column(sqlalchemy.Boolean)
    point_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    streamer_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("users.id"))
    streamer = orm.relation('User')