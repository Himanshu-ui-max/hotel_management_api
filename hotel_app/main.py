from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import session
from . import crud, schemas, hashing, token
from .database import session_local
app = FastAPI(title="HIMS' Hotel Management")

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
async def get(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    admin_db = crud.get_admin(db,admin.email)
    if admin_db:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_admin(db, admin)

