import pytest


@pytest.mark.asyncio
async def test_register_team_by_member(client, create_registered_test_user_member):
    """
    Тест на регистрацию команды ролью обвчного юзера (member`a)
    """
    payload = {
        'name': 'Test team 1',
        'invite_code': 'test_code_1'
    }

    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)

    assert response.status_code == 403
    assert response.json()['detail'] == 'У вас недостаточно прав'


@pytest.mark.asyncio
async def test_register_team_by_manager(client, create_registered_test_user_manager):
    """
    Тест на регистрацию команды ролью менеджера
    """
    payload = {
        'name': 'Test team 1',
    }

    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()['name'] == 'Test team 1'


@pytest.mark.asyncio
async def test_join_by_invite_code(client, create_registered_test_user_manager, create_registered_test_user_member):
    """
    Тест на присоединение к команде по инвайт коду
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team = await client.post('/teams/create_team/', json={'name': 'Test team 1'}, headers=manager_headers)
    assert team.status_code == 200

    invite_code = team.json()['invite_code']

    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.post(f'/teams/{invite_code}/join/', headers=member_headers)
    assert response.status_code == 200
    assert response.json() is not None


@pytest.mark.asyncio
async def test_get_team_members_success(client, create_registered_test_user_manager):
    """
    Тест на получение списка участников команды менеджером (владельцем)
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Test Team Members'}, headers=manager_headers)
    team_id = team_res.json()['id']

    res = await client.get(f'/teams/{team_id}/members/', headers=manager_headers)

    assert res.status_code == 200
    data = res.json()
    assert 'members' in data
    assert isinstance(data['members'], list)


@pytest.mark.asyncio
async def test_get_team_members_forbidden_for_outsider(client, create_registered_test_user_manager,
                                                       create_registered_test_user_member):
    """
    Тест может ли НЕ участник команды просматривать состав команды
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Secret Team'}, headers=manager_headers)
    team_id = team_res.json()['id']

    # Юзер который не в команде пытается посмотреть участников
    res = await client.get(f'/teams/{team_id}/members/', headers=member_headers)

    # Т.к. create_team() возвращает None, ожидается 404
    assert res.status_code == 404
    assert res.json()['detail'] == f'Команды с id:{team_id} не существует'


@pytest.mark.asyncio
async def test_delete_team_member_by_manager_success(client, create_registered_test_user_manager,
                                                     create_registered_test_user_member):
    """
    Тест на успешное удаление участника менеджером
    """
    manager_headers = {'Authorization': f'Bearer {create_registered_test_user_manager}'}
    member_headers = {'Authorization': f'Bearer {create_registered_test_user_member}'}

    team_res = await client.post('/teams/create_team/', json={'name': 'Kick Team'}, headers=manager_headers)
    team_data = team_res.json()
    team_id = team_data['id']
    invite_code = team_data['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    me_res = await client.get('/users/me/', headers=member_headers)
    member_id = me_res.json()['id']

    del_res = await client.delete(f'/teams/{team_id}/members/{member_id}/', headers=manager_headers)

    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_delete_team_member_by_member_fails(client, create_registered_test_user_manager,
                                                  create_registered_test_user_member):
    """
    Тест может ли обычный участник удалить члена команды
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Rebel Team'}, headers=manager_headers)
    team_data = team_res.json()
    team_id = team_data['id']
    invite_code = team_data['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    me_res = await client.get('/users/me/', headers=member_headers)
    member_id = me_res.json()['id']

    del_res = await client.delete(f'/teams/{team_id}/members/{member_id}/', headers=member_headers)

    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_change_member_role_by_manager_success(
        client,
        create_registered_test_user_manager,
        create_registered_test_user_member
):
    """
    Тест на успешное изменение роли участника менеджером команды
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Role Team'}, headers=manager_headers)
    team_data = team_res.json()
    team_id = team_data['id']
    invite_code = team_data['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    me_res = await client.get('/users/me/', headers=member_headers)
    member_id = me_res.json()['id']

    response = await client.patch(
        f'/teams/{team_id}/members/{member_id}/role/',
        json={'role': 'manager'},
        headers=manager_headers
    )

    assert response.status_code == 200
    assert response.json()['role'] == 'manager'


@pytest.mark.asyncio
async def test_change_member_role_by_member_fails(
        client,
        create_registered_test_user_manager,
        create_registered_test_user_member
):
    """
    Тест может ли обычный участник роли
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Role Team'}, headers=manager_headers)
    team_data = team_res.json()
    team_id = team_data['id']
    invite_code = team_data['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    me_res = await client.get('/users/me/', headers=member_headers)
    member_id = me_res.json()['id']

    response = await client.patch(
        f'/teams/{team_id}/members/{member_id}/role/',
        json={'role': 'manager'},
        headers=member_headers
    )

    # 404, т.к. обычный участник не имеет прав
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_change_member_role_invalid_value(
        client,
        create_registered_test_user_manager,
        create_registered_test_user_member
):
    """
    Тест на валидация пайдантик (UpdateRoleRequest с Literal[])
    """
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Role Team'}, headers=manager_headers)
    team_data = team_res.json()
    team_id = team_data['id']
    invite_code = team_data['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    me_res = await client.get('/users/me/', headers=member_headers)
    member_id = me_res.json()['id']

    # Попытка установить недопустимую роль (admin вместо manager/member)
    response = await client.patch(
        f'/teams/{team_id}/members/{member_id}/role/',
        json={'role': 'admin'},
        headers=manager_headers
    )

    # Ошибка валидации пайдантик (422)
    assert response.status_code == 422