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

    

    location = await db.get(LocationSeat, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")


    file_extension = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_extension}"
    

    upload_dir = Path("uploads")
    destination_path = upload_dir / new_filename


    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        file.file.close()


    file_url = f"/static/{new_filename}"


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

    pic = await db.get(Picture, picture_id)
    if not pic:
        raise HTTPException(status_code=404, detail="Picture not found")


    is_admin = getattr(current_user, 'role_id', None) == 1
    is_uploader = pic.user_id == current_user.id

    if not (is_uploader or is_admin):
        raise HTTPException(status_code=403, detail="Not enough permissions")


    try:
        filename = pic.url.split("/")[-1] 
        file_path = f"uploads/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}") 


    await db.delete(pic)
    await db.commit()
    
    return None