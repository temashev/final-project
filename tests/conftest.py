import pytest
import uuid

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.main import app
from app.db.database import get_db_session
from app.core.security import create_access_token
from app.db.models import *

test_engine = create_async_engine(settings.TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False)


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
async def register_user(client):
    '''
    Фабрика для быстрой регистрации пользователя
    '''

    async def _register(email: str, full_name: str):
        test_user_register_data = {
            'email': email,
            'full_name': full_name,
            'password': 'Password123',
            'confirm_password': 'Password123',
        }
        reg = await client.post('/auth/register/', json=test_user_register_data)
        assert reg.status_code == 200
        return test_user_register_data

    return _register


@pytest.fixture
async def create_registered_test_user_member(register_user, unique_email):
    await register_user(email=unique_email, full_name='test user member')


    test_token = create_access_token(
        data={'email': unique_email, 'role': 'member'}
    )
    return test_token


@pytest.fixture
async def create_registered_test_user_manager(register_user):
    manager_email = f'test_manager_{uuid.uuid4().hex[:6]}@example.com'

    await register_user(email=manager_email, full_name='test user manager')

    # Обращение к тестовой бд, чтобы изменить роль на менеджера, т.к. в бекенде жестко вшивается роль member для каждого
    async with TestingSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == manager_email))
        db_user = res.scalar_one()

        assert db_user is not None, 'Пользователь не найден в тестовой сессии БД'
        db_user.role = 'manager'
        await session.commit()


    test_token = create_access_token(
        data={'email': manager_email, 'role': 'member'}
    )
    return test_token



@pytest.fixture
async def test_team_with_member(unique_email, create_registered_test_user_member):
    """
    Создает команду и сразу добавляет в нее тестового пользователя
    """
    async with TestingSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == unique_email))
        db_user = res.scalar_one_or_none()

        new_team = Team(name="Тестовая команда", invite_code=uuid.uuid4().hex[:8])
        session.add(new_team)
        await session.flush()

        new_member = TeamMember(team_id=new_team.id, user_id=db_user.id)
        session.add(new_member)

        await session.commit()
        await session.refresh(new_team)

        return new_team


@pytest.fixture
async def test_team_with_manager(create_registered_test_user_manager):
    async with TestingSessionLocal() as session:
        res = await session.execute(select(User).where(User.role == 'manager'))
        db_user = res.scalars().all()[-1]

        new_team = Team(name="Команда менеджера", invite_code=uuid.uuid4().hex[:8])
        session.add(new_team)
        await session.flush()

        new_member = TeamMember(team_id=new_team.id, user_id=db_user.id)
        session.add(new_member)

        await session.commit()
        await session.refresh(new_team)

        return new_team
