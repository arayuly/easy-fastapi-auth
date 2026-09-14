# easy-fastapi-auth

Ready-to-use authentication for FastAPI applications with async SQLAlchemy, Argon2 password hashing, and JWT access and refresh tokens.

## Features

- User registration with email validation
- Login through the standard OAuth2 password flow
- Argon2 password hashing
- JWT access and refresh tokens
- Async SQLAlchemy user provider
- Protected `GET /me` endpoint
- Pydantic v2 schemas

## Requirements

- Python 3.10+
- FastAPI
- An async SQLAlchemy database driver, such as `aiosqlite` or `asyncpg`

## Installation

```bash
pip install easy-fastapi-auth python-multipart aiosqlite
```

Install a different async SQLAlchemy driver when needed. For example, PostgreSQL users can install `asyncpg` instead of `aiosqlite`.

## Quick Start

The following example uses SQLite with `aiosqlite`:

```python
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import (
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)

from easy_fastapi_auth import Base, BaseUser, EasyAuth, SQLAlchemyUserProvider


class User(BaseUser):
	__tablename__ = "users"


engine = create_async_engine("sqlite+aiosqlite:///./app.db")
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
	async with session_factory() as session:
		yield session


async def create_tables() -> None:
	async with engine.begin() as connection:
		await connection.run_sync(Base.metadata.create_all)


app = FastAPI(title="My API")

auth = EasyAuth(
	secret_key="replace-this-with-a-long-random-secret",
	provider=SQLAlchemyUserProvider(User),
	get_session_dep=get_session,
	access_token_expire_minutes=15,
	refresh_token_expire_days=7,
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.on_event("startup")
async def on_startup() -> None:
	await create_tables()


@app.get("/private")
async def private_endpoint(current_user=Depends(auth.get_current_user)):
	return {"user_id": str(current_user.id), "email": current_user.email}
```

For production, load `secret_key` from an environment variable or a secret manager. Do not commit it to source control.

Start the application with:

```bash
uvicorn main:app --reload
```

Then open the interactive API documentation at <http://127.0.0.1:8000/docs>.

## API Endpoints

When the router is mounted with `prefix="/auth"`, the package exposes:

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Create a user with `email` and `password` |
| `POST` | `/auth/login` | Authenticate with OAuth2 form fields `username` and `password` |
| `GET` | `/auth/me` | Return the authenticated user |

The login response contains:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

Despite the OAuth2 field name, `username` must contain the user's email address.

Use the access token as a bearer token:

```http
Authorization: Bearer <access_token>
```

## User Model

Create your application user model by inheriting from `BaseUser`:

```python
from easy_fastapi_auth import BaseUser


class User(BaseUser):
	__tablename__ = "users"

	# Add application-specific fields here.
```

`BaseUser` provides:

- `id: UUID`
- `email: str` (unique and indexed)
- `hashed_password: str`
- `is_active: bool`

The default `SQLAlchemyUserProvider` expects these fields. You can implement a custom provider with the same async operations when your application needs different persistence logic.

## Configuration

`EasyAuth` accepts the following options:

| Option | Default | Description |
| --- | --- | --- |
| `secret_key` | required | Secret used to sign JWTs |
| `provider` | required | User provider instance |
| `get_session_dep` | required | FastAPI dependency returning an `AsyncSession` |
| `access_token_expire_minutes` | `15` | Access token lifetime |
| `refresh_token_expire_days` | `7` | Refresh token lifetime |

## Security Notes

- Use a strong, random secret key in production.
- Serve authentication endpoints over HTTPS.
- Store tokens securely on the client.
- The current release returns a refresh token but does not provide a refresh endpoint or token revocation store. Applications must implement refresh and revocation behavior if required.
- Deactivate a user by setting `is_active` to `False`; inactive users cannot access protected endpoints.

## License

This project is licensed under the [MIT License](LICENSE).

## Links

- [GitHub repository](https://github.com/arayuly/easy-fastapi-auth)
- [Issue tracker](https://github.com/arayuly/easy-fastapi-auth/issues)
