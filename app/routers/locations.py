from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from decimal import Decimal
from app.database import get_db
from app.pyd.schemas import LocationSeatCreate, LocationSeatBase,LocationSeatResponse
from app.pyd.base_models import LocationSeatBase
from app.security import get_current_user
from app.map.models import User,LocationSeat,Review,LocationSeatOfReview
from sqlalchemy.orm import selectinload
locations_router = APIRouter(prefix="/locations", tags=["Locations"])

@locations_router.post("/", response_model=LocationSeatResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationSeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_location = LocationSeat(
        name=location_data.name,
        description=location_data.description,
        address=location_data.address,
        type=location_data.type,
        cord_x=location_data.cord_x,
        cord_y=location_data.cord_y,
        status=location_data.status,
        author_id=current_user.id

    )
    db.add(new_location)
    await db.flush()


    
    if location_data.first_review:
        review_in = location_data.first_review
        

        new_review = Review(
            rate=review_in.rate,
            pollution_id=review_in.pollution_id,
            condition_id=review_in.condition_id,
            material_id=review_in.material_id,
            seating_positions=review_in.seating_positions,
            author_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(new_review)
        await db.flush() 

        link = LocationSeatOfReview(
            locations_id=new_location.id,
            reviews_id=new_review.id
        )
        db.add(link)

    await db.commit()
    

    stmt = (
        select(LocationSeat)
        .options(
            selectinload(LocationSeat.reviews),   
            selectinload(LocationSeat.pictures)   
        )
        .where(LocationSeat.id == new_location.id)
    )
    result = await db.execute(stmt)
    full_location = result.scalar_one()
    
    return full_location

@locations_router.get("/", response_model=List[LocationSeatResponse])
async def get_locations(
    # Фильтры для видимой области карты (Bounding Box)
    min_lat: Optional[Decimal] = None,
    max_lat: Optional[Decimal] = None,
    min_lon: Optional[Decimal] = None,
    max_lon: Optional[Decimal] = None,
    # Твои старые фильтры
    type_id: Optional[int] = None,
    status_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(LocationSeat).options(
        selectinload(LocationSeat.reviews),
        selectinload(LocationSeat.pictures)
    )

    # Логика "Квадрата": ищем точки внутри границ
    if min_lat and max_lat and min_lon and max_lon:
        query = query.where(
            LocationSeat.cord_x >= min_lat,
            LocationSeat.cord_x <= max_lat,
            LocationSeat.cord_y >= min_lon,
            LocationSeat.cord_y <= max_lon
        )

    # Остальные фильтры
    if type_id:
        query = query.where(LocationSeat.type == type_id)
    if status_id:
        query = query.where(LocationSeat.status == status_id)

    result = await db.execute(query)
    return result.scalars().all()


    
@locations_router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    stmt = select(LocationSeat).where(LocationSeat.id == location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    is_admin = current_user.role_id == 1 
    is_author = location.author_id == current_user.id

    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="You do not have permission to delete this location")


    await db.delete(location)
    await db.commit()
    
    return None

@locations_router.get("/my", response_model=List[LocationSeatResponse])
async def get_my_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    stmt = (
        select(LocationSeat)
        .options(
            selectinload(LocationSeat.reviews),
            selectinload(LocationSeat.pictures)
        )
        .where(LocationSeat.author_id == current_user.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

  