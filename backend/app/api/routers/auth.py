from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import sqlite3
import bcrypt
from enum import Enum

SECRET_KEY = "asdasd123123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3600

auth_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Role(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    email: str
    role: Role

class UserInDB(User):
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    role: Role

    @validator('role')
    def validate_role(cls, v):
        if v not in Role.__members__.values():
            raise ValueError('Invalid role')
        return v
    
class UserLogin(BaseModel):
    email: str
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
async def login_for_access_token(user_data: UserLogin):
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register")
async def register(user: UserRegister):
    conn = sqlite3.connect("user_database.db")
    cur = conn.cursor()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    try:
        cur.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                    (user.email, hashed_password.decode('utf-8'), user.role.value))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    conn.close()
    return {"message": "User registered successfully"}

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

class ChangeRoleRequest(BaseModel):
    email: str
    new_role: Role

@auth_router.post("/change_role")
async def change_role(request: ChangeRoleRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    conn = sqlite3.connect("user_database.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE email = ?", (request.new_role.value, request.email))
    conn.commit()
    conn.close()
    return {"message": f"Role updated for {request.email}"}

def role_required(allowed_roles: list):
    def decorator(func):
        async def wrapper(current_user: User = Depends(get_current_user), *args, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Not authorized")
            return await func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator