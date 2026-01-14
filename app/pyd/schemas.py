from datetime import datetime
from .base_models import *
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from .base_models import UserBase,LocationSeatBase

class RoleSchema(RoleBase):
    id: int = Field(None, gt=0, example=1)
    role_name: str = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)

class UserSchema(UserBase):
    id: int = Field(..., gt=0, example=1)
    role_id: int = Field(..., gt=0, example=2)

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):

    password: str = Field(..., min_length=6, example="strongpassword123")
    password_confirm: str = Field(..., min_length=6, example="strongpassword123")

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('Пароли не совпадают')
        return self
    
    model_config = ConfigDict(from_attributes=True)
class UserLogin(UserBase):
    email: str = Field(..., max_length=255, example="kolbasa@gmail.com")
    password: str = Field(..., min_length=6, example="strongpassword123")


    model_config = ConfigDict(from_attributes=True)

    
class ReviewCreateNested(ReviewBase):
    location_id: Optional[int] = Field(None, exclude=True)

  

class LocationSeatCreate(LocationSeatBase):
    name: str = Field(min_length=1, max_length=255, example="Скамейка в парке")
    description: str = Field(min_length=1, max_length=1000, example="Удобная скамейка с видом на озеро")
    address: str = Field( min_length=1, max_length=500, example="ул. Пушкина, д. 10")
    type: int = Field( gt=0, example=1)
    cord_x: Decimal = Field(example=55.7558)
    cord_y: Decimal = Field(example=37.6173)
    status: int = Field(gt=0, example=1)
    first_review: Optional[ReviewCreateNested] = None
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Схема для JWT токена"""
    access_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """Данные в JWT токене"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
class ReviewCreate(ReviewBase):

    location_id: int = Field(..., gt=0, description="ID локации, к которой пишем отзыв")

class ReviewResponse(ReviewBase):
    id: int
    author_id: int      
    created_at: datetime

class PollutionCreate(PollutionBase):
    pass

class PollutionResponse(PollutionBase):
    id: int

# --- CONDITIONS ---
class ConditionCreate(ConditionBase):
    pass

class ConditionResponse(ConditionBase):
    id: int

# --- MATERIALS ---
class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int

# --- TYPES ---
class TypeOfSeatCreate(TypeOfSeatBase):
    pass

class TypeOfSeatResponse(TypeOfSeatBase):
    id: int

# --- STATUSES ---
class StatusCreate(StatusBase):
    pass

class StatusResponse(StatusBase):
    id: int

class LocationSeatResponse(LocationSeatBase):
    id: int
    
    author_id: int

    reviews: List["ReviewResponse"] = [] 
    
    pictures: List[PictureResponse] = [] 
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: str  
        }
    )