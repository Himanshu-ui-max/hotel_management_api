from pydantic import BaseModel, EmailStr

class AdminBase(BaseModel):
    name : str
    email : EmailStr

class AdminIn(AdminBase):
    password : str

class AdminOut(AdminBase):
    pass

class AdminDB(AdminBase):
    id : int | None  = None
    hashed_password : str

    class Config:
        from_attributes = True
class CustomerBase(BaseModel):
    name : str
    email : EmailStr
    

class CustomerIn(CustomerBase):
    password : str

class CustomerOut(CustomerBase):
    pass

class CustomerDB(CustomerBase):
    id : int | None  = None
    hashed_password : str
    booking : int | None = None
    class Config:
        from_attributes = True


class token_response(BaseModel):
    access_token : str
    token_type : str