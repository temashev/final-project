import pytest


@pytest.mark.asyncio
async def test_register_team_by_member(client, create_registered_test_user_member):
    token = create_registered_test_user_member

    payload = {
        'name': 'Test team 1',
        'invite_code': 'test_code_1'
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)
    assert response.status_code == 403

    data = response.json()
    assert data['detail'] == 'У вас недостаточно прав'


@pytest.mark.asyncio
async def test_register_team_by_manager(client, create_registered_test_user_manager):
    token = create_registered_test_user_manager

    payload = {
        'name': 'Test team 1',
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data['name'] == 'Test team 1'


@pytest.mark.asyncio
async def test_join_by_invite_code(client, create_registered_test_user_manager, create_registered_test_user_member):
    manager_token = create_registered_test_user_manager
    manager_headers = {
        'Authorization': f'Bearer {manager_token}'
    }
    payload = {
        'name': 'Test team 1',
    }

    team = await client.post('/teams/create_team/', json=payload, headers=manager_headers)
    assert team.status_code == 200

    invite_code = team.json()['invite_code']

    member_token = create_registered_test_user_member
    member_headers = {
        'Authorization': f'Bearer {member_token}'
    }
    join_payload = {
        'invite_code': invite_code
    }

    response = await client.post(f'/teams/join/{invite_code}/', json=join_payload, headers=member_headers)
    assert response.status_code == 200
