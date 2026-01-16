from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.database import get_db
from app.security import get_current_user
from app.map.models import User, Review, LocationSeat, LocationSeatOfReview
from app.pyd import schemas

reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])
# cоздать обзор
@reviews_router.post("/", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location = await db.get(LocationSeat, review_data.location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Локация {review_data.location_id} не найдена"
        )
    stmt = (
        select(Review)
        .join(LocationSeatOfReview, Review.id == LocationSeatOfReview.reviews_id)
        .where(
            Review.author_id == current_user.id,
            LocationSeatOfReview.locations_id == location.id
        )
    )
    result = await db.execute(stmt)
    existing_review = result.scalar_one_or_none()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обзор уже существует, просим изменить его"
        )
    new_review = Review(
        rate=review_data.rate,
        pollution_id=review_data.pollution_id,
        condition_id=review_data.condition_id,
        material_id=review_data.material_id,
        seating_positions=review_data.seating_positions,
        author_id=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.add(new_review)
    await db.flush() 

    new_link = LocationSeatOfReview(
        locations_id=location.id,
        reviews_id=new_review.id
    )
    db.add(new_link)
     
    await db.commit()
    await db.refresh(new_review)

    new_review.location_id = location.id
    return new_review

#вывести все обзоры по локации с пагинацией
@reviews_router.get("/location/{location_id}", response_model=List[schemas.ReviewResponse])
async def get_location_reviews(
    location_id: int,
    limit: int = 10, 
    offset: int = 0,  
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Review)
        .options(selectinload(Review.location_links))
        .join(LocationSeatOfReview, Review.id == LocationSeatOfReview.reviews_id)
        .where(LocationSeatOfReview.locations_id == location_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    
    for r in reviews:
        r.location_id = location_id
        
    return reviews


#вывести все обзоры пользователя
@reviews_router.get("/user/my", response_model=List[schemas.ReviewResponse])
async def get_my_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Review)
        .options(selectinload(Review.location_links))
        .where(Review.author_id == current_user.id)
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()


    for r in reviews:
        if r.location_links:
            r.location_id = r.location_links[0].locations_id
            
    return reviews


#вывести один обзор
@reviews_router.get("/{review_id}", response_model=schemas.ReviewResponse)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Review)
        .options(selectinload(Review.location_links))
        .where(Review.id == review_id)
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Обзор не найден")

    if review.location_links:
        review.location_id = review.location_links[0].locations_id

    return review


#изменить обзор
@reviews_router.patch("/{review_id}", response_model=schemas.ReviewResponse)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    stmt = (
        select(Review)
        .options(selectinload(Review.location_links))
        .where(Review.id == review_id)
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Обзор не найден")


    is_admin = current_user.role_id == 1
    is_author = review.author_id == current_user.id

    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="Недостаточно прав администратора")


    update_data = review_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(review, key, value)

    await db.commit()
    await db.refresh(review)


    if review.location_links:
        review.location_id = review.location_links[0].locations_id

    return review

#удалить обзор
@reviews_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = await db.get(Review, review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Обзор не найден")

    is_admin = current_user.role_id == 1
    is_author = review.author_id == current_user.id

    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="У вас нет прав администратора")

    await db.delete(review)
    await db.commit()

    return None

