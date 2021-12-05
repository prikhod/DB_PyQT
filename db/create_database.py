from sqlalchemy import create_engine, MetaData, String, Table, Column, Integer, DateTime, ForeignKey

from core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)

metadata = MetaData()
client = Table('client', metadata,
               Column('id', Integer, primary_key=True),
               Column('login', String),
               Column('info', String))

client_history = Table('client_history', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('client_id', Integer, ForeignKey("client.id"), nullable=False),
                       Column('login_time', DateTime),
                       Column('ip_address', String))

metadata.create_all(engine)
