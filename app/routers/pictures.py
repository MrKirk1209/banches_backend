import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.map.models import LocationSeat, Picture, User
from app.security import get_current_user
from app.pyd import schemas
import os

pictures_router = APIRouter(prefix="/pictures", tags=["Pictures"])

@pictures_router.post("/upload", response_model=schemas.PictureResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    location_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    
    # 1. Проверяем существование локации
    location = await db.get(LocationSeat, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # 2. Генерируем уникальное имя файла
    # (чтобы user1.jpg не перезаписал user2.jpg)
    file_extension = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Путь сохранения на диске
    upload_dir = Path("uploads")
    destination_path = upload_dir / new_filename

    # 3. Сохраняем файл физически
    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        file.file.close()

    # 4. Формируем URL (относительный)
    # Android добавит базовый URL сервера (http://192.168.1.5:8000)
    file_url = f"/static/{new_filename}"

    # 5. Записываем в БД
    new_picture = Picture(
        url=file_url,
        location_id=location.id,
        user_id=current_user.id
        
    )

    db.add(new_picture)
    await db.commit()
    await db.refresh(new_picture)

    return new_picture

@pictures_router.delete("/{picture_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_picture(
    picture_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Ищем картинку
    pic = await db.get(Picture, picture_id)
    if not pic:
        raise HTTPException(status_code=404, detail="Picture not found")

    # 2. Проверка прав (Загрузивший юзер или Админ)
    is_admin = getattr(current_user, 'role_id', None) == 1
    is_uploader = pic.user_id == current_user.id

    if not (is_uploader or is_admin):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 3. Удаляем файл с диска
    # url у нас вида "/static/filename.jpg", нужно превратить в путь "uploads/filename.jpg"
    try:
        filename = pic.url.split("/")[-1] # Берем имя файла
        file_path = f"uploads/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}") # Логируем, но не крашим запрос

    # 4. Удаляем из БД
    await db.delete(pic)
    await db.commit()
    
    return None