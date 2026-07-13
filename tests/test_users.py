import pytest


@pytest.mark.asyncio
async def test_register_user(client, unique_email):
    payload = {
        'email': unique_email,
        'full_name': 'Test user',
        'password': 'TestPass1',
        'confirm_password': 'TestPass1'
    }

    response = await client.post('/users/register/', json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data['email'] == unique_email
    assert data['full_name'] == 'Test user'
    assert data['role'] == 'member'
    assert 'password' not in data


@pytest.mark.asyncio
@pytest.mark.login
async def test_register_and_login_user_pipeline(client, unique_email):
    password = 'TestPass1'

    registered_payload = {
        'email': unique_email,
        'full_name': 'Test user',
        'password': password,
        'confirm_password': password
    }

    payload = {
        'email': unique_email,
        'password': password,
    }

    await client.post('/users/register/', json=registered_payload)
    response = await client.post('/users/login/', json=payload)

    assert response.status_code == 200

    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


@pytest.mark.asyncio
async def test_register_duplicate_email(client, unique_email):
    password = 'TestPass1'

    payload_1 = {
        'email': unique_email,
        'full_name': 'Test user 1',
        'password': password,
        'confirm_password': password
    }

    await client.post('/users/register/', json=payload_1)

    payload_2 = {
        'email': unique_email,
        'full_name': 'Test user 2',
        'password': password,
        'confirm_password': password
    }

    response = await client.post('/users/register/', json=payload_2)

    assert response.status_code == 400
    assert response.json()['detail'] == 'Пользователь с таким email уже зарегистрирован'


@pytest.mark.asyncio
@pytest.mark.login
async def test_login_wrong_password(client, unique_email):
    password = 'TestPass1'

    registered_payload = {
        'email': unique_email,
        'full_name': 'Test user',
        'password': password,
        'confirm_password': password
    }

    payload = {
        'email': unique_email,
        'password': password + '1',
    }

    await client.post('/users/register/', json=registered_payload)
    response = await client.post('/users/login/', json=payload)

    assert response.status_code == 401
    assert response.json()['detail'] == 'Неверный email или пароль'