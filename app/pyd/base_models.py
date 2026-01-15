from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator,ConfigDict
from decimal import Decimal

class UserBase(BaseModel):
    Username: str = Field(..., max_length=255, example="kolbasa")
    email: str = Field(..., max_length=255, example="kolbasa@gmail.com")

    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    id: int = Field(None, gt=0, example=1)
    role: str = Field(None, max_length=255, example="Администратор")

    model_config = ConfigDict(from_attributes=True)
class LocationSeatBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, example="Скамейка в парке")
    description: str = Field(min_length=1, max_length=1000, example="Описание")
    address: str = Field(min_length=1, max_length=500, example="Адрес")
    
    # ID справочников должны быть положительными
    type: int = Field(gt=0, example=1)
    status: int = Field(gt=0, example=1)

    # --- КООРДИНАТЫ ---

    cord_x: Decimal = Field(example=55.7558, description="Широта (Latitude)")
    cord_y: Decimal = Field(example=37.6173, description="Долгота (Longitude)")
    
    # --- ВАЛИДАТОРЫ (Разрешаем отрицательные) ---
    
    @field_validator('cord_x')
    def validate_cord_x(cls, v):
        # Широта (Latitude) бывает от -90 (Юг) до 90 (Север)
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Широта (cord_x) должна быть между -90 и 90')
        return v
    
    @field_validator('cord_y')
    def validate_cord_y(cls, v):
        # Долгота (Longitude) бывает от -180 (Запад) до 180 (Восток)
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Долгота (cord_y) должна быть между -180 и 180')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: str}
    )

class ReviewBase(BaseModel):
    # Оценка от 1 до 5
    rate: int = Field(..., ge=1, le=5, example=4, description="Оценка от 1 до 5")
    
    pollution_id: int = Field(..., gt=0, example=1)
    condition_id: int = Field(..., gt=0, example=1)
    material_id: int = Field(..., gt=0, example=1)
    seating_positions: int = Field(..., gt=0, example=4)
    
    # location_id лежит здесь, как основа
    location_id: Optional[int] = Field(None, gt=0, example=1)
    
    model_config = ConfigDict(from_attributes=True)
class PictureResponse(BaseModel):
    id: int
    url: str
    user_id: int 

    model_config = ConfigDict(from_attributes=True)

class PollutionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Сильно загрязнено")
    model_config = ConfigDict(from_attributes=True)

class ConditionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Требует ремонта")
    model_config = ConfigDict(from_attributes=True)

class MaterialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Дерево")
    model_config = ConfigDict(from_attributes=True)

class TypeOfSeatBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Беседка")
    model_config = ConfigDict(from_attributes=True)

class StatusBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Активно")
    model_config = ConfigDict(from_attributes=True)