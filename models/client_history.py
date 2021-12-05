from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ClientHistory(Base):
    __tablename__ = 'client_history'
    id = Column('id', Integer, primary_key=True)
    client_id = Column('client_id', Integer, ForeignKey("client.id"), nullable=False)
    login_time = Column('login_time', DateTime)
    ip_address = Column('ip_address', String)

    def __init__(self, client_id, login_time, ip_address):
        self.client_id = client_id
        self.login_time = login_time
        self.ip_address = ip_address
