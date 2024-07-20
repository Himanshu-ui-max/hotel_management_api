from pydantic import BaseModel, EmailStr
from typing import List, Union

class successResponse(BaseModel):
    message : str

class AnswerBase(BaseModel):
    answer : str

class AnswerDB(AnswerBase):
    id : int
    owner_id : int
    question_id : int

class AnswerIn(AnswerBase):
    question_id : int

class AnswerUser(AnswerBase):
    id : int
    question_title : str
    question_id : int

class AnswerOut(AnswerBase):
    id : int
    owner_name : str
    question_id : int

class QuestionBase(BaseModel):
    title : str
    Question : str
    tags : Union[List[str], None] = None

class QuestionDB(QuestionBase):
    owner_id : int
    answers : Union[List[AnswerDB], None] = None

class QuestionList(BaseModel):
    id : int
    title : str
    tags : list[str]
class QuestionIn(QuestionBase):
    pass
class QuestionOut(QuestionBase):
    id : int

class login(BaseModel):
    email : EmailStr
    password : str
    isAdmin : bool

class AdminBase(BaseModel):
    name : str
    email : EmailStr

class AdminIn(AdminBase):
    password : str
    admin_secret : str

class AdminOut(AdminBase):
    pass

class AdminDB(AdminBase):
    id : Union[int, None]  = None
    hashed_password : str

    class Config:
        from_attributes = True
class UserBase(BaseModel):
    name : str
    email : EmailStr
    

class UserIn(UserBase):
    password : str

class UserOut(UserBase):
    pass

class UserDB(UserBase):
    id : Union[int, None]  = None
    hashed_password : str
    questions : List[QuestionDB]
    answers : List[AnswerDB]
    class Config:
        from_attributes = True


class token_response(BaseModel):
    access_token : str
    token_type : str