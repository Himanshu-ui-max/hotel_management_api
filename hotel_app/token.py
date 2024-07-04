from jose import jwt, JWTError
from datetime import timedelta, timezone, datetime

SECURITY_KEY = "HIMS' Management Systme"

def decode_token(token : dict):
    data = jwt.decode(token, algorithms=["HS256"], key=SECURITY_KEY)
    return data

def encode_token(data : dict, expire_time : timedelta | None = None):
    to_encode = data
    if(expire_time):
        to_encode.update({"exp" : datetime.now(timezone.utc) + expire_time})
    else:
        to_encode.update({"exp" : datetime.now(timezone.utc) + timedelta(minutes=30)})
    token = jwt.encode(to_encode, key=SECURITY_KEY)
    return token

