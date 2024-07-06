import asyncio
from datetime import date

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db
from src.entity.models import Base, User
from src.services.auth import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "test_user",
    "email": "test_user@example.com",
    "password": "12345678",
}

test_contact = {
    "first_name": "test_name",
    "last_name": "test_last_name",
    "email": "test@example.com",
    "phone_number": "12345678",
    "birthday": date(2022, 1, 1),
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = auth_service.get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                password=hash_password,
                confirmed=False,
            )

            session.add(current_user)
            await session.commit()

            # current_contact = Contact(
            #     first_name=test_contact["first_name"],
            #     last_name=test_contact["last_name"],
            #     email=test_contact["email"],
            #     phone_number=test_contact["phone_number"],
            #     birthday=test_contact["birthday"],
            #     user_id=1,
            # )
            # session.add(current_contact)
            # await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    test_client.headers.update({"X-Forwarded-For": "127.0.0.1"})

    yield test_client


@pytest_asyncio.fixture()
async def get_token():
    token = await auth_service.create_access_token(data={"sub": test_user["email"]})
    return token


# pytest -v