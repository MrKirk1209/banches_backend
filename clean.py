import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def clean_database():
    print("🧹 Очистка базы данных...")
    
    async with async_session_maker() as session:
        # Список таблиц, которые нужно очистить.
        # ВАЖНО: Используй точные названия таблиц из БД (обычно они совпадают с __tablename__)
        # CASCADE удалит зависимые данные (например, удаляя User, удалит и его Review)
        tables = [
            "Location_seats_of_Reviews", # Связи удаляем первыми (или вместе с остальными)
            "Pictures",
            "Reviews",
            "Location_seats",
            "Users",
            "Roles",
            # Справочники тоже чистим, seed.py их заново создаст
            "Type_of_seats",
            "Statuses",
            "Materials",
            "Conditions",
            "Рollutions" # Скопируй название точно как в модели (у тебя там русская Р была?)
        ]
        
        # Формируем SQL запрос: TRUNCATE TABLE table1, table2... RESTART IDENTITY CASCADE;
        # RESTART IDENTITY - сбрасывает ID обратно к 1.
        # CASCADE - игнорирует ограничения внешних ключей при удалении.
        tables_sql = ", ".join([f'"{t}"' for t in tables]) # Оборачиваем в кавычки на случай спецсимволов
        statement = text(f"TRUNCATE TABLE {tables_sql} RESTART IDENTITY CASCADE;")
        
        try:
            await session.execute(statement)
            await session.commit()
            print("✅ База данных полностью очищена.")
        except Exception as e:
            print(f"❌ Ошибка при очистке: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(clean_database())