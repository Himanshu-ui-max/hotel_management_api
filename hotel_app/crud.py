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


def update_admin_password(db : session, admin_id : int, new_password : str):
    new_hashed_password = hashing.hash_password(new_password)
    db.query(models.Admin).filter(models.Admin.id == admin_id).update({models.Admin.hashed_password : new_hashed_password})
    db.commit()

def delete_admin(db : session, admin_id : int):
    db.query(models.Admin).filter(models.Admin.id == admin_id).delete()
    db.commit()


def create_User(db:session, User : schemas.UserIn):
    password = User.password
    hashed = hashing.hash_password(password)
    data_db = models.User(name = User.name, email = User.email, hashed_password = hashed)
    print(data_db)
    db.add(data_db)
    db.commit()
    db.refresh(data_db)
    return schemas.UserOut(**User.dict())

def update_User_email(db : session, User_id : int, new_email : str):
    db.query(models.User).filter(models.User.id == User_id).update({models.User.email : new_email})
    db.commit()

def update_User_password(db : session, User_id : int, new_password : str):
    new_hashed_password = hashing.hash_password(new_password)
    db.query(models.User).filter(models.User.id == User_id).update({models.User.hashed_password : new_hashed_password})
    db.commit()

def get_User(db: session, email : str)->models.User | bool:
    User = db.query(models.User).filter(models.User.email == email).first()
    if not User:
        return False
    return User

def delete_User(db : session, User_id : int):
    db.query(models.User).filter(models.User.id == User_id).delete()
    db.commit()


def create_question(db : session, user_id : int, question : schemas.QuestionIn):
    tags = question.tags
    tags_db = ""
    for i in range(0, len(tags)):
        if i == len(tags) - 1:
            tags_db += tags[i]
            break
        tags_db += tags[i] + ","
    
    question_db = models.Question(owner_id = user_id, title = question.title, question = question.Question, tags = tags_db)
    db.add(question_db)
    db.commit()
    db.refresh(question_db)