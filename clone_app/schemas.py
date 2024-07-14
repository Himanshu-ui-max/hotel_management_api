from pydantic import BaseModel, EmailStr


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


class AnswerOut(AnswerBase):
    owner_name : str

class QuestionBase(BaseModel):
    title : str
    Question : str
    tags : list[str] | None = None

class QuestionDB(QuestionBase):
    owner_id : int
    answers : list[AnswerDB] | None = None

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
    id : int | None  = None
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
    id : int | None  = None
    hashed_password : str
    questions : list[QuestionDB]
    answers : list[AnswerDB]
    class Config:
        from_attributes = True


class token_response(BaseModel):
    access_token : str
    token_type : str