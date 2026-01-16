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

class ConditionCreate(ConditionBase):
    pass

class ConditionResponse(ConditionBase):
    id: int


class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int


class TypeOfSeatCreate(TypeOfSeatBase):
    pass

class TypeOfSeatResponse(TypeOfSeatBase):
    id: int


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
class UserResponse(UserBase):

    id: int
    role_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewUpdate(BaseModel):

    rate: Optional[int] = Field(None, ge=1, le=5)
    pollution_id: Optional[int] = Field(None, gt=0)
    condition_id: Optional[int] = Field(None, gt=0)
    material_id: Optional[int] = Field(None, gt=0)
    seating_positions: Optional[int] = Field(None, gt=0)

    model_config = ConfigDict(from_attributes=True)

class LocationSeatUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    address: Optional[str] = Field(None, max_length=500)
    type: Optional[int] = Field(None, gt=0)
    status: Optional[int] = Field(None, gt=0)
    cord_x: Optional[Decimal] = None
    cord_y: Optional[Decimal] = None

    @field_validator('cord_x')
    def validate_cord_x(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('cord_x должен быть между -180 и 180')
        return v
    
    @field_validator('cord_y')
    def validate_cord_y(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('cord_y должен быть между -90 и 90')
        return v

    model_config = ConfigDict(from_attributes=True)

