from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

security_schema_1 = OAuth2PasswordBearer(tokenUrl="/adminlogin")
security_schema_2 = OAuth2PasswordBearer(tokenUrl="/customerlogin")

@app.post("/adminlogin", response_model=schemas.token_response, tags=["admin"])
async def admin_login(db : session = Depends(get_DB), request : OAuth2PasswordRequestForm = Depends()):
    admin = crud.get_admin(db, request.username)
    if not admin:
        raise HTTPException(status_code=400, detail="Incorrect password or username")
    match_password = hashing.verify_password(request.password, admin.hashed_password)
    if not match_password:
        raise HTTPException(status_code=400, detail="Incorrect password or username")
    data = {
        "id" : admin.id
    }
    jwt_token = token.encode_token(data)
    return {
        "access_token" : jwt_token,
        "token_type" : "bearer"
    }



@app.post("/create_admin", response_model=schemas.AdminOut, tags=["admin"])
async def create_admin(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    admin_db = crud.get_admin(db,admin.email)
    if admin_db:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_admin(db, admin)


@app.delete("/delete_admin")
async def delete_admin(db : session = Depends(get_DB), Token : str = Depends(security_schema_1)):
    token_data = token.decode_token(Token)
    print("keys :" , token_data.keys())
    if "customer_id" in token_data.keys():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorised for this route")
    admin_id = token_data["id"]
    crud.delete_admin(db, admin_id)

@app.post("/create_customer", response_model=schemas.AdminOut, tags=["customer"])
async def create_customer(customer : schemas.CustomerIn, db : session = Depends(get_DB)):
    customer_db = crud.get_customer(db,customer.email)
    if customer_db:
        raise HTTPException(status_code=400, detail="User already exists")
    if crud.get_admin(db, customer.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin can not be a customer")
    return crud.create_customer(db, customer)

@app.post("/customerlogin", response_model=schemas.token_response, tags=["customer"])
async def customer_login(customer : OAuth2PasswordRequestForm = Depends(), db : session = Depends(get_DB)):
    customer_db = crud.get_customer(db, customer.username)
    if not customer_db:
        raise HTTPException(status_code=400, detail="Incorrect Password or email")
    if not hashing.verify_password(customer.password, customer_db.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect Password or email")
    token_data = {
        "customer_id" : customer_db.id
    }
    jwt_token = token.encode_token(token_data)
    return {
        "access_token" : jwt_token,
        "token_type" : "bearer"
    }

# @app.delete("/delete_customer", tags=["customer"])
# async def delete_customer(db : session = Depends(get_DB), Token : str = Depends(security_schema_2)):
#     token_data = token.decode_token(Token)
#     customer_id = token_data["customer_id"]
#     crud.delete_customer(db, customer_id)

