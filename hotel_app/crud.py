from sqlalchemy import delete
from sqlalchemy.orm import session
from . import schemas, models, database, hashing

def create_admin(db:session, admin : schemas.AdminIn):
    password = admin.password
    hashed = hashing.hash_password(password)
    data_db = models.Admin(name = admin.name, email = admin.email, hashed_password = hashed)
    print(data_db)
    db.add(data_db)
    db.commit()
    db.refresh(data_db)
    return schemas.AdminOut(**admin.dict())

def get_admin(db: session, email : str)->models.Admin | bool:
    admin = db.query(models.Admin).filter(models.Admin.email == email).first()
    if not admin:
        return False
    return admin

def update_admin_email(db : session, admin_id : int, new_email : str):
    db.query(models.Admin).filter(models.Admin.id == admin_id).update({models.Admin.email : new_email})
    db.commit()

def delete_admin(db : session, admin_id : int):
    db.query(models.Admin).filter(models.Admin.id == admin_id).delete()
    db.commit()


def create_customer(db:session, customer : schemas.CustomerIn):
    password = customer.password
    hashed = hashing.hash_password(password)
    data_db = models.Customer(name = customer.name, email = customer.email, hashed_password = hashed, Booking = 0)
    print(data_db)
    db.add(data_db)
    db.commit()
    db.refresh(data_db)
    return schemas.CustomerOut(**customer.dict())

def update_customer_email(db : session, customer_id : int, new_email : str):
    db.query(models.Customer).filter(models.Customer.id == customer_id).update({models.Customer.email : new_email})
    db.commit()

def get_customer(db: session, email : str)->models.Customer | bool:
    customer = db.query(models.Customer).filter(models.Customer.email == email).first()
    if not customer:
        return False
    return customer

def delete_customer(db : session, customer_id : int):
    db.query(models.Customer).filter(models.Customer.id == customer_id).delete()
    db.commit()