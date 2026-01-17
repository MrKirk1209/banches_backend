
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.security import authenticate_user, create_access_token, verify_password
from app.database import async_session_maker
from app.config import settings
from jose import jwt, JWTError
from sqladmin.authentication import AuthenticationBackend
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Открываем сессию БД вручную, так как мы не внутри эндпоинта FastAPI
        async with async_session_maker() as session:
            user = await authenticate_user(username, password, session)
            
            # 1. Проверяем, существует ли юзер
            if not user:
                return False
            
            # 2. ПРОВЕРКА НА АДМИНА (Самое важное!)
            if user.role_id != 1:
                return False

            # 3. Если админ - создаем токен
            access_token = create_access_token(data={"sub": str(user.id)})
            
            # 4. Сохраняем токен в сессию браузера
            request.session.update({"token": access_token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        # Проверяем валидность токена
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            if user_id is None:
                return False
            # Можно дополнительно сходить в базу и проверить, не забанен ли юзер,
            # но для админки достаточно валидного JWT и проверки при входе.
            return True
        except JWTError:
            return False

# Инициализируем класс с секретным ключом
authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)