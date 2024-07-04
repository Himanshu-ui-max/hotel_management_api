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


