from fastapi import FastAPI, Depends, HTTPException, status, Header, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import session
from . import crud, schemas, hashing, token
from .database import session_local, engine, Base
app = FastAPI(title="HIMS' Hotel Management")

Base.metadata.create_all(bind=engine)

def get_DB():
    db = session_local()
    try:
        yield db
    finally:
        db.close()




@app.post("/login", tags=["admin", "customer"])
async def login(db: session = Depends(get_DB), email : EmailStr = Form(...), password : str = Form(...), isAdmin : bool = Form(...)):
    if isAdmin:
        admin_db = crud.get_admin(db, email)
        if not admin_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        if not hashing.verify_password(password, admin_db.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        data = {
            "admin_id" : admin_db.id
        }
        jwt_token = token.encode_token(data)
        return jwt_token
    else:
        customer_db = crud.get_customer(db, email)
        if not customer_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        if not hashing.verify_password(password, customer_db.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        data = {
            "customer_id" : customer_db.id
        }
        jwt_token = token.encode_token(data)
        return jwt_token

@app.post("/create_admin", response_model=schemas.AdminOut, tags=["admin"])
async def create_admin(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    admin_db = crud.get_admin(db,admin.email)
    if admin_db:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_admin(db, admin)


@app.put("/update_admin_email", tags=["admin"])
async def update_admin_email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_admin_email(db, token_data["admin_id"], new_email)
    return {
        "message" : "email updated successfuly"
    }
@app.put("/update_admin_password", tags=["admin"])
async def update_admin_email(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_admin_password(db, token_data["admin_id"], new_password)
    return {
        "message" : "password updated successfuly"
    }

@app.delete("/delete_admin", tags=["admin"])
async def delete_admin(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if "customer_id" in token_data.keys():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorised for this route")
    admin_id = token_data["admin_id"]
    crud.delete_admin(db, admin_id)

@app.post("/create_customer", response_model=schemas.AdminOut, tags=["customer"])
async def create_customer(customer : schemas.CustomerIn, db : session = Depends(get_DB)):
    customer_db = crud.get_customer(db,customer.email)
    if customer_db:
        raise HTTPException(status_code=400, detail="User already exists")
    if crud.get_admin(db, customer.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin can not be a customer")
    return crud.create_customer(db, customer)

@app.put("/update_customer_email", tags=["customer"])
async def update_customer_Email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_customer_email(db, token_data["customer_id"], new_email)
    return {
        "message" : "email updated successfuly"
    }

@app.put("/update_customer_password", tags=["customer"])
async def update_customer_password(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_customer_password(db, token_data["customer_id"], new_password)
    return {
        "message" : "password updated successfuly"
    }


@app.delete("/delete_customer", tags=["customer"])
async def delete_customer(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid token")
    customer_id = token_data["customer_id"]
    crud.delete_customer(db, customer_id)

