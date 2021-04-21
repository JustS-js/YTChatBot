import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy import orm


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    channel_id = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    settings = orm.relation("Settings", back_populates='streamer')
    viewers = orm.relation("Viewer", back_populates='streamer')

    def __repr__(self):
        return f'{self.surname} {self.name}'
