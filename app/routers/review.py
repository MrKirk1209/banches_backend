from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.security import get_current_user
from app.map.models import User, Review, LocationSeat, LocationSeatOfReview
from app.pyd import schemas

reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])

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
            detail=f"Location with id {review_data.location_id} not found"
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
    await db.flush() # Получаем new_review.id


    new_link = LocationSeatOfReview(
        locations_id=location.id,
        reviews_id=new_review.id
    )
    db.add(new_link)

    await db.commit()
    await db.refresh(new_review)

    new_review.location_id = location.id 
    
    return new_review