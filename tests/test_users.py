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
@pytest.mark.login
async def test_login_non_existent_email(client):
    payload = {
        'username': 'test_test_test@example.com',
        'password': 'Password123',
    }

    response = await client.post('/auth/login/', data=payload)

    assert response.status_code == 401
    assert response.json()['detail'] == 'Неверный email или пароль'


@pytest.mark.asyncio
async def test_get_user_profile_unauthorized(client):
    # Запрос без заголовка
    response = await client.get('/users/me/')

    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


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


@pytest.mark.asyncio
async def test_logout_success_and_token_invalidation(client, create_registered_test_user_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    logout_response = await client.post('/auth/logout/', headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json()['detail'] == 'Вы успешно вышли из системы'

    # Попытка получить профиль с тем же токеном
    profile_response = await client.get('/users/me/', headers=headers)
    assert profile_response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(client, create_registered_test_user_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    payload = {
        'old_password': 'Password123',
        'new_password': 'NewStrongPassword1!',
        'confirm_new_password': 'NewStrongPassword1!'
    }

    response = await client.post('/users/change-password/', json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()['message'] == 'Пароль обновлен успешно'


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client, create_registered_test_user_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    payload = {
        'old_password': 'WrongPassword!',
        'new_password': 'NewStrongPassword1!',
        'confirm_new_password': 'NewStrongPassword1!'
    }

    response = await client.post('/users/change-password/', json=payload, headers=headers)
    assert response.status_code == 401
    assert response.json()['detail'] == 'Неверный пароль'


@pytest.mark.asyncio
async def test_update_profile_duplicate_email(client, create_registered_test_user_member, register_user):
    second_email = 'second_user@example.com'
    await register_user(email=second_email, full_name='Second User')

    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    # Попытка поменять имейл первого юзера на имейл второго
    payload = {
        'email': second_email
    }

    response = await client.patch('/users/update-profile', json=payload, headers=headers)

    assert response.status_code in (400, 409)