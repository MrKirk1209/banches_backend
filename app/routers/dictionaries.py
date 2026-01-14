# app/routers/dictionaries.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.map.models import TypeOfSeat, Status, Pollution, Condition, Material, User
from app.pyd import schemas
from app.security import get_current_admin

dict_router = APIRouter(prefix="/dicts", tags=["Dictionaries"])

from app.pyd.schemas import (
    TypeOfSeatResponse, 
    StatusResponse, 
    PollutionResponse, 
    ConditionResponse, 
    MaterialResponse
)

@dict_router.get("/types", response_model=List[TypeOfSeatResponse])
async def get_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TypeOfSeat))
    return result.scalars().all()

@dict_router.get("/materials", response_model=List[MaterialResponse])
async def get_materials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Material))
    return result.scalars().all()

@dict_router.get("/conditions", response_model=List[ConditionResponse])
async def get_conditions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Condition))
    return result.scalars().all()

@dict_router.get("/pollutions", response_model=List[PollutionResponse])
async def get_pollutions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pollution))
    return result.scalars().all()

@dict_router.get("/statuses", response_model=List[StatusResponse])
async def get_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Status))
    return result.scalars().all()

@dict_router.post("/types", response_model=schemas.TypeOfSeatResponse, status_code=status.HTTP_201_CREATED)
async def create_type(
    item: schemas.TypeOfSeatCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    new_item = TypeOfSeat(name=item.name)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@dict_router.post("/materials", response_model=schemas.MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    item: schemas.MaterialCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    new_item = Material(name=item.name)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@dict_router.post("/conditions", response_model=schemas.ConditionResponse, status_code=status.HTTP_201_CREATED)
async def create_condition(
    item: schemas.ConditionCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    new_item = Condition(name=item.name)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@dict_router.post("/pollutions", response_model=schemas.PollutionResponse, status_code=status.HTTP_201_CREATED)
async def create_pollution(
    item: schemas.PollutionCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    new_item = Pollution(name=item.name)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

