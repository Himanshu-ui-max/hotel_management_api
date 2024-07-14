from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import delete
from sqlalchemy.orm import session
from . import schemas, models, database, hashing
import spacy
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from dotenv import dotenv_values
import random


env_values = dotenv_values(".env")
env_values = dict(env_values)
config = ConnectionConfig(
    MAIL_USERNAME =env_values["USER"],
    MAIL_PASSWORD = env_values["PASSWORD"],
    MAIL_FROM = env_values["USER"],
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

nlp = spacy.load("en_core_web_lg")

def create_admin(db:session, admin : schemas.AdminIn):
    if admin.admin_secret != env_values["ADMIN_SECRET"]:
        raise HTTPException(status_code=400, detail="Not authorised to be admin")
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
    data_db = models.User(name = User.name, email = User.email, hashed_password = hashed, is_verified = False, otp = 0)
    print(data_db)
    db.add(data_db)
    db.commit()
    db.refresh(data_db)
    return schemas.UserOut(**User.dict())

async def send_verification_mail(token : str, user_mail : EmailStr):
    template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <title>mail service</title>
        </head>
        <body>
            <p>Sign up process invoked <a href="http://localhost:8000/email_verification/{token}">click here</a> to verify</p>
            <p> <b>NOT YOU </b><a href="http://localhost:8000/email_verification_revoke/{user_mail}">click here</a> to revoke</p>
        </body>
        </html>

    """
    message = MessageSchema(
       subject="Email verification for stackoverflow clone",
       recipients=[user_mail],  # List of recipients, as many as you can pass  
       body = template,
       subtype="html"
       )
    try:
        print("working")
        fm = FastMail(config=config)
        await fm.send_message(message)
        return True
    except:
        print("message not sent")
        return False

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

async def forget_password_otp_generation(user_mail : EmailStr, db : session)->bool:
    print("working")
    user_db = db.query(models.User).filter(models.User.email == user_mail).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    otp = random.randint(100000, 999999)
    db.query(models.User).filter(models.User.email == user_mail).update({models.User.otp : otp})
    db.commit()
    template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <title>mail service</title>
        </head>
        <body>
            <p>otp to reset passwoed is {otp}</p>
        </body>
        </html>
    """
    message = MessageSchema(
       subject="OTP to reset password",
       recipients=[user_mail],  # List of recipients, as many as you can pass  
       body = template,
       subtype="html"
       )
    try:
        fm = FastMail(config=config)
        await fm.send_message(message=message)
        return True
    except:
        return False
    
def forget_password_otp_validation(db : session, user_mail : EmailStr, otp : int, new_password):
    user_db = db.query(models.User).filter(models.User.email == user_mail).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="user not found")
    if otp != user_db.otp:
        raise HTTPException(status_code=400, detail="invalid OTP")
    new_hashed_password = hashing.hash_password(new_password)
    db.query(models.User).filter(models.User.email == user_mail).update({
        models.User.hashed_password : new_hashed_password,
        models.User.otp : 0
    })
    db.commit()
    return {
        "message" :"password reset succesfull"
    }

def get_User(db: session, email : str) -> models.User | bool:
    User = db.query(models.User).filter(models.User.email == email).first()
    if not User:
        return False
    return User

def delete_User(db : session, User_id : int):
    is_user = db.query(models.User).filter(models.User.id == User_id).first()
    if  not is_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(models.User).filter(models.User.id == User_id).delete()
    user_questions = db.query(models.Question).filter(models.Question.owner_id == User_id).all()
    for question in user_questions:
        question_id = question.id
        db.query(models.Answer).filter(models.Answer.question_id == question_id).delete()
    db.query(models.Question).filter(models.Question.owner_id == User_id).delete()
    db.query(models.Answer).filter(models.Answer.owner_id == User_id).delete()
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

def get_questions(db : session, start : int, end : int):
    question_db = db.query(models.Question).offset(start).limit(end).all()
    to_return : list[schemas.QuestionOut] = []
    for question in question_db:
        data = {
                "id" : question.id,
                "title" : question.title,
                "Question" : question.question,
                "tags" : question.tags.split(",")
        }
        to_return.append(data)
    return to_return

def get_question_by_id(db : session, que_id : int):
    question = db.query(models.Question).filter(models.Question.id == que_id).first()
    if not question:
        raise HTTPException(404, "Question not found")
    data = {
        "id" : question.id,
        "title" : question.title,
        "Question" : question.question,
        "tags" : question.tags.split(",")
    }
    return schemas.QuestionOut(**data)


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
    que_db = db.query(models.Question)
    for tag in tags:
        que_db = que_db.filter(models.Question.tags.like(f"%{tag}%"))
        print(que_db)
    to_return : list[dict] = []
    for question in que_db.all():
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


def get_user_answers(db : session, user_id):
    answers = db.query(models.Answer).filter(models.Answer.owner_id == user_id).all()
    to_return : list[schemas.AnswerOut] = []
    for answer in  answers:
        owner_name = db.query(models.User).filter(models.User.id == answer.owner_id).first().name
        data = {
            "id" : answer.id,
            "owner_name" : owner_name,
            "answer" : answer.answer,
            "question_id" : answer.question_id
        }
        to_return.append(schemas.AnswerOut(**data))

    return to_return

def get_ans_by_que_id(db : session, que_id: int):
    answers = db.query(models.Answer).filter(models.Answer.question_id == que_id).all()
    to_return : list[schemas.AnswerOut] = []
    for answer in  answers:
        owner_name = db.query(models.User).filter(models.User.id == answer.owner_id).first().name
        data = {
            "id" : answer.id,
            "owner_name" : owner_name,
            "answer" : answer.answer,
            "question_id" : answer.question_id
        }
        to_return.append(schemas.AnswerOut(**data))

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


def admin_delete_user(db : session, user_id: int):
    user_db = db.query(models.User).filter((models.User.id == user_id)).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(models.User).filter(models.User.id == user_id).delete()
    question_db = db.query(models.Question).filter(models.Question.owner_id == user_id).all()
    db.query(models.Question).filter(models.Question.owner_id == user_id).delete()
    for question in question_db:
        db.query(models.Answer).filter(models.Answer.question_id == question.id).delete()
    db.query(models.Answer).filter(models.Answer.owner_id == user_id).delete()
    db.commit()
    
def admin_question_delete(db : session, que_id : int):
    que_db = db.query(models.Question).filter(models.Question.id == que_id).first()
    if not que_db:
        raise HTTPException(status_code=404, detail="question not found")
    db.query(models.Question).filter(models.Question.id == que_id).delete()
    db.commit()

def admin_answer_delete(db : session, ans_id : int):
    ans_db = db.query(models.Answer).filter(models.Answer.id == ans_id).first()
    if not ans_db:
        raise HTTPException(status_code=404, detail="answer not found")
    db.query(models.Answer).filter(models.Answer.id == ans_id).delete()
    db.commit()