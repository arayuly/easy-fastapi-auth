import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import BaseUser
from .schemas import UserCreate

class SQLAlchemyUserProvider:
    def __init__(self, user_model: type[BaseUser]):
        self.user_model = user_model

    async def get_by_email(self, session: AsyncSession, email: str) -> BaseUser | None:
        stmt = select(self.user_model).where(self.user_model.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, session: AsyncSession, user_id: uuid.UUID) -> BaseUser | None:
        stmt = select(self.user_model).where(self.user_model.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, user_in: UserCreate, hashed_password: str) -> BaseUser:
        db_user = self.user_model(
            email=user_in.email,
            hashed_password=hashed_password
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user