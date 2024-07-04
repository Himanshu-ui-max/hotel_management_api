from fastapi import FastAPI, Depends
from sqlalchemy.orm import session
from . import crud, schemas
from .database import session_local
app = FastAPI(title="HIMS' Hotel Management")

def get_DB():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


@app.post("/create_admin", response_model=schemas.AdminOut)
async def get(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    return crud.create_admin(db, admin)

