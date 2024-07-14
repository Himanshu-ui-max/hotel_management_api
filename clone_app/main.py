from fastapi import FastAPI, Depends, HTTPException, status, Header, Form, Query, Body, Path
from fastapi.responses import HTMLResponse, Response
from pydantic import EmailStr
from sqlalchemy.orm import session
from . import crud, schemas, hashing, token, models
from .database import session_local, engine, Base
app = FastAPI(title="HIMS' Stackoverflow")

Base.metadata.create_all(bind=engine)

def get_DB():
    db = session_local()
    try:
        yield db
    finally:
        db.close()



@app.get("/email_verification/{Token}", tags=["Email service"])
async def email_verification(Token : str = Path(...), db : session = Depends(get_DB)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    user_db = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="user not found")
    db.query(models.User).filter(models.User.id == user_id).update({models.User.is_verified : True})
    db.commit()
    response = """
    <!DOCTYPE html>
        <html lang="en">
        <head>
        <title>email verification sucessful</title>
        </head>
        <body>
            email verified successfuly you can log in now
        </body>
        </html>
    """
    return HTMLResponse(content=response, status_code=200)


@app.get("/email_verification_revoke/{email}", tags=["Email service"])
async def email_verification_revoke(email : EmailStr, db : session = Depends(get_DB)):
    try:
        User_db = db.query(models.User).filter(models.User.email == email).first()
        if not User_db:
            raise HTTPException(status_code=404, detail="User not found")
        if User_db.is_verified:
            raise HTTPException(status_code=400, detail="User already verified")
        db.query(models.User).filter(models.User.email == email).delete()
        db.commit()
        response = """
        <!DOCTYPE html>
            <html lang="en">
            <head>
            <title>email verification sucessful</title>
            </head>
            <body>
                email registration revoked successfuly
            </body>
            </html>
        """
        return HTMLResponse(content=response, status_code=200)
    except HTTPException as e:
        raise e
    except Exception as e:
        return e

