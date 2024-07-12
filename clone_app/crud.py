from fastapi import HTTPException, status

from sqlalchemy import delete
from sqlalchemy.orm import session
from . import schemas, models, database, hashing
import spacy

nlp = spacy.load("en_core_web_lg")

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


def update_User_name(db : session, User_id : int, new_name : str):
    db.query(models.User).filter(models.User.id == User_id).update({models.User.name : new_name})
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



def get_questions_by_title(db : session, title: str):
    questions_db = db.query(models.Question).all()
    to_return : list[schemas.QuestionOut] = []
    for question in questions_db:
        if nlp(question.title).similarity(nlp(title)) >= 0.4:            
            data = {
                "id" : question.id,
                "title" : question.title,
                "Question" : question.question,
                "tags" : question.tags.split(",")
            }
            data = schemas.QuestionOut(**data)
            to_return.append(data)
    return to_return



def get_question_by_tags(db : session, tags : list[str]):
    tags_str = ""
    for i in range(0, len(tags)):
        if i == len(tags) - 1:
            tags_str += tags[i]
            break
        tags_str += (tags[i]+',')
    questions_db = db.query(models.Question).all()
    to_return : list[dict] = []
    for question in questions_db:
        if(nlp(tags_str).similarity(nlp(question.tags)) >= 0.4):
            data = {
                "id" : question.id,
                "title" : question.title,
                "Question" : question.question,
                "tags" : question.tags.split(",")
            }
            data = schemas.QuestionOut(**data)
            to_return.append(data)
    return to_return

def delete_question(db : session, user_id : int, ques_id : int):
    question_data = db.query(models.Question).filter(models.Question.id == ques_id).first()
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found")
    owner_id = question_data.owner_id
    if user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unauthorised to delete this question")
    db.query(models.Answer).filter(models.Answer.question_id == ques_id).delete()
    db.commit()
    db.query(models.Question).filter(models.Question.id == ques_id).delete()
    db.commit()

def edit_question(db : session, user_id : int, ques_id : int, question : schemas.QuestionIn):
    question_data = db.query(models.Question).filter(models.Question.id == ques_id).first()
    if not question_data:
        raise HTTPException(status_code=404, detail="question not found")
    owner_id = question_data.owner_id
    if user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unauthorised to edit this question")
    tags_str = ""
    for i in range(0, len(question.tags)):
        if i == len(question.tags) - 1:
            tags_str += question.tags[i]
            break
        tags_str += (question.tags[i] + ",")
    db.query(models.Question).filter(models.Question.id == ques_id).update({
        models.Question.title : question.title,
        models.Question.question : question.Question,
        models.Question.tags : tags_str
        })
    db.commit()

def create_answer(db : session, user_id : int, answer : schemas.AnswerIn):
    is_answer = db.query(models.Answer).filter(models.Answer.question_id == answer.question_id).filter(models.Answer.owner_id == user_id).first()
    if is_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already answered the question")
    answer_db = models.Answer(answer = answer.answer, question_id = answer.question_id, owner_id = user_id)
    db.add(answer_db)
    db.commit()
    db.refresh(answer_db)


def get_ans_by_que_id(db : session, que_id: int):
    answers = db.query(models.Answer).filter(models.Answer.question_id == que_id).all()
    to_return : list[dict] = []
    for answer in  answers:
        owner_name = db.query(models.User).filter(models.User.id == answer.owner_id).first().name
        data = {
            "owner_name" : owner_name,
            "answer" : answer.answer
        }
        to_return.append(data)

    return to_return

def edit_answer(db : session, user_id : int, ans_id : int , new_answer : str):
    answer_db = db.query(models.Answer).filter(models.Answer.id == ans_id).first()
    if not answer_db:
        raise HTTPException(status_code=404, detail="Answer not found")
    if user_id != answer_db.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not authorised to edit this answer")
    db.query(models.Answer).filter(models.Answer.id == ans_id).update({models.Answer.answer : new_answer})
    db.commit()

def delete_answer(db : session, user_id : int, answer_id : int):
    answer_data = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not answer_data:
        raise HTTPException(status_code=404, detail="Answer not found")
    if user_id != answer_data.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unauthorised to delete this question")
    db.query(models.Answer).filter(models.Answer.id == answer_id).delete()
    db.commit()


