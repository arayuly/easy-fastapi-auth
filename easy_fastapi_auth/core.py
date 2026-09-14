import uuid
from datetime import timedelta
from typing import Callable
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserCreate, UserResponse, TokenResponse
from .security import SecurityManager
from .provider import SQLAlchemyUserProvider

class EasyAuth:
    def __init__(
        self,
        secret_key: str,
        provider: SQLAlchemyUserProvider,
        get_session_dep: Callable, # Dependency для получения сессии БД
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7
    ):
        self.security = SecurityManager(secret_key)
        self.provider = provider
        self.get_session = get_session_dep
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Схема OAuth2 для Swagger UI
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
        
        # Создаем роутер
        self.router = self._create_router()

    def _create_router(self) -> APIRouter:
        router = APIRouter()

        @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
        async def register(user_in: UserCreate, session: AsyncSession = Depends(self.get_session)):
            existing_user = await self.provider.get_by_email(session, user_in.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            hashed_pwd = self.security.hash_password(user_in.password)
            new_user = await self.provider.create(session, user_in, hashed_pwd)
            return new_user

        @router.post("/login", response_model=TokenResponse)
        async def login(
            form_data: OAuth2PasswordRequestForm = Depends(),
            session: AsyncSession = Depends(self.get_session)
        ):
            # В OAuth2 форма требует поле username, мы интерпретируем его как email
            user = await self.provider.get_by_email(session, form_data.username)
            if not user or not self.security.verify_password(form_data.password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            
            access_token = self.security.create_token(
                subject=str(user.id),
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )
            refresh_token = self.security.create_token(
                subject=str(user.id),
                expires_delta=timedelta(days=self.refresh_token_expire_days)
            )
            return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

        @router.get("/me", response_model=UserResponse)
        async def get_me(current_user = Depends(self.get_current_user)):
            return current_user

        return router

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)  # type: ignore (FastAPI resolved in runtime)
    ):
        """Зависимость (Dependency) для защиты приватных эндпоинтов"""
        user_id_str = self.security.decode_token(token)
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token format")

        user = await self.provider.get_by_id(session, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user