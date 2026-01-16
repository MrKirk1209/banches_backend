import asyncio

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_maker
from app.map.models import User, Role,Status
from app.security import get_password_hash
fake = Faker("ru_RU")  


ROLES_DATA = ["admin", "user"]

STATUSES_DATA = [
    "Активно", 
    "На ремонте", 
    "Временно недоступно"
]

SEAT_TYPE_NAMES = [
    "Лавочка",
    "Беседка",
]

MATERIALS_DATA = [
    "Дерево", 
    "Металл", 
    "Бетон", 
    "Пластик", 
    "Комбинированный", 
    "Камень"
]

CONDITIONS_DATA = [
    "Идеальное", 
    "Хорошее", 
    "Удовлетворительное", 
    "Плохое", 
    "Аварийное"
]

POLLUTIONS_DATA = [
    "Чисто", 
    "Немного мусора", 
    "Грязно", 
    "Свалка", 
    "Переполнена урна"
]



async def seed_roles():
    """Сидинг ролей (Roles)"""
    from app.map.models import Role
    
    async with async_session_maker() as session:
        print("--- Начало сидинга ролей ---")
        
        stmt = select(Role.role_name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in ROLES_DATA:
            if name not in existing:
                print(f"Добавляем роль: {name}")
                to_add.append(Role(role_name=name))
            else:
                print(f"Роль существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг ролей завершен ---\n")


async def seed_default_users():
    """Сидинг администратора и тестового пользователя"""
    from app.map.models import User, Role
    
    async with async_session_maker() as session:
        print("--- Начало сидинга пользователей ---")

 
        admin_role = await session.scalar(select(Role).where(Role.role_name == "admin"))
        user_role = await session.scalar(select(Role).where(Role.role_name == "user"))

        if not admin_role or not user_role:
            print("❌ Ошибка: Роли не найдены. Сначала запустите seed_roles.")
            return


        existing_admin = await session.scalar(select(User).where(User.email == "admin@admin.com"))
        if not existing_admin:
            print("Создаем админа...")
            admin_user = User(
                Username="admin",
                email="admin@admin.com",
                password=get_password_hash("admin123"),
                role_id=admin_role.id
            )
            session.add(admin_user)
        else:
            print("Админ уже существует.")

        existing_user = await session.scalar(select(User).where(User.email == "user@user.com"))
        if not existing_user:
            print("Создаем тестового юзера...")
            test_user = User(
                Username="user",
                email="user@user.com",
                password=get_password_hash("user123"),
                role_id=user_role.id
            )
            session.add(test_user)
        else:
            print("Тестовый юзер уже существует.")

        await session.commit()
        print("--- Сидинг пользователей завершен ---\n")


async def seed_statuses():
    """Сидинг статусов (Statuses)"""
    from app.map.models import Status
    
    async with async_session_maker() as session:
        print("--- Начало сидинга статусов ---")
        
        stmt = select(Status.name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in STATUSES_DATA:
            if name not in existing:
                print(f"Добавляем статус: {name}")
                to_add.append(Status(name=name))
            else:
                print(f"Статус существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг статусов завершен ---\n")


async def seed_materials():
    """Сидинг материалов (Material)"""
    from app.map.models import Material
    
    async with async_session_maker() as session:
        print("--- Начало сидинга материалов ---")
        
        stmt = select(Material.name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in MATERIALS_DATA:
            if name not in existing:
                print(f"Добавляем материал: {name}")
                to_add.append(Material(name=name))
            else:
                print(f"Материал существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг материалов завершен ---\n")


async def seed_conditions():
    """Сидинг состояний (Condition)"""
    from app.map.models import Condition
    
    async with async_session_maker() as session:
        print("--- Начало сидинга состояний ---")
        
        stmt = select(Condition.name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in CONDITIONS_DATA:
            if name not in existing:
                print(f"Добавляем состояние: {name}")
                to_add.append(Condition(name=name))
            else:
                print(f"Состояние существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг состояний завершен ---\n")


async def seed_pollutions():
    """Сидинг загрязнений (Pollution)"""
    from app.map.models import Pollution
    
    async with async_session_maker() as session:
        print("--- Начало сидинга загрязнений ---")
        
        stmt = select(Pollution.name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in POLLUTIONS_DATA:
            if name not in existing:
                print(f"Добавляем загрязнение: {name}")
                to_add.append(Pollution(name=name))
            else:
                print(f"Загрязнение существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг загрязнений завершен ---\n")


async def seed_types_of_seat():
    """Сидинг типов мест (TypeOfSeat)"""
    from app.map.models import TypeOfSeat
    
    async with async_session_maker() as session:
        print("--- Начало сидинга типов мест ---")
        
        stmt = select(TypeOfSeat.name)
        result = await session.execute(stmt)
        existing = set(result.scalars().all())
        
        to_add = []
        for name in SEAT_TYPE_NAMES:
            if name not in existing:
                print(f"Добавляем тип: {name}")
                to_add.append(TypeOfSeat(name=name))
            else:
                print(f"Тип существует: {name}")
        
        if to_add:
            session.add_all(to_add)
            await session.commit()
        print("--- Сидинг типов мест завершен ---\n")


async def main():
    print("🚀 Запуск посева данных...")
    

    await seed_roles()
    

    await seed_default_users()
    

    await seed_statuses()
    await seed_types_of_seat()
    await seed_materials()
    await seed_pollutions()
    await seed_conditions()

    print("\n🎉 Посев завершён!")
    print("=" * 40)
    print("👑 Администратор:")
    print("  Email: admin@admin.com")
    print("  Пароль: admin123")
    print()
    print("👤 Пользователь:")
    print("  Email: user@user.com")
    print("  Пароль: user123")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())