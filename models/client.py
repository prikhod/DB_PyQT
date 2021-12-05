from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Client(Base):
    __tablename__ = 'client'
    id = Column('id', Integer, primary_key=True),
    login = Column('login', String)
    info = Column('info', String)

    def __init__(self, login, info):
        self.login = login
        self.info = info