@app.post("/login", tags=["admin", "User"])
async def login(db: session = Depends(get_DB), email : EmailStr = Form(...), password : str = Form(...), isAdmin : bool = Form(...)):
    try:
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
            User_db = crud.get_User(db, email)
            if not User_db:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
            if not User_db.is_verified:
                raise HTTPException(status_code=400, detail="User not verified")
            if not hashing.verify_password(password, User_db.hashed_password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
            data = {
                "User_id" : User_db.id
            }
            jwt_token = token.encode_token(data)
            return jwt_token
    except HTTPException as e:
        raise e
    except Exception as e:
        return e

@app.post("/create_admin", response_model=schemas.AdminOut, tags=["admin"])
async def create_admin(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    try:
        admin_db = crud.get_admin(db,admin.email)
        if admin_db:
            raise HTTPException(status_code=400, detail="User already exists")
        return crud.create_admin(db, admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Some Internal error occured")


@app.put("/update_admin_email", tags=["admin"], response_model= schemas.successResponse)
async def update_admin_email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    try:
        crud.update_admin_email(db, token_data["admin_id"], new_email)
        return {
            "message" : "email updated successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")



@app.put("/update_admin_password", tags=["admin"], response_model= schemas.successResponse)
async def update_admin_email(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    try:
        crud.update_admin_password(db, token_data["admin_id"], new_password)
        return {
            "message" : "password updated successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.delete("/delete_admin", tags=["admin"], response_model= schemas.successResponse)
async def delete_admin(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if "User_id" in token_data.keys():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorised for this route")
    admin_id = token_data["admin_id"]
    try:
        crud.delete_admin(db, admin_id)
        return {
            "message" : "Admin deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.post("/create_User", tags=["User"], response_model= schemas.successResponse)
async def create_User(User: schemas.UserIn, db: session = Depends(get_DB)):
    try:
        User_db = crud.get_User(db, User.email)
        if User_db:
            raise HTTPException(status_code=400, detail="User already exists")
        
        if crud.get_admin(db, User.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot be a User")
        
        crud.create_User(db, User)
        User_db = db.query(models.User).filter(models.User.email == User.email).first()
        data = {
            "User_id": User_db.id
        }
        jwt_token = token.encode_token(data)
        
        if await crud.send_verification_mail(jwt_token, User.email):
            return {
                "message": "Verification mail sent successfully"
            }
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Some internal error occurred")
    except HTTPException as e:
        # Catch specific HTTPExceptions and re-raise them
        raise e
    except Exception as e:
        # Log the exception details for debugging purposes
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Some internal error occurred")


@app.put("/update_User_email", tags=["User"], response_model= schemas.successResponse)
async def update_User_Email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    try:
        crud.update_User_email(db, token_data["User_id"], new_email)
        return {
            "message" : "email updated successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.put("/update_User_password", tags=["User"], response_model= schemas.successResponse)
async def update_User_password(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    try:
        crud.update_User_password(db, token_data["User_id"], new_password)
        return {
            "message" : "password updated successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
@app.put("/update_User_name", tags=["User"], response_model= schemas.successResponse)
async def update_User_name(db : session = Depends(get_DB), new_name : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    try:
        crud.update_User_name(db, token_data["User_id"], new_name)
        return {
            "message" : "name updated successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")


@app.post("/forget_password_otp_generation", tags=["User"], response_model= schemas.successResponse)
async def forget_password_otp_generation(user_mail : EmailStr, db : session  =Depends(get_DB)):
    if await crud.forget_password_otp_generation(user_mail,db):
        return {
            "message" : "otp sent to your mail successfuly"
        }
    raise HTTPException(status_code=500, detail="some internal error occured")

@app.post("/forget_password_otp_validation", tags=["User"], response_model= schemas.successResponse)
async def forget_password_otp_validation(user_mail : EmailStr = Form(...), otp : int = Form(...), new_password : str = Form(...), db : session = Depends(get_DB)):
    try:
        return crud.forget_password_otp_validation(db, user_mail, otp, new_password)
    except:
        raise HTTPException(status_code=500, detail="some internal error occured")

@app.delete("/delete_User", tags=["User"], response_model= schemas.successResponse)
async def delete_User(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid token")
    User_id = token_data["User_id"]
    try:
        crud.delete_User(db, User_id)
        return {
            "message" : "User deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")






@app.post("/create_question", tags=["Question"], response_model= schemas.successResponse)
async def create_question(question : schemas.QuestionIn, db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.create_question(db, user_id, question)
        return {
            "message" : "Question created successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.get("/get_questions", tags=["Question"], response_model=list[schemas.QuestionOut])
async def get_question(db: session = Depends(get_DB), pagenumber : int = Query(...), pagesize : int = Query(...)):
    try:
        return crud.get_questions(db, pagesize*(pagenumber - 1), pagesize)
    except:
        raise HTTPException(status_code=500, detail="some internal error occured")

@app.get("/get_question_by_id", tags=["Question"], response_model=schemas.QuestionOut)
async def get_question_by_id(db : session = Depends(get_DB), que_id : int = Query(...)):
    try:
        return crud.get_question_by_id(db, que_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
    

@app.get("/get_question_by_title", tags = ["Question"], response_model=list[schemas.QuestionOut])
async def get_question_by_title(title : str, db : session = Depends(get_DB)):
    try:
        questions = crud.get_questions_by_title(db, title)
        return questions
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.get("/get_questions_by_tags", tags=["Question"], response_model=list[schemas.QuestionOut])
async def get_question_by_tags(tags : list[str] = Query(...), db : session = Depends(get_DB)):
    try:
        questions = crud.get_question_by_tags(db, tags)
        return questions
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500 ,detail="Some Internal error occured")


@app.put("/edit_question", tags=["Question"], response_model= schemas.successResponse)
async def edit_question(question : schemas.QuestionIn, db : session = Depends(get_DB), ques_id : int = Query(...), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.edit_question(db, user_id, ques_id, question)
        return {
            "message" : "question edited successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.delete("/delete_question", tags=["Question"], response_model= schemas.successResponse)
async def delete_question(db : session = Depends(get_DB), ques_id : int = Query(...), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.delete_question(db, user_id, ques_id)
        return {
            "message" : "question deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
    

@app.post("/create_answer", tags=["Answer"], response_model= schemas.successResponse)
async def create_answer(answer : schemas.AnswerIn, db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.create_answer(db, user_id, answer)
        return {
            "message" : "success"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.get("/get_user_answers", tags=["Answer"], response_model=list[schemas.AnswerOut])
async def get_user_answers(db : session = Depends(get_DB), Token : str = Header(...)):
    try:
        data = token.decode_token(Token)
        user_id = data["User_id"]
        return crud.get_user_answers(db, user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.get("/get_answers_by_question_id", tags=["Answer"], response_model=list[schemas.AnswerOut])
async def get_answers_by_Question_id(que_id : int = Query(...), db : session = Depends(get_DB)):
    try:
        return crud.get_ans_by_que_id(db, que_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Some Internal error occured")


@app.put("/edit_answer", tags=["Answer"], response_model= schemas.successResponse)
async def edit_answer(db : session = Depends(get_DB), ans_id : int = Query(...), Token : str = Header(...), new_answer : schemas.AnswerBase = Body(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.edit_answer(db,user_id,ans_id,new_answer.answer)
        return {
            "message" : "answer  edited successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.delete("/delete_answer", tags=["Answer"], response_model= schemas.successResponse)
async def delete_answer(answer_id : int = Query(...), db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    try:
        crud.delete_answer(db, user_id, answer_id)
        return {
            "message" : "Answer deleted Successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
    


@app.delete("/admin_user_delete", tags=["Admin CRUD"], response_model= schemas.successResponse)
async def admin_user_delete(user_id : int = Query(...), db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    admin_id = data.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=400, detail="not authorised to delete this account")
    try:
        crud.admin_delete_user(db, user_id)
        return {
            "mesage" : "User deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
    
@app.delete("/admin_question_delete", tags=["Admin CRUD"], response_model= schemas.successResponse)
async def admin_question_delete(que_id : int = Query(...), db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    admin_id = data.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=400, detail="Not Authorised to delete this question")
    try:
        crud.admin_question_delete(db, que_id)
        return {
            "mesage" : "question deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")

@app.delete("/admin_answer_delete", tags=["Admin CRUD"], response_model= schemas.successResponse)
async def admin_answer_delete(ans_id : int = Query(...), db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    admin_id = data.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=400, detail="Not Authorised to delete this answer")
    try:
        crud.admin_answer_delete(db, ans_id)
        return {
            "mesage" : "answer deleted successfuly"
        }
    except HTTPException as e:
        raise e
    except:
        raise HTTPException(status_code=500, detail="Some Internal error occured")
    
