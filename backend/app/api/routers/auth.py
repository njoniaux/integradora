from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sqlite3
import bcrypt

load_dotenv()

SECRET_KEY = "asdasd123123"
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

auth_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    email: str
    role: str

class UserInDB(User):
    password: str

def get_user(email: str):
    conn = sqlite3.connect("user_database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()
    if user:
        return UserInDB(email=user[1], password=user[2], role=user[3])

def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register")
async def register(email: str, password: str):
    conn = sqlite3.connect("user_database.db")
    cur = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cur.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                    (email, hashed_password.decode('utf-8'), "STUDENT"))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    conn.close()
    return {"message": "User registered successfully"}

@auth_router.post("/change_role")
async def change_role(email: str, new_role: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    conn = sqlite3.connect("user_database.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE email = ?", (new_role, email))
    conn.commit()
    conn.close()
    return {"message": f"Role updated for {email}"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
        return User(email=email, role=role)
    except JWTError:
        raise credentials_exception

def role_required(allowed_roles: list):
    def decorator(func):
        async def wrapper(current_user: User = Depends(get_current_user), *args, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Not authorized")
            return await func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator
