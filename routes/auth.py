import configparser
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from database_models import (User, UserCreate, UserInDB, check_username,
                             create_new_user, retrieve_user)
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

config = configparser.ConfigParser()
config.read_file(open("./.config"))

SECRET_KEY = config.get("auth_config", "SECRET_KEY")
ALGORITHM =  config.get("auth_config", "ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get("auth_config", "ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str):
    user = await retrieve_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = retrieve_user(username)
    if user is None:
        raise credentials_exception
    return await user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    
    return current_user


@router.post("/users/register")
async def register_new_user(user_create: UserCreate):
    print("pies")
    if user_create.password != user_create.password_confirmed:
        raise HTTPException(409, {"message":"Password does not match."})
    # if check_username(user_create.username):
    #     raise HTTPException(409, {"message": "User already exists"})
    hashed_pwd = get_password_hash(user_create.password)
    template_for_db = UserInDB(
        username=user_create.username,
        hashed_password=hashed_pwd
    )
    user = await create_new_user(template_for_db)
    print(user)
    
    return Response(status_code=201, content={"message": "Account created succesfully"})
    