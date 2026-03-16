import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def clean_database():
    print("🧹 Очистка базы данных...")
    
    async with async_session_maker() as session:
        # ТОЧНЫЕ названия таблиц из твоих моделей (проверь __tablename__):
        tables = [
            # Связи (удаляем первыми)
            "Location_seats_of_Reviews",
            
            # Контент (зависит от пользователей и справочников)
            "Pictures",
            "Reviews",
            "Complaints",  # ← добавлена сюда
            
            # Основные сущности
            "Location_seats",
            
            # Пользователи и роли
            "Users",
            "Roles",
            
            # Справочники (seed.py их восстановит)
            "Type_of_seats",
            "Statuses",
            "Materials",
            "Conditions",
            "Рollutions",  # ← русская Р из твоей модели Pollution
            
            # Жалобы (справочники)
            "Complaint_reasons",     # ← в модели ComplaintReason
            "Complaint_statuses",    # ← в модели ComplaintStatus
        ]
        
        # Оборачиваем в двойные кавычки для PostgreSQL (особенно важно для "Рollutions")
        tables_sql = ", ".join([f'"{t}"' for t in tables])
        statement = text(f"TRUNCATE TABLE {tables_sql} RESTART IDENTITY CASCADE;")
        
        try:
            await session.execute(statement)
            await session.commit()
            print("✅ База данных полностью очищена.")
            print(f"   🗂️  Очищено таблиц: {len(tables)}")
        except Exception as e:
            print(f"❌ Ошибка при очистке: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(clean_database())
