import json

from models.models import ClientHistory, Client, Contacts


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def get(self, db, _id):
        return db.query(self.model).filter(self.model.id == _id).first()

    def get_multi(self, db, *, skip, limit=100):
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db, *, obj_in):
        obj_in_data = json.load(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db, *, _id):
        obj = db.query(self.model).get(_id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDContact(CRUDBase):
    def get(self, db, _id):
        return db.query(self.model).filter(self.model.client_id == _id)

    def remove(self, db, *, contact_id, client_id):
        obj = db.query(self.model).filter(Contacts.contact_id == contact_id and Contacts.client_id == client_id).first()
        db.delete(obj)
        db.commit()
        return obj


client = CRUDBase(Client)
client_history = CRUDBase(ClientHistory)
contacts = CRUDBase(Contacts)
