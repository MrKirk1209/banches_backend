from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.map.models import User, Role
from app.pyd import schemas
from app.security import get_current_admin, get_password_hash

users_router = APIRouter(
    prefix="/users", 
    tags=["User Management (Admin)"],
    dependencies=[Depends(get_current_admin)] 
)

# 1. Получить список всех пользователей
@users_router.get("/", response_model=List[schemas.UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(
            selectinload(User.role),      
            selectinload(User.locations),  
            selectinload(User.reviews)     
        )
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()

# Создать пользователя (Вручную админом)
@users_router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    user_data: schemas.UserCreate, 
    role_id: int = 2, 
    db: AsyncSession = Depends(get_db)
):

    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    new_user = User(
        Username=user_data.Username,
        email=user_data.email,
        password=get_password_hash(user_data.password),
        role_id=role_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Удалить пользователя
@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await db.delete(user)
    await db.commit()
    return None

# Изменить роль 
@users_router.patch("/{user_id}/role", response_model=schemas.UserResponse)
async def change_user_role(
    user_id: int,
    role_id: int, # 1=Admin, 2=User
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    user.role_id = role_id
    await db.commit()
    await db.refresh(user)
    return user