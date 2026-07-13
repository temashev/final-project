import pytest
import uuid

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.db.database import Base
from app.main import app
from app.db.database import get_db_session
from app.services.security import create_access_token
from app.db.models import *

test_engine = create_async_engine(settings.TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope='session', autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', timeout=5) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def unique_email():
    return f'test_{uuid.uuid4().hex[:6]}@example.com'


@pytest.fixture
async def create_registered_test_user_member(client, unique_email):
    test_user_register_data = {
        'email': unique_email,
        'full_name': 'test user member',
        'password': 'Password123',
        'confirm_password': 'Password123',
    }

    # Регистрация
    reg = await client.post('/users/register/', json=test_user_register_data)
    assert reg.status_code == 200

    # Замена имейла на sub, т.к. в get_current_user проверяется именно по ключу sub
    test_token = create_access_token(
        data={'sub': unique_email, 'role': 'member'}
    )

    return test_token


@pytest.fixture
async def create_registered_test_user_manager(client):
    manager_email = f'test_manager_{uuid.uuid4().hex[:6]}@example.com'

    test_user_register_data = {
        'email': manager_email,
        'full_name': 'test user manager',
        'password': 'Password123',
        'confirm_password': 'Password123',
    }

    # Регистрация
    reg = await client.post('/users/register/', json=test_user_register_data)
    assert reg.status_code == 200

    # Обращение к тестовой бд, чтобы изменить роль на менеджера, т.к. в бекенде жестко вшивается роль member для каждого
    async with TestingSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == manager_email))
        db_user = res.scalar_one_or_none()

        assert db_user is not None, "Пользователь не найден в тестовой сессии БД"

        if db_user:
            db_user.role = 'manager'
            await session.commit()

    # Замена имейла на sub, т.к. в get_current_user проверяется именно по ключу sub
    test_token = create_access_token(
        data={'sub': manager_email, 'role': 'manager'}
    )

    return test_token