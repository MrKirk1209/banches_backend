from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import Request
from app.map.models import User
from typing import Annotated, Optional
from app.database import get_db
import app.map.models as m
from app import config


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72] 
    password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, config.settings.SECRET_KEY, algorithm=config.settings.ALGORITHM
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
) -> m.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(m.User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


async def authenticate_user(
    username: str, password: str, db: AsyncSession
) -> Optional[m.User]:

    stmt = select(m.User).where(
        or_(m.User.email == username, m.User.Username == username)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()


    if not user or not verify_password(password, user.password):
        return None
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    
    if current_user.role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав администратора"
        )
    
    return current_user

async def get_current_user_or_none(
    token: Optional[str] = Depends(oauth2_scheme_optional), 
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    
    if not token:
        return None
    
    try:

        return await get_current_user(token=token, db=db)
    except Exception:

        return None