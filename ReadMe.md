Запуск проекта
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

venv\scripts\activate

alembic revision --autogenerate -m "Name migration"

alembic upgrade head

python seed.py

pip freeze > requirements.txt