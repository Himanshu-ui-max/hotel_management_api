from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base 



class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)




class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    answers = relationship("Answer", back_populates="owner")
    questions = relationship("Question", back_populates="owner")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    question = Column(String)
    tags = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="questions")
    answers = relationship("Answer", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    answer = Column(String)
    question_id = Column(Integer, ForeignKey("questions.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="answers")
    questions = relationship("Question", back_populates="answers")