import uuid
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, Boolean

class Base(DeclarativeBase):
    pass

class BaseUser(Base):
    """
    Базовая модель пользователя.
    __abstract__ = True означает, что SQLAlchemy не будет создавать таблицу 
    для этого класса напрямую, только для его наследников.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)