import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.map.models import LocationSeat, Picture, User
from app.security import get_current_user
from app.pyd import schemas

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