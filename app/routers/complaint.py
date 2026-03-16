from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.map.models import LocationSeat, Picture, Review, User, Complaint
from app.pyd import ComplaintCreate
from app.security import get_current_admin, get_current_user
HIDDEN_STATUS_ID = 3
REASON_ALLOWED_TARGETS = {
    1: ["location_id", "review_id", "picture_id"],  # Спам — всё
    2: ["location_id"],           # Нет лавочки — только точка
    3: ["review_id", "location_id", "reported_user_id"],  # Оскорбление — отзыв или пользователь
    4: ["picture_id"],            # Порнография — только фото
}
complaint_router = APIRouter(prefix="/complaints", tags=["Complaints"])


async def apply_complaint_action(complaint: Complaint, db: AsyncSession):
    
    # 1 - Спам → удаляем объект
    if complaint.reason_id == 1:
        await _delete_target(complaint, db)
    
    # 2 - Нет лавочки → скрываем точку на проверку
    elif complaint.reason_id == 2:
        if complaint.location_id:
            location = await db.get(LocationSeat, complaint.location_id)
            if location:
                location.status = HIDDEN_STATUS_ID
    
    # 3 - Оскорбление → удаляем только контент, не баним
    elif complaint.reason_id == 3:
        await _delete_target(complaint, db)
        
    
    # 4 - Порнография → удаляем контент + баним
    elif complaint.reason_id == 4:
        await _delete_target(complaint, db)
        await _ban_author(complaint, db)
    

    await db.commit()


async def _delete_target(complaint: Complaint, db: AsyncSession):
    """Удаляет объект жалобы"""
    if complaint.review_id:
        obj = await db.get(Review, complaint.review_id)
    elif complaint.picture_id:
        obj = await db.get(Picture, complaint.picture_id)
    elif complaint.location_id:
        obj = await db.get(LocationSeat, complaint.location_id)
    else:
        return
    if obj:
        await db.delete(obj)


async def _ban_author(complaint: Complaint, db: AsyncSession):
    """Банит автора объекта или reported_user"""
    
    # Если жалоба напрямую на пользователя
    if complaint.reported_user_id:
        user = await db.get(User, complaint.reported_user_id)
    
    # Иначе находим автора контента
    elif complaint.review_id:
        review = await db.get(Review, complaint.review_id)
        user = await db.get(User, review.author_id) if review else None
    elif complaint.picture_id:
        picture = await db.get(Picture, complaint.picture_id)
        user = await db.get(User, picture.user_id) if picture else None
    else:
        return
    
    if user:
        user.is_banned = True

@complaint_router.post("/")
async def create_complaint(
    complaint_data: ComplaintCreate,
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    provided_targets = {
        "location_id": complaint_data.location_id,
        "review_id": complaint_data.review_id,
        "picture_id": complaint_data.picture_id,
        "reported_user_id": complaint_data.reported_user_id,
    }
    filled = [key for key, val in provided_targets.items() if val is not None]

    # Проверка что передан ровно один объект
    if len(filled) != 1:
        raise HTTPException(
            status_code=400, 
            detail="Укажите ровно один объект жалобы"
        )

    # Проверка соответствия причины и объекта
    target_field = filled[0]
    allowed = REASON_ALLOWED_TARGETS.get(complaint_data.reason_id, [])
    if target_field not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Эта причина не применима к данному объекту"
        )
    if complaint_data.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Вы не можете пожаловаться на себя")

    # ← Проверяем что объект жалобы существует
    if complaint_data.review_id:
        obj = await db.get(Review, complaint_data.review_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Отзыв не найден")

    if complaint_data.location_id:
        obj = await db.get(LocationSeat, complaint_data.location_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Точка не найдена")

    if complaint_data.picture_id:
        obj = await db.get(Picture, complaint_data.picture_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Фото не найдено")

    if complaint_data.reported_user_id:
        obj = await db.get(User, complaint_data.reported_user_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Пользователь не найден")


    stmt = select(Complaint).where(
        Complaint.author_id == current_user.id,
        Complaint.location_id == complaint_data.location_id,
        Complaint.review_id == complaint_data.review_id,
        Complaint.picture_id == complaint_data.picture_id,
        Complaint.reported_user_id == complaint_data.reported_user_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none() # Получаем первый результат или None
    
    if existing:
         raise HTTPException(status_code=400, detail="Вы уже отправляли жалобу на этот объект")

    # Создание новой жалобы
    new_complaint = Complaint(
        author_id=current_user.id,
        reason_id=complaint_data.reason_id,
        text=complaint_data.text,
        location_id=complaint_data.location_id,
        review_id=complaint_data.review_id,
        picture_id=complaint_data.picture_id,
        reported_user_id=complaint_data.reported_user_id
    )
    
    db.add(new_complaint)
    
    await db.commit() 
    
    return {"message": "Жалоба успешно отправлена"}

@complaint_router.get("/")
async def get_complaints(
    status_id: Optional[int] = None,      # фильтр по статусу
    reason_id: Optional[int] = None,      # фильтр по причине
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    
    stmt = select(Complaint).offset(skip).limit(limit)
    if status_id:
        stmt = stmt.where(Complaint.status_id == status_id)
    if reason_id:
        stmt = stmt.where(Complaint.reason_id == reason_id)
    
    result = await db.execute(stmt)
    return result.scalars().all()

# свои жалобы (для обычного пользователя)
@complaint_router.get("/my")
async def get_my_complaints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Complaint).where(Complaint.author_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

#одобрить или отклонить жалобу
@complaint_router.patch("/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: int,
    status_id: int,   # 2 = Одобрена, 3 = Отклонена
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if current_user.role.role_name not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    complaint = await db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    
    complaint.status_id = status_id
    complaint.resolved_by_id = current_user.id
    if status_id == 2:
        await apply_complaint_action(complaint, db)
    await db.commit()
    return {"message": "Статус жалобы обновлён"}


