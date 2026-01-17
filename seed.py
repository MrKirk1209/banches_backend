import asyncio
import random
from decimal import Decimal
from datetime import datetime

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_maker
from app.map.models import (
    User, Role, Status, TypeOfSeat, Material, 
    Condition, Pollution, LocationSeat, Review, LocationSeatOfReview
)
from app.security import get_password_hash

fake = Faker("ru_RU")

# --- КОНСТАНТЫ ---

ROLES_DATA = ["admin", "user"]

STATUSES_DATA = ["Активно", "На ремонте", "Временно недоступно"]
SEAT_TYPE_NAMES = ["Лавочка", "Беседка"]
MATERIALS_DATA = ["Дерево", "Металл", "Бетон", "Пластик", "Комбинированный", "Камень"]
CONDITIONS_DATA = ["Идеальное", "Хорошее", "Удовлетворительное", "Плохое", "Аварийное"]
POLLUTIONS_DATA = ["Чисто", "Немного мусора", "Грязно", "Свалка", "Переполнена урна"]

# Координаты Нижнего Тагила (Центр)
TAGIL_LAT = 57.9194
TAGIL_LON = 59.9650

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ СИДИНГА СПРАВОЧНИКОВ ---

async def seed_roles(session: AsyncSession):
    print("--- Сидинг ролей ---")
    stmt = select(Role.role_name)
    existing = (await session.execute(stmt)).scalars().all()
    existing_set = set(existing)
    
    for name in ROLES_DATA:
        if name not in existing_set:
            session.add(Role(role_name=name))
    await session.commit()

async def seed_simple_dict(session: AsyncSession, model, data_list, dict_name):
    print(f"--- Сидинг {dict_name} ---")
    stmt = select(model.name)
    existing = (await session.execute(stmt)).scalars().all()
    existing_set = set(existing)
    
    for name in data_list:
        if name not in existing_set:
            session.add(model(name=name))
    await session.commit()

async def seed_default_users(session: AsyncSession):
    print("--- Сидинг дефолтных пользователей ---")
    admin_role = (await session.execute(select(Role).where(Role.role_name == "admin"))).scalar_one_or_none()
    user_role = (await session.execute(select(Role).where(Role.role_name == "user"))).scalar_one_or_none()

    if not admin_role or not user_role:
        print("❌ Роли не найдены!")
        return

    # Админ
    if not (await session.execute(select(User).where(User.email == "admin@admin.com"))).scalar_one_or_none():
        session.add(User(Username="admin", email="admin@admin.com", password=get_password_hash("admin123"), role_id=admin_role.id))
    
    # Юзер
    if not (await session.execute(select(User).where(User.email == "user@user.com"))).scalar_one_or_none():
        session.add(User(Username="user", email="user@user.com", password=get_password_hash("user123"), role_id=user_role.id))
    
    await session.commit()

# --- ГЕНЕРАЦИЯ РАНДОМНОГО КОНТЕНТА (Тагил) ---

