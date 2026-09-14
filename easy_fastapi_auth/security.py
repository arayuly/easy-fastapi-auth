import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta, timezone

class SecurityManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        """Хэширует пароль через Argon2"""
        return self.pwd_hasher.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Сравнивает чистый пароль и хэш"""
        try:
            return self.pwd_hasher.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    def create_token(self, subject: str, expires_delta: timedelta) -> str:
        """Создает JWT токен"""
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"sub": str(subject), "exp": expire}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> str | None:
        """Декодирует токен и возвращает subject (user_id)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None