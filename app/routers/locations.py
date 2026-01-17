from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from decimal import Decimal
from app.database import get_db
from app.pyd.schemas import LocationSeatCreate, LocationSeatBase,LocationSeatResponse,LocationSeatUpdate
from app.pyd.base_models import LocationSeatBase
from app.security import get_current_user
from app.map.models import User,LocationSeat,Review,LocationSeatOfReview
from sqlalchemy.orm import selectinload
from app.map.models import Status
from app.security import get_current_user_or_none


locations_router = APIRouter(prefix="/locations", tags=["Locations"])
# cоздать локацию
@locations_router.post("/", response_model=LocationSeatResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationSeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --- 1. ПРОВЕРКА НА ДУБЛИКАТЫ (В самом начале) ---
    stmt = select(LocationSeat).where(
        LocationSeat.cord_x == location_data.cord_x,
        LocationSeat.cord_y == location_data.cord_y
    )
    result = await db.execute(stmt)
    existing_location = result.scalars().first()

    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Локация с такими координатами уже существует"
        )

    # --- 2. СОЗДАНИЕ ЛОКАЦИИ (Переменная new_location появляется здесь) ---
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
    
    # Важно: flush присваивает ID новой локации
    await db.flush() 

    # --- 3. ОБРАБОТКА ОТЗЫВА (Если есть) ---
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

    # Сохраняем всё в базу
    await db.commit()
    
    # --- 4. ПОДГОТОВКА ОТВЕТА (Строго В КОНЦЕ) ---
    # Мы используем new_location.id только тут, когда он уже точно существует
    stmt = (
        select(LocationSeat)
        .options(
            # Подгружаем цепочку: Отзывы -> Авторы отзывов -> Локация отзыва
            selectinload(LocationSeat.reviews).options(
                selectinload(Review.author),
                selectinload(Review.location_links)
            ),
            selectinload(LocationSeat.pictures),
            selectinload(LocationSeat.status_ref)   
        )
        .where(LocationSeat.id == new_location.id)
    )
    result = await db.execute(stmt)
    full_location = result.scalar_one()
    
    return full_location
    

# получить все локации
@locations_router.get("/", response_model=List[LocationSeatResponse])
async def get_locations(
    min_lat: Optional[Decimal] = None,
    max_lat: Optional[Decimal] = None,
    min_lon: Optional[Decimal] = None,
    max_lon: Optional[Decimal] = None,

    type_id: Optional[int] = None,
    status_id: Optional[int] = None, 
    

    current_user: Optional[User] = Depends(get_current_user_or_none),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(LocationSeat).options(

        selectinload(LocationSeat.reviews).options(
            selectinload(Review.author),
            selectinload(Review.location_links).selectinload(LocationSeatOfReview.location) 
        ),
        
        selectinload(LocationSeat.pictures),
        selectinload(LocationSeat.status_ref)
    )


    is_admin = False
    if current_user:

        if current_user.role_id == 1:
            is_admin = True
    
    if is_admin:
   
        pass 
    else:

        query = query.join(Status, LocationSeat.status == Status.id)
        query = query.where(Status.name.in_(["Активно", "На ремонте"]))


    if status_id:
        query = query.where(LocationSeat.status == status_id)

    # 5. Гео-фильтры
    if min_lat and max_lat and min_lon and max_lon:
        query = query.where(
            LocationSeat.cord_x >= min_lat,
            LocationSeat.cord_x <= max_lat,
            LocationSeat.cord_y >= min_lon,
            LocationSeat.cord_y <= max_lon
        )


    if type_id:
        query = query.where(LocationSeat.type == type_id)

    result = await db.execute(query)
    return result.scalars().all()

# удалить локацию
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
        raise HTTPException(status_code=404, detail="Такой локации не существует")

    is_admin = current_user.role_id == 1 
    is_author = location.author_id == current_user.id

    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="У вас нет прав администратора")


    await db.delete(location)
    await db.commit()
    
    return None
# получить мои локации
@locations_router.get("/my", response_model=List[LocationSeatResponse])
async def get_my_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    stmt = (
        select(LocationSeat)
        .options(

            selectinload(LocationSeat.reviews).options(
                selectinload(Review.location_links), 
                selectinload(Review.author)          
            ),
            
   
            selectinload(LocationSeat.pictures),
            

            selectinload(LocationSeat.status_ref)
        )
        .where(LocationSeat.author_id == current_user.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
#Получить полную информацию о локации
@locations_router.get("/{location_id}", response_model=LocationSeatResponse)
async def get_location_detail(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    stmt = (
        select(LocationSeat)
        .options(
            # Подгружаем всё необходимое для LocationSeatResponse + ReviewResponse
            selectinload(LocationSeat.reviews).options(
                selectinload(Review.location_links), # Для имени локации в отзыве (если надо)
                selectinload(Review.author)          # Для имени автора отзыва
            ),
            selectinload(LocationSeat.pictures),
            selectinload(LocationSeat.status_ref)
        )
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Ищем конкретную локацию по её ID, а не все локации автора
        .where(LocationSeat.id == location_id)
    )
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Такой локации не существует")
    
    # ... (дальше твоя логика проверки статусов, public_statuses и т.д.) ...
    
    # ПОВТОРЮ ЛОГИКУ ПРОВЕРКИ (на всякий случай):
    public_statuses = ["Активно", "На ремонте"]
    is_admin = current_user and getattr(current_user, 'role_id', None) == 1
    is_author = current_user and location.author_id == current_user.id
    status_name = location.status_ref.name if location.status_ref else ""

    if status_name not in public_statuses:
        if not (is_admin or is_author):
            raise HTTPException(status_code=404, detail="Такой локации не существует")
            
    return location
# обновить локацию
@locations_router.patch("/{location_id}", response_model=LocationSeatResponse)
async def update_location(
    location_id: int,
    location_update: LocationSeatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить данные локации (только автор или админ)"""

    stmt = (
        select(LocationSeat)
        .options(
            selectinload(LocationSeat.reviews).options(
                selectinload(Review.location_links),
                selectinload(Review.author)
            ),
            selectinload(LocationSeat.pictures),
            selectinload(LocationSeat.status_ref)
        )
        .where(LocationSeat.id == location_id) # Ищем просто по ID!
    )
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Такой локации не существует")


    is_admin = getattr(current_user, 'role_id', None) == 1
    is_author = location.author_id == current_user.id

    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="У вас нет прав администратора")


    update_data = location_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(location, key, value)

    await db.commit()
    await db.refresh(location)
    
    return location