async def seed_random_content(session: AsyncSession, users_count=10, locations_count=20, reviews_count=30):
    print(f"\n🎲 Генерация рандомных данных для Нижнего Тагила...")
    
    # 1. Получаем ID справочников
    user_role = (await session.execute(select(Role).where(Role.role_name == "user"))).scalar_one()
    
    types = (await session.execute(select(TypeOfSeat))).scalars().all()
    statuses = (await session.execute(select(Status))).scalars().all()
    materials = (await session.execute(select(Material))).scalars().all()
    conditions = (await session.execute(select(Condition))).scalars().all()
    pollutions = (await session.execute(select(Pollution))).scalars().all()

    if not all([types, statuses, materials, conditions, pollutions]):
        print("❌ Сначала заполните справочники!")
        return

    # 2. Создаем рандомных юзеров
    created_users = []
    print(f"   👤 Создаем {users_count} пользователей...")
    for _ in range(users_count):
        profile = fake.simple_profile()
        email = f"{random.randint(1000,9999)}_{profile['mail']}" # Уникализируем email
        
        user = User(
            Username=profile['username'],
            email=email,
            password=get_password_hash("123123"),
            role_id=user_role.id
        )
        session.add(user)
        created_users.append(user)
    
    await session.commit()
    # Обновляем объекты юзеров, чтобы получить их ID
    for u in created_users: await session.refresh(u)
    
    # Добавим дефолтного юзера в пул авторов
    default_user = (await session.execute(select(User).where(User.email == "user@user.com"))).scalar_one_or_none()
    if default_user: created_users.append(default_user)

    # 3. Создаем локации в Нижнем Тагиле
    created_locations = []
    print(f"   📍 Создаем {locations_count} локаций в Нижнем Тагиле...")
    
    for _ in range(locations_count):
        # Генерируем координаты вокруг центра Тагила (разброс ~5-7 км)
        # 1 градус широты ~ 111 км. 0.05 ~ 5.5 км.
        lat = Decimal(TAGIL_LAT + random.uniform(-0.05, 0.05))
        lon = Decimal(TAGIL_LON + random.uniform(-0.08, 0.08))
        
        loc = LocationSeat(
            name=f"{random.choice(['Скамейка', 'Беседка', 'Место отдыха'])} на {fake.street_name()}",
            description=fake.sentence(nb_words=10),
            address=fake.address(),
            type=random.choice(types).id,
            status=random.choice(statuses).id,
            cord_x=lat,
            cord_y=lon,
            author_id=random.choice(created_users).id
        )
        session.add(loc)
        created_locations.append(loc)
    
    await session.commit()
    for l in created_locations: await session.refresh(l)

    # 4. Создаем отзывы
    print(f"   ⭐ Создаем {reviews_count} отзывов...")
    
    for _ in range(reviews_count):
        target_location = random.choice(created_locations)
        author = random.choice(created_users)
        
        # Создаем сам отзыв
        review = Review(
            rate=random.randint(1, 5),
            pollution_id=random.choice(pollutions).id,
            condition_id=random.choice(conditions).id,
            material_id=random.choice(materials).id,
            seating_positions=random.randint(2, 6),
            author_id=author.id,
            created_at=datetime.utcnow()
        )
        session.add(review)
        await session.flush() # Получаем ID отзыва

        # Связываем отзыв и локацию (Many-to-Many)
        link = LocationSeatOfReview(
            locations_id=target_location.id,
            reviews_id=review.id
        )
        session.add(link)

    await session.commit()
    print("✅ Рандомные данные успешно сгенерированы!")


# --- MAIN ---

async def main():
    print("🚀 Запуск посева данных...")
    
    async with async_session_maker() as session:
        # 1. Базовые справочники
        await seed_roles(session)
        await seed_default_users(session)
        
        await seed_simple_dict(session, Status, STATUSES_DATA, "Статусы")
        await seed_simple_dict(session, TypeOfSeat, SEAT_TYPE_NAMES, "Типы мест")
        await seed_simple_dict(session, Material, MATERIALS_DATA, "Материалы")
        await seed_simple_dict(session, Condition, CONDITIONS_DATA, "Состояния")
        await seed_simple_dict(session, Pollution, POLLUTIONS_DATA, "Загрязнения")
        
        # 2. Рандомные данные (Пользователи -> Локации -> Отзывы)
        # Можно настроить количество здесь
        await seed_random_content(
            session, 
            users_count=10, 
            locations_count=30, 
            reviews_count=50
        )

    print("\n🎉 Посев завершён!")
    print("=" * 40)
    print("👑 Администратор: admin@admin.com / admin123")
    print("👤 Пользователь: user@user.com / user123")
    print(f"📍 Локации сгенерированы вокруг координат: {TAGIL_LAT}, {TAGIL_LON}")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(main())