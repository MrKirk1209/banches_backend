from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import ForeignKey, String, DECIMAL, TIMESTAMP, BigInteger,UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, created_at, updated_at, str_uniq


class Role(Base):
    __tablename__ = 'Roles'
    id: Mapped[int_pk]
    role_name: Mapped[str_uniq]

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="role", cascade="all, delete"
    )   
    def __str__(self):
        return self.role_name
class User(Base):
    __tablename__ = 'Users'
    
    id: Mapped[int_pk]
    Username: Mapped[str] 
    email: Mapped[str] 
    password: Mapped[str]
    
    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('Roles.id', name='fk_user_role'),  # ← ЯВНОЕ указание ForeignKey
        nullable=True, 
        default=None
    )
    locations: Mapped[List['LocationSeat']] = relationship(
        back_populates='author',
        foreign_keys='LocationSeat.author_id'
    )
    reviews: Mapped[List['Review']] = relationship(
        back_populates='author',
        foreign_keys='Review.author_id'
    )
    role: Mapped[Optional["Role"]] = relationship(
        "Role", 
        back_populates="users",
        foreign_keys=[role_id]  
    )
    def __str__(self):
        return self.Username

class TypeOfSeat(Base):
    __tablename__ = 'Type_of_seats'
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    
    locations: Mapped[List['LocationSeat']] = relationship(
        back_populates='type_ref',
        foreign_keys='LocationSeat.type'
    )

    def __str__(self):
        return self.name
class Status(Base):
    __tablename__ = 'Statuses'
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    
    locations: Mapped[List['LocationSeat']] = relationship(
        back_populates='status_ref',
        foreign_keys='LocationSeat.status'
    )

    def __str__(self):
        return self.name
class LocationSeat(Base):
    __tablename__ = 'Location_seats'
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))
    type: Mapped[int] = mapped_column(ForeignKey('Type_of_seats.id'))
    cord_x: Mapped[Decimal] = mapped_column(DECIMAL(20, 15))
    cord_y: Mapped[Decimal] = mapped_column(DECIMAL(20, 15))
    author_id: Mapped[int] = mapped_column(ForeignKey('Users.id'))
    status: Mapped[int] = mapped_column(ForeignKey('Statuses.id'))
    
    
    # --- Отношения ---
    author: Mapped['User'] = relationship(
        back_populates='locations',
        foreign_keys=[author_id]
    )
    type_ref: Mapped['TypeOfSeat'] = relationship(
        back_populates='locations',
        foreign_keys=[type]
    )
    status_ref: Mapped['Status'] = relationship(
        back_populates='locations',
        foreign_keys=[status]
    )

    # --- Связь с отзывами ---
    # 1. Прямой доступ к списку отзывов (только для чтения)
    reviews: Mapped[List['Review']] = relationship(
        "Review",
        secondary='Location_seats_of_Reviews',
        back_populates='locations',
        viewonly=True 
    )
    
    # 2. Доступ к промежуточным объектам (для добавления/удаления связей)
    review_links: Mapped[List['LocationSeatOfReview']] = relationship(
        "LocationSeatOfReview",
        back_populates='location',
        cascade="all, delete-orphan"
    )
    
    pictures: Mapped[List['Picture']] = relationship(
        "Picture",
        back_populates='location',
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.name

    
class Picture(Base):
    __tablename__ = 'Pictures' # Лучше назвать во множественном числе
    
    id: Mapped[int_pk]
    url: Mapped[str] = mapped_column(String(255))
    
    # Ссылка на лавочку (Вместо промежуточной таблицы)
    location_id: Mapped[int] = mapped_column(ForeignKey('Location_seats.id', ondelete="CASCADE"))
    
    # Ссылка на того, кто загрузил (Исправил timestamp на ForeignKey)
    user_id: Mapped[int] = mapped_column(ForeignKey('Users.id'))
    

    location: Mapped['LocationSeat'] = relationship(
        "LocationSeat",
        back_populates='pictures'
    )
    
    # Связь с юзером (чтобы знать автора фото)
    uploader: Mapped['User'] = relationship(
        "User",
        foreign_keys=[user_id]
    )

class Pollution(Base):
    __tablename__ = 'Рollutions'  # Сохраняем русскую букву
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    
    reviews: Mapped[List['Review']] = relationship(
        back_populates='pollution_ref',
        foreign_keys='Review.pollution_id'
    )

    def __str__(self):
        return self.name
class Condition(Base):
    __tablename__ = 'Conditions'
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    
    reviews: Mapped[List['Review']] = relationship(
        back_populates='condition_ref',
        foreign_keys='Review.condition_id'
    )

    def __str__(self):
        return self.name
class Material(Base):
    __tablename__ = 'Materials'
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255))
    
    reviews: Mapped[List['Review']] = relationship(
        back_populates='material_ref',
        foreign_keys='Review.material_id'
    )

    def __str__(self):
        return self.name
class Review(Base):
    __tablename__ = 'Reviews'
    
    id: Mapped[int_pk]
    rate: Mapped[int] = mapped_column(BigInteger)
    author_id: Mapped[int] = mapped_column(ForeignKey('Users.id'))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)
    pollution_id: Mapped[int] = mapped_column(ForeignKey('Рollutions.id'))
    condition_id: Mapped[int] = mapped_column(ForeignKey('Conditions.id'))
    material_id: Mapped[int] = mapped_column(ForeignKey('Materials.id'))
    seating_positions: Mapped[int] = mapped_column(BigInteger)
    
    # Отношения
    author: Mapped['User'] = relationship(
        back_populates='reviews',
        foreign_keys=[author_id]
    )
    pollution_ref: Mapped['Pollution'] = relationship(
        back_populates='reviews',
        foreign_keys=[pollution_id]
    )
    condition_ref: Mapped['Condition'] = relationship(
        back_populates='reviews',
        foreign_keys=[condition_id]
    )
    material_ref: Mapped['Material'] = relationship(
        back_populates='reviews',
        foreign_keys=[material_id]
    )
    
    # --- Связь с локациями ---
    # 1. Прямой доступ к списку локаций (только для чтения)
    locations: Mapped[List['LocationSeat']] = relationship(
        "LocationSeat",
        secondary='Location_seats_of_Reviews',
        back_populates='reviews',
        viewonly=True 
    )
    
    # 2. Доступ к промежуточным объектам
    location_links: Mapped[List['LocationSeatOfReview']] = relationship(
        "LocationSeatOfReview",
        back_populates='review',
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"Отзыв {self.id} (Оценка: {self.rate})"
class LocationSeatOfReview(Base):
    __tablename__ = 'Location_seats_of_Reviews'
    
    id: Mapped[int_pk]
    locations_id: Mapped[int] = mapped_column(ForeignKey('Location_seats.id'))
    reviews_id: Mapped[int] = mapped_column(ForeignKey('Reviews.id'))
    
    # Связи с объектами
    location: Mapped['LocationSeat'] = relationship(
        back_populates='review_links',
        foreign_keys=[locations_id]
    )
    review: Mapped['Review'] = relationship(
        back_populates='location_links',
        foreign_keys=[reviews_id]
    )
    
    __table_args__ = (
        UniqueConstraint('locations_id', 'reviews_id', name='unique_location_review'),
    )


