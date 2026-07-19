import pytest


@pytest.mark.asyncio
@pytest.mark.register
async def test_register_user(client, unique_email):
    payload = {
        'email': unique_email,
        'full_name': 'Test user',
        'password': 'TestPass1',
        'confirm_password': 'TestPass1'
    }

    response = await client.post('/auth/register/', json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data['email'] == unique_email
    assert data['full_name'] == 'Test user'
    assert data['role'] == 'member'
    assert 'password' not in data


@pytest.mark.asyncio
@pytest.mark.login
async def test_register_and_login_user_pipeline(client, unique_email, register_user):
    await register_user(email=unique_email, full_name='Test user')

    payload = {
        'username': unique_email,
        'password': 'Password123',
    }

    response = await client.post('/auth/login/', data=payload)

    assert response.status_code == 200

    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


@pytest.mark.asyncio
@pytest.mark.register
async def test_register_duplicate_email(client, unique_email, register_user):
    await register_user(email=unique_email, full_name='Test user 1')

    payload_2 = {
        'email': unique_email,
        'full_name': 'Test user 2',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }

    response = await client.post('/auth/register/', json=payload_2)

    assert response.status_code == 400
    assert response.json()['detail'] == 'Пользователь с таким email уже зарегистрирован'


@pytest.mark.asyncio
@pytest.mark.login
async def test_login_wrong_password(client, unique_email, register_user):
    await register_user(email=unique_email, full_name='Test user')

    payload = {
        'username': unique_email,
        'password': 'Password123' + '1',
    }

    response = await client.post('/auth/login/', data=payload)

    assert response.status_code == 401
    assert response.json()['detail'] == 'Неверный email или пароль'


@pytest.mark.asyncio
async def test_get_user_profile(client, create_registered_test_user_member, unique_email):
    users_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.get('/users/me/', headers=users_headers)
    assert response.status_code == 200
    assert 'email' in response.json()


@pytest.mark.asyncio
async def test_update_profile_success(client, create_registered_test_user_member):
    users_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    payload = {
        'full_name': 'Обновленное Имя',
        'email': 'updated_email@example.com'
    }

    response = await client.patch('/users/update-profile', json=payload, headers=users_headers)

    assert response.status_code == 200
    assert response.json()['full_name'] == 'Обновленное Имя'
    assert response.json()['email'] == 'updated_email@example.com'


@pytest.mark.asyncio
async def test_update_profile_invalid_email(client, create_registered_test_user_member):
    users_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    payload = {
        'email': 'bad-email'
    }

    response = await client.patch('/users/update-profile', json=payload, headers=users_headers)

    assert response.status_code == 422
    assert 'detail' in response.json()