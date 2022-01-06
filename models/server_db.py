from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ServerDB:
    Base = declarative_base()

    class Clients(Base):
        __tablename__ = 'clients'
        id = Column('id', Integer, primary_key=True)
        login = Column('login', String, unique=True)
        last_login_time = Column('last_login_time', DateTime)

        def __init__(self, login, last_login_time):
            self.login = login
            self.last_login_time = last_login_time

    class ClientHistory(Base):
        __tablename__ = 'client_history'
        id = Column('id', Integer, primary_key=True)
        client_id = Column('client_id', Integer, ForeignKey("clients.id"), nullable=False)
        login_time = Column('login_time', DateTime)
        ip_address = Column('ip_address', String)
        port = Column('port', Integer)

        def __init__(self, client_id, login_time, ip_address, port):
            self.client_id = client_id
            self.login_time = login_time
            self.ip_address = ip_address
            self.port = port

    class ActiveClients(Base):
        __tablename__ = 'active_clients'
        id = Column('id', Integer, primary_key=True)
        client_id = Column('client_id', Integer, ForeignKey("clients.id"), nullable=False)
        ip_address = Column('ip_address', String)
        port = Column('port', Integer)
        login_time = Column('login_time', DateTime)

        def __init__(self, client_id, login_time, ip_address, port):
            self.client_id = client_id
            self.login_time = login_time
            self.ip_address = ip_address
            self.port = port

    def __init__(self):
        self.engine = create_engine('sqlite:///messenger.sqlite3', pool_recycle=7200)
        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.query(self.ActiveClients).delete()
        self.session.commit()

    def client_login(self, login, ip_address, port):
        now = datetime.now()
        clients = self.session.query(self.Clients).filter_by(login=login)
        if clients.count():
            client = clients.first()
            client.last_login = now
        else:
            client = self.Clients(login, now)
            self.session.add(client)
            self.session.commit()
        active_client = self.ActiveClients(client.id, now, ip_address, port)
        self.session.add(active_client)
        history = self.ClientHistory(client.id, now, ip_address, port)
        self.session.add(history)
        self.session.commit()

    def client_logout(self, login):
        client = self.session.query(self.Clients).filter_by(login=login).first()
        self.session.query(self.ActiveClients).filter_by(client_id=client.id).delete()
        self.session.commit()

    def clients_list(self):
        query = self.session.query(self.Clients.login, self.Clients.last_login_time)
        return query.all()

    def active_clients_list(self):
        query = self.session.query(
            self.Clients.login,
            self.ActiveClients.port,
            self.ActiveClients.ip_address,
            self.ActiveClients.login_time
        ).join(self.Clients, self.Clients.id == self.ActiveClients.client_id)

        return query.all()

    def login_history(self, login=None):
        query = self.session.query(self.Clients.login,
                                   self.ClientHistory.login_time,
                                   self.ClientHistory.ip_address,
                                   self.ClientHistory.port
                                   ).join(self.Clients)
        if login:
            query = query.filter(self.Clients.login == login)
        return query.all()

    def clear_history(self, login):
        client = self.session.query(self.Clients).filter_by(login=login).first()
        self.session.query(self.ClientHistory).filter_by(client_id=client.id).delete()
        self.session.commit()

    def client_delete(self, login):
        self.session.query(self.Clients).filter_by(login=login).delete()
        self.session.commit()


if __name__ == '__main__':
    db = ServerDB()
    db.client_login('client_1', '192.168.1.4', 8888)
    db.client_login('client_2', '192.168.1.5', 7777)

    print(db.active_clients_list())

    db.client_logout('client_1')
    print(db.clients_list())

    print(db.active_clients_list())
    db.client_logout('client_2')
    print(db.clients_list())
    print(db.active_clients_list())
    print(db.login_history('client_1'))
    # db.clear_history('client_1')
    # print(db.login_history('client_1'))
    # print(db.login_history())
    # db.client_delete('client_2')
    # print(db.login_history())
