from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ClientDB:
    Base = declarative_base()

    class Contacts(Base):
        __tablename__ = 'clients'
        id = Column('id', Integer, primary_key=True)
        contact = Column('contact', String, unique=True)

        def __init__(self, contact):
            self.contact = contact

    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column('id', Integer, primary_key=True)
        from_login = Column('from_login', String)
        to_login = Column('to_login', String)
        message = Column('message', String)
        date = Column('date', DateTime)

        def __init__(self, from_login, to_login, message, date):
            self.from_login = from_login
            self.to_login = to_login
            self.message = message
            self.date = date

    def __init__(self):
        self.engine = create_engine('sqlite:///client.sqlite3',
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def get_contacts(self):
        query = self.session.query(self.Contacts.contact)
        return query.all()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(contact=contact).count():
            _contact = self.Contacts(contact)
            self.session.add(_contact)
            self.session.commit()

    def add_contacts(self, contacts):
        self.session.query(self.Contacts).delete()
        for contact in contacts:
            _contact = self.Contacts(contact)
            self.session.add(_contact)
        self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(contact=contact).delete()
        self.session.commit()

    def save_message(self, from_login, to_login, message, date):
        _message = self.MessageHistory(from_login, to_login, message, date)
        self.session.add(_message)
        self.session.commit()

    def get_history(self, from_login, to_login):
        query = self.session.query(self.MessageHistory.from_login,
                                   self.MessageHistory.to_login,
                                   self.MessageHistory.message, self.MessageHistory.date
                                   ).filter_by(from_login=from_login, to_login=to_login)
        return query.all()


if __name__ == '__main__':
    db = ClientDB()
    db.save_message('client_1', 'client_2', 'message1', datetime.now())
    db.save_message('client_2', 'client_2', 'message2', datetime.now())
    db.save_message('client_1', 'client_2', 'message4', datetime.now())
    print(db.get_history('client_1', 'client_2'))
    db.add_contact('contact1')
    print(db.get_contacts())
    db.add_contact('contact2')
    print(db.get_contacts())
    db.del_contact('contact1')
    print(db.get_contacts())


