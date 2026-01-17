from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.map.models import User, Role
from app.pyd import schemas
from app.config import settings
from app.security import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_current_user
)

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """Аутентификация пользователя и получение JWT токена"""
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": str(user.id), "username": user.Username}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", response_model=schemas.Token)
async def register(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    
    # Проверяем, существует ли пользователь с таким email или username
    existing_user = await db.execute(
        select(User).where(
            or_(
                User.email == user_data.email,
                User.Username == user_data.Username
            )
        )
    )
    
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или именем уже существует"
        )
    
    # Если role_id не указан, присваиваем роль "user" по умолчанию
    default_role = await db.execute(select(Role).where(Role.role_name == "user"))
    role = default_role.scalar_one_or_none()
    role_id_to_set = role.id if role else 2

    
    # Создаем нового пользователя
    new_user = User(
        Username=user_data.Username,
        email=user_data.email,
        password=get_password_hash(user_data.password),
        role_id=role_id_to_set
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": str(new_user.id), "username": new_user.Username}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=schemas.UserBase)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Получить информацию о текущем пользователе"""
    return current_user

